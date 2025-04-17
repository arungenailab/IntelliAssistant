"""
Intent analysis node for the LangGraph SQL generation system.

This module contains the function that analyzes user query intent
to identify the tables and operations needed.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple

from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from ..utils.llm_utils import get_llm_for_generation, format_conversation_history
from ..prompts.intent_analysis_prompts import INTENT_ANALYSIS_SYSTEM_PROMPT, INTENT_ANALYSIS_USER_PROMPT

# Set up logging
logger = logging.getLogger(__name__)


async def analyze_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the user query to identify tables, operations, and intent.
    
    This node analyzes the user's natural language query against the database
    schema to identify:
    - Relevant tables and relationships
    - Type of operation (SELECT, INSERT, UPDATE, DELETE, etc.)
    - Aggregation and grouping requirements
    - Filtering conditions
    - Time ranges or date-based criteria
    
    Args:
        state: The current state including user_query and schema_info
        
    Returns:
        Updated state with intent_analysis_result populated
    """
    logger.info("Starting intent analysis")
    
    # Extract required information from state
    user_query = state["user_query"]
    schema_info = state.get("schema_info", {})
    conversation_history = state.get("conversation_history", [])
    
    # Basic validation
    if not user_query:
        logger.error("No user query found in state")
        return {
            **state,
            "error": "No user query provided for intent analysis",
            "workflow_stage": "error"
        }
    
    if not schema_info:
        logger.warning("No schema information found in state")
    
    try:
        # Get LLM
        llm = get_llm_for_generation()
        
        # Format schema info for prompt
        formatted_schema = format_schema_for_prompt(schema_info)
        
        # Format conversation history
        formatted_history = format_conversation_history(conversation_history)
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=INTENT_ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(content=formatted_history + "\n\n" + INTENT_ANALYSIS_USER_PROMPT.format(
                user_query=user_query,
                schema_info=formatted_schema
            ))
        ])
        
        # Get the intent analysis
        logger.info(f"Sending intent analysis request for query: {user_query[:50]}...")
        intent_result = await llm.ainvoke(prompt)
        
        # Parse the result
        intent_analysis = parse_intent_analysis(intent_result.content)
        
        # Update the state
        logger.info(f"Intent analysis complete. Identified tables: {intent_analysis.get('tables', [])}")
        return {
            **state,
            "intent_analysis_result": intent_analysis,
            "tables_used": intent_analysis.get("tables", []),
            "workflow_stage": "intent_analysis_complete"
        }
    
    except Exception as e:
        logger.error(f"Error in intent analysis: {str(e)}")
        return {
            **state,
            "error": f"Intent analysis failed: {str(e)}",
            "workflow_stage": "error"
        }


def format_schema_for_prompt(schema_info: Dict[str, Any]) -> str:
    """
    Format schema information for prompts.
    
    Args:
        schema_info: Dictionary containing database schema information
        
    Returns:
        Formatted schema string for prompts
    """
    if not schema_info:
        return "No schema information available."
    
    formatted = "DATABASE SCHEMA:\n"
    
    # Process tables
    tables = schema_info.get("tables", {})
    for table_name, table_info in tables.items():
        formatted += f"\nTABLE: {table_name}\n"
        
        # Process columns
        columns = table_info.get("columns", {})
        if columns:
            formatted += "Columns:\n"
            for col_name, col_info in columns.items():
                col_type = col_info.get("type", "UNKNOWN")
                is_pk = "PRIMARY KEY" if col_info.get("is_primary_key") else ""
                is_fk = f"FOREIGN KEY to {col_info.get('foreign_key')}" if col_info.get("foreign_key") else ""
                constraints = " ".join(filter(None, [is_pk, is_fk]))
                
                formatted += f"  - {col_name} ({col_type}){' ' + constraints if constraints else ''}\n"
        
        # Process relationships
        relationships = table_info.get("relationships", [])
        if relationships:
            formatted += "Relationships:\n"
            for rel in relationships:
                formatted += f"  - {rel['type']} relationship with {rel['table']} on {rel['on']}\n"
    
    return formatted


def parse_intent_analysis(analysis_text: str) -> Dict[str, Any]:
    """
    Parse the intent analysis text from the LLM into a structured format.
    
    Args:
        analysis_text: The text response from the LLM
        
    Returns:
        Structured intent analysis
    """
    intent_analysis = {
        "tables": [],
        "operation": "SELECT",  # Default to SELECT
        "conditions": [],
        "grouping": [],
        "aggregations": [],
        "order": [],
        "limit": None,
        "time_range": None,
        "joins": []
    }
    
    try:
        # Extract JSON if present
        json_match = re.search(r'```json\s*(.*?)\s*```', analysis_text, re.DOTALL)
        if json_match:
            import json
            try:
                # Try to parse JSON
                parsed = json.loads(json_match.group(1))
                # Update intent with parsed data, keeping defaults for missing fields
                for key in intent_analysis:
                    if key in parsed:
                        intent_analysis[key] = parsed[key]
                return intent_analysis
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from intent analysis")
                # Continue with regex parsing as fallback
    
        # Fallback: Extract information using regex patterns
        # Extract tables
        tables_match = re.search(r'(Tables|TABLES):\s*(.*?)(?:\n\n|\n[A-Z]+:)', analysis_text + "\n\nEND:", re.DOTALL)
        if tables_match:
            tables_text = tables_match.group(2)
            tables = re.findall(r'["\']?([\w_]+)["\']?', tables_text)
            intent_analysis["tables"] = list(set(tables))  # Remove duplicates
        
        # Extract operation type
        operation_match = re.search(r'(Operation|OPERATION):\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)', analysis_text, re.IGNORECASE)
        if operation_match:
            intent_analysis["operation"] = operation_match.group(2).upper()
        
        # Extract conditions
        conditions_match = re.search(r'(Conditions|CONDITIONS):\s*(.*?)(?:\n\n|\n[A-Z]+:)', analysis_text + "\n\nEND:", re.DOTALL)
        if conditions_match:
            conditions_text = conditions_match.group(2)
            conditions = [cond.strip() for cond in conditions_text.split('\n') if cond.strip()]
            intent_analysis["conditions"] = conditions
            
    except Exception as e:
        logger.warning(f"Error parsing intent analysis: {str(e)}")
    
    return intent_analysis 
"""
SQL generation node for the LangGraph SQL generation system.

This module implements SQL generation based on schema information and intent analysis.
"""

import logging
import json
from typing import Dict, List, Any, Optional

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import get_sql_model
from ..prompts.sql_generation import SQL_GENERATION_PROMPT

logger = logging.getLogger(__name__)


async def generate_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate SQL based on schema information and user query.
    
    Args:
        state: The current graph state
        
    Returns:
        Updated state with generated SQL
    """
    logger.info("Generating SQL query")
    
    # Extract required information from state
    user_query = state.get("user_query", "")
    schema_info = state.get("schema_info", {})
    intent_analysis = state.get("intent_analysis", {})
    
    # Handle missing required information
    if not user_query:
        state["error"] = "Missing user query"
        return state
    
    if not schema_info:
        state["error"] = "Missing schema information"
        return state
    
    try:
        # Create schema summary for the prompt
        schema_summary = ""
        for table_name, table_info in schema_info.items():
            schema_summary += f"Table: {table_name}\n"
            schema_summary += "Columns:\n"
            
            for column in table_info.get("columns", []):
                column_name = column.get("name", "")
                column_type = column.get("type", "")
                column_desc = column.get("description", "")
                
                schema_summary += f"- {column_name} ({column_type}): {column_desc}\n"
            
            schema_summary += "\n"
        
        # Format intent analysis for prompt
        intent_analysis_str = json.dumps(intent_analysis, indent=2) if intent_analysis else ""
        
        # Initialize language model
        model = get_sql_model()
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert SQL query generator."),
            HumanMessage(content=SQL_GENERATION_PROMPT.format(
                schema_info=schema_summary,
                user_query=user_query,
                intent_analysis=intent_analysis_str
            ))
        ])
        
        # Generate SQL
        response = await model.ainvoke(prompt)
        sql_query = response.content
        
        # Extract SQL from response (in case model outputs additional text)
        import re
        sql_match = re.search(r'```sql\s*(.*?)\s*```', sql_query, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
        
        # Update state with generated SQL
        state["sql_query"] = sql_query
        state["error"] = None  # Clear any previous errors
        
        logger.info(f"Generated SQL query: {sql_query}")
        
    except Exception as e:
        error_msg = f"Failed to generate SQL query: {str(e)}"
        logger.error(error_msg)
        state["error"] = error_msg
    
    return state 
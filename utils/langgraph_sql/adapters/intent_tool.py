"""
Intent analysis tool adapter for the LangGraph SQL generation system.

This module provides an adapter to analyze query intent using the
existing SQLGeneratorAgent or LLM.
"""

import logging
import json
from typing import Dict, List, Any, Optional

from ..config import get_sql_model

logger = logging.getLogger(__name__)


class IntentAnalysisTool:
    """
    Tool for analyzing user query intent.
    
    This adapter can either use the existing SQLGeneratorAgent or
    directly use an LLM to analyze query intent.
    """
    
    def __init__(self, use_agent: bool = False):
        """
        Initialize the intent analysis tool.
        
        Args:
            use_agent: Whether to use the existing SQLGeneratorAgent
        """
        self.use_agent = use_agent
    
    async def analyze_intent(
        self,
        user_query: str,
        schema_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the intent of a user query.
        
        Args:
            user_query: The natural language query
            schema_info: The database schema information
            
        Returns:
            Dictionary containing intent analysis
        """
        try:
            if self.use_agent:
                return await self._analyze_with_agent(user_query, schema_info)
            else:
                return await self._analyze_with_llm(user_query, schema_info)
        except Exception as e:
            error_msg = f"Intent analysis error: {str(e)}"
            logger.error(error_msg)
            return {
                "primary_intent": "SELECT",
                "required_tables": [],
                "error": error_msg
            }
    
    async def _analyze_with_agent(
        self,
        user_query: str,
        schema_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze intent using the existing SQLGeneratorAgent.
        
        Args:
            user_query: The natural language query
            schema_info: The database schema information
            
        Returns:
            Dictionary containing intent analysis
        """
        try:
            # Import here to avoid circular imports
            from utils.agents.sql_generator import SQLGeneratorAgent
            
            # Create the agent
            agent = SQLGeneratorAgent()
            
            # Analyze intent
            intent_info = agent.analyze_query_intent(user_query, schema_info)
            
            # Format the result
            return {
                "primary_intent": intent_info.get("query_type", "SELECT"),
                "required_tables": intent_info.get("entities", []),
                "key_columns": intent_info.get("columns", []),
                "filter_conditions": intent_info.get("filters", []),
                "joins_needed": intent_info.get("joins", []),
                "aggregations": intent_info.get("aggregations", []),
                "sort_requirements": intent_info.get("ordering", [])
            }
        except Exception as e:
            logger.error(f"Error using agent for intent analysis: {str(e)}")
            # Fall back to LLM
            return await self._analyze_with_llm(user_query, schema_info)
    
    async def _analyze_with_llm(
        self,
        user_query: str,
        schema_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze intent using a language model directly.
        
        Args:
            user_query: The natural language query
            schema_info: The database schema information
            
        Returns:
            Dictionary containing intent analysis
        """
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Format schema information for the prompt
        schema_text = self._format_schema_for_prompt(schema_info)
        
        # Create the prompt
        intent_prompt = """You are an expert at analyzing database query intents. Analyze this query to identify:
1. The primary intent (SELECT, INSERT, UPDATE, DELETE, etc.)
2. The main tables required
3. Key columns needed
4. Any filter conditions
5. Any joins that might be needed
6. Any grouping or aggregation needed
7. Any sorting requirements

USER QUERY: {query}

DATABASE SCHEMA:
{schema}

Respond with a JSON object containing:
- "primary_intent": The main SQL operation
- "required_tables": List of tables needed
- "key_columns": List of important columns
- "filter_conditions": Any filters identified
- "joins_needed": Any joins required
- "aggregations": Any aggregation operations
- "sort_requirements": Any sorting needs
- "query_complexity": A rating from 1-5 of how complex the query is
- "analysis_notes": Any additional notes about the intent
"""
        
        # Get the model
        model = get_sql_model()
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at analyzing database query intents."),
            HumanMessage(content=intent_prompt.format(
                query=user_query,
                schema=schema_text
            ))
        ])
        
        # Generate the intent analysis
        response = await model.ainvoke(prompt)
        intent_text = response.content
        
        # Parse the JSON response
        try:
            intent_data = json.loads(intent_text)
            return intent_data
        except json.JSONDecodeError:
            # Try to extract JSON if it's wrapped in text or code blocks
            import re
            json_match = re.search(r'{.*}', intent_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
            
            # Fallback to a basic structure
            return {
                "primary_intent": "SELECT",
                "required_tables": [],
                "key_columns": [],
                "filter_conditions": [],
                "joins_needed": [],
                "error": "Failed to parse intent analysis output"
            }
    
    def _format_schema_for_prompt(self, schema_info: Dict[str, Any]) -> str:
        """
        Format schema information for the prompt.
        
        Args:
            schema_info: The database schema information
            
        Returns:
            Formatted schema string
        """
        schema_text = []
        
        # Add table information
        for table_name, table_info in schema_info.items():
            if table_name == "relationships":
                continue
                
            schema_text.append(f"TABLE: {table_name}")
            
            # Add column information
            columns = table_info.get("columns", [])
            for column in columns:
                if isinstance(column, dict):
                    column_name = column.get("name", "unknown")
                    column_type = column.get("type", "unknown")
                    primary_key = column.get("primary_key", False)
                    schema_text.append(f"  - {column_name} ({column_type}){' (Primary Key)' if primary_key else ''}")
                elif isinstance(column, str):
                    schema_text.append(f"  - {column}")
            
            schema_text.append("")
        
        # Add relationship information
        relationships = schema_info.get("relationships", [])
        if relationships:
            schema_text.append("RELATIONSHIPS:")
            for rel in relationships:
                if isinstance(rel, dict):
                    from_table = rel.get("from_table", "unknown")
                    from_column = rel.get("from_column", "unknown")
                    to_table = rel.get("to_table", "unknown")
                    to_column = rel.get("to_column", "unknown")
                    
                    schema_text.append(f"  - {from_table}.{from_column} -> {to_table}.{to_column}")
            
            schema_text.append("")
        
        return "\n".join(schema_text) 
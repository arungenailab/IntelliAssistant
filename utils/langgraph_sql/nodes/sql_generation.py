"""
SQL generation node for the LangGraph SQL generation system.

This module generates SQL queries from natural language queries, 
taking into account schema information, intent analysis, and feedback.
"""

import logging
import json
from typing import Dict, List, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import get_generation_model
from ..state import SQLGenerationState
from ..prompts.sql_generation_prompts import SQL_GENERATION_PROMPT
from ..query_processor import process_query  # Import the query processor

logger = logging.getLogger(__name__)


async def generate_sql(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a SQL query based on the user's natural language query.
    
    This node:
    1. Takes the user query, schema info, and intent analysis
    2. Uses an LLM to generate an appropriate SQL query
    3. Updates the state with the generated SQL query
    
    Args:
        state: The current graph state
        
    Returns:
        Updated state with generated SQL query
    """
    logger.info("Generating SQL query")
    
    # Extract required information from state
    user_query = state.get("user_query", "")
    schema_info = state.get("schema_info", "No schema information available")
    intent_analysis = state.get("intent_analysis_result", "No intent analysis available")
    additional_context = state.get("additional_context", "")
    
    try:
        # Initialize language model
        model = get_generation_model()
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a SQL expert who writes precise and optimized SQL queries."),
            HumanMessage(content=SQL_GENERATION_PROMPT.format(
                user_query=user_query,
                schema_info=schema_info,
                intent_analysis=intent_analysis,
                additional_context=additional_context
            ))
        ])
        
        # Generate the SQL query
        response = await model.ainvoke(prompt)
        sql_query = response.content.strip()
        
        # Post-process the query to fix common issues
        processed_sql, was_modified = process_query(user_query, sql_query)
        
        if was_modified:
            logger.info(f"Query was modified during post-processing")
            logger.info(f"Original: {sql_query}")
            logger.info(f"Modified: {processed_sql}")
        
        logger.info(f"Generated SQL query: {processed_sql[:100]}...")
        
        # Update the state
        return {
            **state,
            "sql_query": processed_sql,
            "original_sql_query": sql_query if was_modified else None,
            "query_modified": was_modified,
            "workflow_stage": "sql_generation_complete"
        }
        
    except Exception as e:
        error_msg = f"Failed to generate SQL query: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "error": error_msg,
            "workflow_stage": "sql_generation_error"
        }


def format_schema_for_sql_generation(
    schema_info: Dict[str, Any],
    tables_used: List[str]
) -> str:
    """
    Format schema information for the SQL generation prompt.
    
    Args:
        schema_info: Database schema information
        tables_used: List of tables used in the query
        
    Returns:
        Formatted schema string
    """
    schema_text = []
    
    # Add table information with detailed column types
    for table_name in tables_used:
        schema_text.append(f"Table: {table_name}")
        
        # Get column information
        columns = []
        if "tables" in schema_info and table_name in schema_info["tables"]:
            # Full DDL format
            table_info = schema_info["tables"][table_name]
            if "columns" in table_info:
                columns = table_info["columns"]
        elif table_name in schema_info:
            # Table-as-key format
            columns = schema_info[table_name]
        
        # Format columns with more detail
        for column in columns:
            if isinstance(column, dict):
                column_name = column.get("name", "unknown")
                column_type = column.get("type", "unknown")
                nullable = "NULL" if column.get("nullable", True) else "NOT NULL"
                primary_key = column.get("primary_key", False)
                foreign_key = column.get("foreign_key", False)
                referenced_table = column.get("references", {}).get("table", "") if foreign_key else ""
                referenced_column = column.get("references", {}).get("column", "") if foreign_key else ""
                
                column_desc = f"  - {column_name} ({column_type}, {nullable})"
                if primary_key:
                    column_desc += " PRIMARY KEY"
                if foreign_key and referenced_table and referenced_column:
                    column_desc += f" REFERENCES {referenced_table}({referenced_column})"
                    
                schema_text.append(column_desc)
            elif isinstance(column, str):
                schema_text.append(f"  - {column}")
        
        schema_text.append("")
    
    # Add relationship information with more detail
    relationships = []
    if "relationships" in schema_info:
        relationships = schema_info["relationships"]
    
    if relationships:
        schema_text.append("Relationships:")
        for rel in relationships:
            if isinstance(rel, dict):
                from_table = rel.get("from_table", "unknown")
                from_column = rel.get("from_column", "unknown")
                to_table = rel.get("to_table", "unknown")
                to_column = rel.get("to_column", "unknown")
                rel_type = rel.get("type", "FK")
                cardinality = rel.get("cardinality", "1:N")
                
                schema_text.append(f"  - {from_table}.{from_column} -> {to_table}.{to_column} ({rel_type}, {cardinality})")
        
        schema_text.append("")
    
    # Add example data if available
    for table_name in tables_used:
        example_data = None
        if "tables" in schema_info and table_name in schema_info["tables"]:
            # Full DDL format
            table_info = schema_info["tables"][table_name]
            example_data = table_info.get("example_data", None)
        
        if example_data:
            schema_text.append(f"Example data for {table_name}:")
            schema_text.append("```")
            if isinstance(example_data, list) and len(example_data) > 0:
                # Format as a table
                headers = example_data[0].keys() if isinstance(example_data[0], dict) else []
                if headers:
                    schema_text.append(" | ".join(headers))
                    schema_text.append("-" * (sum(len(h) for h in headers) + (len(headers) - 1) * 3))
                    
                    # Add rows (limit to 3 for brevity)
                    for row in example_data[:3]:
                        schema_text.append(" | ".join(str(row.get(h, "")) for h in headers))
            else:
                schema_text.append(str(example_data))
            schema_text.append("```")
            schema_text.append("")
    
    return "\n".join(schema_text) 
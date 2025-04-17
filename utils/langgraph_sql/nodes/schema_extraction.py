"""
Schema extraction node for the LangGraph SQL generation system.

This module extracts database schema information from the connection,
which is essential for generating correct SQL queries.
"""

import logging
import json
from typing import Dict, List, Any, Optional

from ..config import get_sql_model
from ..adapters.schema_tool import SchemaExtractionTool

logger = logging.getLogger(__name__)


async def extract_schema(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract schema information from the database connection.
    
    This node:
    1. Takes the connection parameters from the state
    2. Uses the schema extraction tool to retrieve schema information
    3. Updates the state with the schema information
    
    Args:
        state: The current graph state
        
    Returns:
        Updated state with schema information
    """
    logger.info("Extracting schema information")
    
    # Extract required information from state
    connection_params = state.get("connection_params", {})
    
    # Skip if no connection parameters
    if not connection_params:
        error_msg = "No connection parameters provided"
        logger.error(error_msg)
        return {
            **state,
            "error": error_msg,
            "workflow_stage": "schema_extraction_error"
        }
    
    try:
        # Initialize schema extraction tool
        schema_tool = SchemaExtractionTool()
        
        # Extract schema
        schema_info = await schema_tool.extract_schema(connection_params)
        
        # Check if schema extraction was successful
        if not schema_info:
            error_msg = "Failed to extract schema information"
            logger.error(error_msg)
            return {
                **state,
                "error": error_msg,
                "workflow_stage": "schema_extraction_error"
            }
        
        logger.info(f"Schema extraction complete. Found {len(schema_info)} tables")
        
        # Update the state
        return {
            **state,
            "schema_info": schema_info,
            "workflow_stage": "schema_extraction_complete"
        }
        
    except Exception as e:
        error_msg = f"Failed to extract schema information: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "error": error_msg,
            "workflow_stage": "schema_extraction_error"
        }


def extract_table_columns(
    table_name: str, 
    schema_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract column information for a specific table.
    
    Args:
        table_name: Name of the table
        schema_info: Database schema information
        
    Returns:
        List of column definitions
    """
    # Handle different schema formats
    if "tables" in schema_info and table_name in schema_info["tables"]:
        # Full DDL format
        table_info = schema_info["tables"][table_name]
        if "columns" in table_info:
            return table_info["columns"]
    elif table_name in schema_info:
        # Table-as-key format
        return schema_info[table_name]
    
    # No columns found
    return []


def get_relationships(
    schema_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract relationship information from the schema.
    
    Args:
        schema_info: Database schema information
        
    Returns:
        List of relationship definitions
    """
    if "relationships" in schema_info:
        return schema_info["relationships"]
    
    # No relationships found
    return [] 
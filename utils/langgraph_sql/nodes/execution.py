"""
Execution node for the LangGraph SQL generation system.

This module executes SQL queries against the database.
"""

import logging
import time
from typing import Dict, List, Any, Optional

from ..config import ENABLE_EXECUTION
from ..adapters.execution_tool import SQLExecutionTool

logger = logging.getLogger(__name__)


async def execute_sql(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the generated SQL query against the database.
    
    This node:
    1. Takes the generated SQL query and connection parameters
    2. Executes the query against the database
    3. Updates the state with the execution results
    
    Args:
        state: The current graph state
        
    Returns:
        Updated state with execution results
    """
    logger.info("Executing SQL query")
    
    # Extract required information from state
    sql_query = state.get("sql_query", "")
    connection_params = state.get("connection_params", {})
    execute = state.get("execute", ENABLE_EXECUTION)
    
    # Skip execution if not requested or no SQL query
    if not execute:
        logger.info("SQL execution disabled, skipping")
        return {
            **state,
            "execution_result": {
                "executed": False,
                "message": "Execution skipped - execution disabled by configuration"
            },
            "workflow_stage": "execution_skipped"
        }
    
    if not sql_query:
        logger.warning("No SQL query to execute")
        return {
            **state,
            "execution_result": {
                "executed": False,
                "message": "Execution skipped - no SQL query provided"
            },
            "workflow_stage": "execution_skipped"
        }
    
    try:
        # Initialize execution tool
        execution_tool = SQLExecutionTool()
        
        # Record start time
        start_time = time.time()
        
        # Execute the query
        results = await execution_tool.execute_query(connection_params, sql_query)
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Check if execution was successful
        if results.get("error"):
            logger.error(f"SQL execution error: {results['error']}")
            return {
                **state,
                "execution_result": {
                    "executed": True,
                    "error": results["error"],
                    "query_time_ms": execution_time_ms
                },
                "workflow_stage": "execution_error"
            }
        
        # Get the results
        row_count = len(results.get("rows", []))
        
        logger.info(f"SQL execution complete. Returned {row_count} rows in {execution_time_ms}ms")
        
        # Update the state
        return {
            **state,
            "execution_result": {
                "executed": True,
                "results": results.get("rows", []),
                "row_count": row_count,
                "query_time_ms": execution_time_ms
            },
            "workflow_stage": "execution_complete"
        }
        
    except Exception as e:
        error_msg = f"Failed to execute SQL query: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "execution_result": {
                "executed": True,
                "error": error_msg
            },
            "workflow_stage": "execution_error"
        }


async def handle_error(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle errors in the SQL generation process.
    
    This node:
    1. Takes the error information
    2. Formats a user-friendly error message
    3. Updates the state to indicate an error
    
    Args:
        state: The current graph state
        
    Returns:
        Updated state with error information
    """
    logger.info("Handling error")
    
    # Extract error information
    error = state.get("error", "Unknown error")
    
    # Format a user-friendly error message
    user_message = f"I encountered an error while processing your query: {error}"
    
    # Update the state
    return {
        **state,
        "user_message": user_message,
        "success": False,
        "workflow_stage": "error_handled"
    } 
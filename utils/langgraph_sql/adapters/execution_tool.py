"""
SQL execution tool adapter for the LangGraph SQL generation system.

This module provides an adapter to execute SQL queries against a database
using the existing SQL connector.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SQLExecutionTool:
    """
    Tool for executing SQL queries against a database.
    
    This adapter uses the existing SQLServerConnector to execute SQL
    queries and return the results in a format suitable for the LangGraph system.
    """
    
    def __init__(self):
        """Initialize the SQL execution tool."""
        pass
    
    async def execute_query(
        self,
        connection_params: Dict[str, Any],
        sql_query: str,
        result_limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute a SQL query against a database.
        
        Args:
            connection_params: Database connection parameters
            sql_query: The SQL query to execute
            result_limit: Maximum number of rows to return
            
        Returns:
            Dictionary containing execution results or error message
        """
        try:
            # Import here to avoid circular imports
            from utils.sql_connector import SQLServerConnector
            
            # Create connector
            connector = SQLServerConnector(connection_params)
            
            # Connect to database
            if not connector.connect():
                error_msg = f"Failed to connect to database: {connector.last_error}"
                logger.error(error_msg)
                return {"error": error_msg}
            
            try:
                # Execute the query
                result = connector.execute_query(sql_query, limit=result_limit)
                
                # Check for errors
                if result.get("error"):
                    return {"error": result["error"]}
                
                # Process the results
                rows = result.get("rows", [])
                columns = result.get("columns", [])
                
                # Format the results
                formatted_rows = []
                for row in rows:
                    result_row = {}
                    for i, column in enumerate(columns):
                        result_row[column] = row[i] if i < len(row) else None
                    formatted_rows.append(result_row)
                
                return {
                    "rows": formatted_rows,
                    "columns": columns,
                    "row_count": len(formatted_rows)
                }
                
            finally:
                # Always disconnect
                connector.disconnect()
                
        except Exception as e:
            error_msg = f"SQL execution error: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg} 
"""
SQL execution adapter tool for the LangGraph SQL generation system.

This tool adapts the existing SQL execution functionality for use in the
LangGraph workflow system.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union

# Import existing execution functionality
from utils.database.executor import SQLExecutor

logger = logging.getLogger(__name__)


class SQLExecutionTool:
    """
    Tool for executing SQL queries.
    
    Adapts the existing SQL execution functionality to work within the LangGraph workflow.
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the SQL execution tool.
        
        Args:
            connection_params: Database connection parameters
        """
        self.connection_params = connection_params
        self.executor = SQLExecutor(connection_params)
        self._timestamp = None
        
    async def execute_sql(
        self, 
        sql_query: str,
        safe_mode: bool = True,
        row_limit: int = 100
    ) -> Dict[str, Any]:
        """
        Execute a SQL query and return the results.
        
        Args:
            sql_query: The SQL query to execute
            safe_mode: Whether to execute in safe mode (prevents destructive operations)
            row_limit: Maximum number of rows to return
            
        Returns:
            Execution results and metadata
        """
        self._timestamp = time.time()
        
        try:
            # Call the existing executor
            result = await self.executor.execute_query(
                query=sql_query,
                safe_mode=safe_mode,
                row_limit=row_limit
            )
            
            # Process the result
            row_count = 0
            if isinstance(result, list):
                row_count = len(result)
            elif isinstance(result, dict) and "rows" in result:
                row_count = len(result["rows"])
                
            # Process and return in the expected format
            return {
                "success": True,
                "result": result,
                "row_count": row_count,
                "meta": {
                    "execution_time": time.time() - self._timestamp,
                    "safe_mode": safe_mode,
                    "row_limit": row_limit,
                    "timestamp": self._timestamp
                }
            }
            
        except Exception as e:
            logger.error("Error executing SQL: %s", str(e), exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "result": None,
                "meta": {
                    "execution_time": time.time() - self._timestamp,
                    "safe_mode": safe_mode,
                    "timestamp": self._timestamp
                }
            }
            
    def get_timestamp(self) -> float:
        """
        Get the timestamp of the last execution.
        
        Returns:
            Timestamp of last execution or current time if not executed
        """
        return self._timestamp or time.time() 
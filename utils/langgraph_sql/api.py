"""
API interface for the LangGraph SQL generation system.

This module provides a simple API interface for the LangGraph SQL generation system,
making it easy to integrate with the rest of the application.
"""

import logging
from typing import Dict, Any, List, Optional

from .graph import SQLGenerationGraph
from .utils.logging_utils import setup_logging

logger = logging.getLogger(__name__)


class TextToSQLConverter:
    """
    Text-to-SQL converter using LangGraph.
    
    This class provides an API-compatible interface for the LangGraph SQL generation
    system, making it easy to drop in as a replacement for the existing system.
    """
    
    def __init__(
        self,
        use_reflection: bool = True,
        execute_queries: bool = True
    ):
        """
        Initialize the text-to-SQL converter.
        
        Args:
            use_reflection: Whether to use the reflection capability
            execute_queries: Whether to execute generated queries
        """
        # Set up logging
        setup_logging(log_level="INFO")
        
        # Create the graph runner
        self.graph_runner = SQLGenerationGraph(
            enable_reflection=use_reflection,
            enable_execution=execute_queries
        )
        
        logger.info(
            "Initialized LangGraph SQL converter (reflection: %s, execution: %s)",
            use_reflection, execute_queries
        )
        
    async def convert_natural_language_to_sql(
        self,
        query: str,
        connection_params: Dict[str, Any],
        database_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Convert natural language to SQL.
        
        This method provides an API-compatible interface that matches the
        existing text-to-SQL conversion system.
        
        Args:
            query: Natural language query from the user
            connection_params: Database connection parameters
            database_context: Additional context about the database
            conversation_history: Previous conversation history
            
        Returns:
            Dictionary containing the SQL query, explanation, and results
        """
        try:
            # Run the graph
            result = await self.graph_runner.generate_sql(
                user_query=query,
                connection_params=connection_params,
                schema_info=database_context,
                conversation_history=conversation_history
            )
            
            # Format the result to match the expected API
            api_result = {
                "sql": result.get("sql_query", ""),
                "explanation": result.get("explanation", ""),
                "success": result.get("success", False),
                "results": result.get("execution_result"),
                "error": result.get("error_message")
            }
            
            # Add additional information that might be useful
            api_result["metadata"] = {
                "workflow_stage": result.get("workflow_stage", "unknown"),
                "iteration_count": result.get("iteration_count", 0),
                "reflection_enabled": len(result.get("reflection_feedback", [])) > 0,
                "tables_used": result.get("tables_used", [])
            }
            
            return api_result
            
        except Exception as e:
            logger.error("Error converting to SQL: %s", str(e), exc_info=True)
            return {
                "success": False,
                "error": f"Error in LangGraph SQL conversion: {str(e)}",
                "sql": "",
                "explanation": "An error occurred during processing.",
                "results": None
            } 
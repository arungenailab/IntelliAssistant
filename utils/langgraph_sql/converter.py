"""
Main converter class for the LangGraph SQL system.

This module implements the TextToSQLConverter class which orchestrates the LangGraph
workflow to convert natural language to SQL.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional

from .graph import SQLGenerationGraph
from .state import create_initial_state
from .config import is_reflection_enabled, is_execution_enabled, apply_feature_flags

logger = logging.getLogger(__name__)


class TextToSQLConverter:
    """
    Main converter class for the LangGraph SQL system.
    
    This class provides a high-level interface to the LangGraph SQL system,
    managing the graph initialization and execution.
    """
    
    def __init__(
        self,
        use_reflection: bool = True,
        execute_queries: bool = False
    ):
        """
        Initialize the TextToSQLConverter.
        
        Args:
            use_reflection: Whether to use the reflection step
            execute_queries: Whether to execute the generated SQL
        """
        logger.info(f"Initializing TextToSQLConverter (reflection={use_reflection}, execution={execute_queries})")
        
        # Store configuration
        self.use_reflection = use_reflection
        self.execute_queries = execute_queries
        
        # Initialize the graph
        self.graph = SQLGenerationGraph()
    
    async def convert_text_to_sql(
        self,
        query: str,
        connection_params: Dict[str, Any],
        execute: bool = False,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Convert natural language to SQL using the LangGraph system.
        
        This method is the main entry point for the converter, matching the
        API expected by the langgraph_convert_text_to_sql function.
        
        Args:
            query: The user's natural language query
            connection_params: Database connection parameters
            execute: Whether to execute the generated SQL query
            conversation_history: Optional conversation history for context
            additional_context: Optional additional context for SQL generation
            
        Returns:
            Dictionary with SQL generation results
        """
        logger.info(f"Converting query with LangGraph: {query}")
        
        try:
            # Create initial state
            initial_state = create_initial_state(
                user_query=query,
                connection_params=connection_params,
                execute=execute,
                conversation_history=conversation_history,
                additional_context=additional_context
            )
            
            # Execute the graph
            result = await self.graph.compiled_graph.ainvoke(initial_state)
            
            # Format the response
            response = {
                "sql_query": result.get("sql_query", ""),
                "explanation": result.get("explanation", ""),
                "execution_result": result.get("execution_result", {}),
                "error": result.get("error", None),
                "success": not bool(result.get("error")),
            }
            
            # Add reflection feedback if available
            if result.get("reflection_feedback"):
                response["reflection_feedback"] = result.get("reflection_feedback")
            
            logger.info(f"Conversion successful: {response['sql_query'][:50]}...")
            return response
            
        except Exception as e:
            logger.exception(f"Error in TextToSQLConverter: {str(e)}")
            return {
                "sql_query": "",
                "explanation": f"Failed to generate SQL: {str(e)}",
                "execution_result": {},
                "error": str(e),
                "success": False
            }
    
    async def convert(
        self,
        query: str,
        connection_params: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        execute: bool = False,
        limit: int = 1000,
        schema_info: Optional[Dict[str, Any]] = None,
        feature_flags: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert a natural language query to SQL (legacy method).
        
        This method is kept for backward compatibility.
        
        Args:
            query: The natural language query
            connection_params: Database connection parameters
            conversation_history: Previous conversation history
            execute: Whether to execute the generated SQL
            limit: Maximum number of results to return
            schema_info: Optional pre-extracted schema information
            feature_flags: Optional feature flags to enable/disable features
            
        Returns:
            Dict containing the SQL query, explanation, and results
        """
        # Apply feature flags if provided
        if feature_flags:
            apply_feature_flags(feature_flags)
        
        logger.info(f"Converting query (legacy method): {query}")
        
        # Delegate to the new method
        result = await self.convert_text_to_sql(
            query=query,
            connection_params=connection_params,
            execute=execute,
            conversation_history=conversation_history
        )
        
        # Format the result for the API (legacy format)
        api_result = {
            "sql": result.get("sql_query", ""),
            "explanation": result.get("explanation", ""),
            "result": result.get("execution_result", {}).get("rows", []),
            "success": result.get("success", False),
            "error": result.get("error", None),
            "metadata": {
                "workflow_stage": "completed",
                "tables_used": [],
                "row_count": len(result.get("execution_result", {}).get("rows", [])),
                "iterations": 1,
                "model_used": "langgraph"
            }
        }
        
        return api_result 
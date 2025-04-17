"""
Graph definition for the LangGraph SQL generation system.

This module defines the LangGraph workflow for SQL generation,
including nodes, edges, and conditional logic.
"""

import logging
from typing import Dict, List, Any, Optional, Annotated, Literal, TypedDict, Union

import langgraph.graph as lg
from langgraph.graph import StateGraph, END

from .state import SQLGenerationState, create_initial_state
from .config import ENABLE_REFLECTION

# Import nodes
from .nodes.schema_extraction import extract_schema
from .nodes.intent_analysis import analyze_intent
from .nodes.sql_generation import generate_sql
from .nodes.reflection import reflect_on_query
from .nodes.execution import execute_sql
from .nodes.explanation import generate_explanation

logger = logging.getLogger(__name__)


def define_workflow_graph() -> StateGraph:
    """
    Define the workflow graph for SQL generation.
    
    This function creates the graph structure with nodes and edges,
    defining how the SQL generation process flows.
    
    Returns:
        A configured StateGraph instance
    """
    # Create a new graph
    workflow = StateGraph(SQLGenerationState)
    
    # Add nodes to the graph
    workflow.add_node("schema_extraction", extract_schema)
    workflow.add_node("intent_analysis", analyze_intent)
    workflow.add_node("sql_generation", generate_sql)
    workflow.add_node("reflection", reflect_on_query)
    workflow.add_node("execution", execute_sql)
    workflow.add_node("explanation", generate_explanation)
    
    # Define edges
    # Start -> Schema Extraction
    workflow.set_entry_point("schema_extraction")
    
    # Schema Extraction -> Intent Analysis
    workflow.add_edge("schema_extraction", "intent_analysis")
    
    # Intent Analysis -> SQL Generation
    workflow.add_edge("intent_analysis", "sql_generation")
    
    # SQL Generation -> Reflection (if enabled) or Execution
    if ENABLE_REFLECTION:
        workflow.add_edge("sql_generation", "reflection")
        
        # Add conditional edge from Reflection
        workflow.add_conditional_edges(
            "reflection",
            condition_based_on_reflection_feedback,
            {
                "regenerate": "sql_generation",
                "execute": "execution",
                "error": END
            }
        )
    else:
        workflow.add_edge("sql_generation", "execution")
    
    # Execution -> Explanation
    workflow.add_edge("execution", "explanation")
    
    # Explanation -> End
    workflow.add_edge("explanation", END)
    
    return workflow


def condition_based_on_reflection_feedback(state: Dict[str, Any]) -> Literal["regenerate", "execute", "error"]:
    """
    Determine the next step based on reflection feedback.
    
    Args:
        state: The current state dictionary
        
    Returns:
        Next step to take: 'regenerate', 'execute', or 'error'
    """
    # Check if there's an error
    if state.get("error"):
        logger.warning(f"Error detected in state: {state.get('error')}")
        return "error"
    
    # Check if we need to regenerate based on reflection feedback
    needs_regeneration = state.get("needs_regeneration", False)
    if needs_regeneration:
        logger.info("Reflection indicates SQL query needs improvement, regenerating")
        return "regenerate"
    
    # Otherwise, proceed to execution
    logger.info("Reflection passed, proceeding to execution")
    return "execute"


class SQLGenerationGraph:
    """
    Main class for managing the SQL generation graph.
    
    This class provides methods to initialize the graph, process
    queries, and retrieve results.
    """
    
    def __init__(self):
        """Initialize the SQL generation graph."""
        self.graph = define_workflow_graph()
        self.compiled_graph = self.graph.compile()
        
        logger.info("SQL generation graph initialized")
    
    async def process_query(
        self,
        user_query: str,
        connection_params: Dict[str, Any],
        execute: bool = False,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Process a natural language query and generate SQL.
        
        Args:
            user_query: The user's natural language query
            connection_params: Database connection parameters
            execute: Whether to execute the generated SQL query
            conversation_history: Conversation history for context
            additional_context: Additional context for SQL generation
            
        Returns:
            Dictionary with SQL generation results
        """
        logger.info(f"Processing query: {user_query}")
        
        # Create initial state
        initial_state = create_initial_state(
            user_query=user_query,
            connection_params=connection_params,
            execute=execute,
            conversation_history=conversation_history,
            additional_context=additional_context
        )
        
        # Execute the graph
        try:
            # Execute the graph with the initial state
            final_state = await self.compiled_graph.ainvoke(initial_state)
            
            # Check for errors
            if final_state.get("error"):
                logger.error(f"Error in graph execution: {final_state.get('error')}")
                return {
                    "error": final_state.get("error"),
                    "sql_query": final_state.get("sql_query", ""),
                    "success": False
                }
            
            # Return the results
            result = {
                "sql_query": final_state.get("sql_query", ""),
                "explanation": final_state.get("explanation", ""),
                "execution_result": final_state.get("execution_result", {}),
                "reflection_feedback": final_state.get("reflection_feedback", {}),
                "success": True
            }
            
            logger.info(f"Query processed successfully: {result['sql_query'][:50]}...")
            return result
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "sql_query": "",
                "success": False
            } 
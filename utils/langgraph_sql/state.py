"""
State definition for the LangGraph SQL generation system.

This module defines the state structure used in the LangGraph system
for generating SQL queries.
"""

from typing import Dict, List, Any, Optional, TypedDict, Union

from pydantic import BaseModel, Field


class SQLGenerationState(BaseModel):
    """State for the SQL generation graph."""
    
    # Input state
    user_query: str = Field(default="", description="The user's natural language query")
    connection_params: Dict[str, Any] = Field(default_factory=dict, description="Database connection parameters")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history for context")
    additional_context: str = Field(default="", description="Additional context for SQL generation")
    execute: bool = Field(default=False, description="Whether to execute the generated SQL query")
    
    # Intermediate state
    schema_info: Dict[str, Any] = Field(default_factory=dict, description="Database schema information")
    intent_analysis_result: Dict[str, Any] = Field(default_factory=dict, description="Analysis of user query intent")
    tables_used: List[str] = Field(default_factory=list, description="Tables used in the query")
    reflection_feedback: Dict[str, Any] = Field(default_factory=dict, description="Feedback from reflection")
    reflection_rating: float = Field(default=0.0, description="Quality rating from reflection (0-10)")
    needs_regeneration: bool = Field(default=False, description="Whether SQL needs regeneration")
    
    # Output state
    sql_query: str = Field(default="", description="The generated SQL query")
    execution_result: Dict[str, Any] = Field(default_factory=dict, description="Results from executing the SQL query")
    explanation: str = Field(default="", description="Natural language explanation of the SQL query")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    # Workflow tracking
    workflow_stage: str = Field(default="init", description="Current stage in the workflow")
    

# Function to create and initialize state
def create_initial_state(
    user_query: str,
    connection_params: Dict[str, Any],
    execute: bool = False,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    additional_context: str = ""
) -> Dict[str, Any]:
    """
    Create an initial state for the SQL generation graph.
    
    Args:
        user_query: The user's natural language query
        connection_params: Database connection parameters
        execute: Whether to execute the generated SQL query
        conversation_history: Conversation history for context
        additional_context: Additional context for SQL generation
        
    Returns:
        Initial state dictionary
    """
    return SQLGenerationState(
        user_query=user_query,
        connection_params=connection_params,
        execute=execute,
        conversation_history=conversation_history or [],
        additional_context=additional_context,
        workflow_stage="init"
    ).dict() 
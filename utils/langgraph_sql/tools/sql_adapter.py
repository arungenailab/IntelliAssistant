"""
SQL generation adapter tool for the LangGraph SQL generation system.

This tool adapts the existing SQL generation functionality for use in the
LangGraph workflow system.
"""

import logging
import time
from typing import Dict, Any, List, Optional

# Import existing SQL generation functionality
from utils.agents.sql_generator import SQLGeneratorAgent

logger = logging.getLogger(__name__)


class SQLGenerationTool:
    """
    Tool for generating SQL queries.
    
    Adapts the existing SQLGeneratorAgent to work within the LangGraph workflow.
    """
    
    def __init__(self):
        """Initialize the SQL generation tool."""
        self.sql_agent = SQLGeneratorAgent("SQLGeneratorAgent")
        self._timestamp = None
        
    async def generate_sql(
        self, 
        query: str, 
        schema_info: Dict[str, Any],
        intent_info: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        reflection_feedback: Optional[List[Dict[str, Any]]] = None,
        iteration_count: int = 0
    ) -> Dict[str, Any]:
        """
        Generate a SQL query based on the user's intent and schema.
        
        Args:
            query: The natural language query from the user
            schema_info: Database schema information
            intent_info: User intent information
            conversation_history: Previous conversation history
            reflection_feedback: Feedback from previous reflection
            iteration_count: Current iteration count
            
        Returns:
            Generated SQL and related information
        """
        self._timestamp = time.time()
        
        try:
            # Prepare feedback for the SQL agent if this is not the first attempt
            agent_feedback = None
            if reflection_feedback and iteration_count > 0:
                last_feedback = reflection_feedback[-1]
                agent_feedback = {
                    "issues": last_feedback.get("issues", []),
                    "suggestions": last_feedback.get("suggestions", []),
                    "revision_focus": last_feedback.get("revision_focus", "")
                }
            
            # Get a list of tables from schema_info
            tables_used = list(schema_info.get("tables", {}).keys()) if isinstance(schema_info.get("tables"), dict) else schema_info.get("tables", [])
            
            # Call the existing SQL agent using the process method
            sql_result = self.sql_agent.process({
                "intent_info": intent_info or {"operation": "select"},
                "validated_columns": {},
                "schema_info": schema_info,
                "tables_used": tables_used
            })
            
            # Process and return in the expected format
            return {
                "sql_query": sql_result.get("sql", ""),
                "explanation": sql_result.get("explanation", "SQL query generated using standard generator"),
                "validated_columns": sql_result.get("validated_columns", {}),
                "confidence": sql_result.get("confidence", 0.0),
                "meta": {
                    "generation_method": "sql_agent",
                    "timestamp": self._timestamp,
                    "iteration": iteration_count
                }
            }
            
        except Exception as e:
            logger.error("Error in SQL generation: %s", str(e), exc_info=True)
            raise
            
    def get_timestamp(self) -> float:
        """
        Get the timestamp of the last generation.
        
        Returns:
            Timestamp of last execution or current time if not executed
        """
        return self._timestamp or time.time() 
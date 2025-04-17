"""
Schema extraction adapter tool for the LangGraph SQL generation system.

This tool adapts the existing schema extraction functionality for use in the
LangGraph workflow system.
"""

import logging
import time
from typing import Dict, Any, List, Optional

# Import existing schema extraction functionality
from utils.agents.schema_agent import SchemaAgent

logger = logging.getLogger(__name__)


class SchemaExtractionTool:
    """
    Tool for extracting database schema information.
    
    Adapts the existing SchemaAgent to work within the LangGraph workflow.
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the schema extraction tool.
        
        Args:
            connection_params: Database connection parameters
        """
        self.connection_params = connection_params
        self.schema_agent = SchemaAgent(connection_params)
        self._timestamp = None
        
    async def extract_schema(
        self, 
        query: str, 
        database_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract relevant schema information based on the user query.
        
        Args:
            query: The natural language query from the user
            database_context: Additional context about the database
            
        Returns:
            Schema information relevant to the query
        """
        self._timestamp = time.time()
        
        try:
            # Call the existing schema agent
            schema_info = await self.schema_agent.extract_relevant_schema(
                query=query, 
                context=database_context or {}
            )
            
            # Process and return in the expected format
            return {
                "relevant_tables": schema_info.get("relevant_tables", []),
                "table_schemas": schema_info.get("table_schemas", {}),
                "relationships": schema_info.get("relationships", []),
                "constraints": schema_info.get("constraints", []),
                "meta": {
                    "database_type": schema_info.get("database_type", "unknown"),
                    "extraction_method": "schema_agent",
                    "timestamp": self._timestamp
                }
            }
            
        except Exception as e:
            logger.error("Error in schema extraction: %s", str(e), exc_info=True)
            raise
            
    def get_timestamp(self) -> float:
        """
        Get the timestamp of the last extraction.
        
        Returns:
            Timestamp of last execution or current time if not executed
        """
        return self._timestamp or time.time() 
"""
Schema extraction tool adapter for the LangGraph SQL generation system.

This module provides an adapter to extract database schema information
using the existing SQL connector.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SchemaExtractionTool:
    """
    Tool for extracting database schema information.
    
    This adapter uses the existing SQLServerConnector to extract schema
    information and return it in a format suitable for the LangGraph system.
    """
    
    def __init__(self):
        """Initialize the schema extraction tool."""
        pass
    
    async def extract_schema(
        self,
        connection_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract schema information from a database.
        
        Args:
            connection_params: Database connection parameters
            
        Returns:
            Dictionary containing schema information or empty dict on error
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
                return {}
            
            try:
                # Get schema information
                schema_info = {}
                
                # Get all tables
                tables = connector.list_tables()
                
                # For each table, get the columns
                for table in tables:
                    columns = connector.get_table_columns(table)
                    
                    # Format the schema info
                    schema_info[table] = {
                        "columns": columns
                    }
                
                # Get relationships if available
                # This is a placeholder - actual implementation depends on the connector's capabilities
                relationships = []
                if hasattr(connector, 'get_relationships'):
                    relationships = connector.get_relationships()
                
                if relationships:
                    schema_info["relationships"] = relationships
                
                logger.info(f"Extracted schema for {len(tables)} tables")
                
                return schema_info
                
            finally:
                # Always disconnect
                connector.disconnect()
                
        except Exception as e:
            error_msg = f"Schema extraction error: {str(e)}"
            logger.error(error_msg)
            return {} 
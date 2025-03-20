"""
Schema Agent module for extracting and managing database schema information.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Set

from utils.agents.base_agent import BaseAgent
from utils.sql_connector import SQLServerConnector

# Configure logging
logger = logging.getLogger(__name__)

class SchemaAgent(BaseAgent):
    """
    Agent responsible for extracting and managing database schema information.
    Maintains a cache of schema information to avoid redundant queries.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Schema Agent.
        
        Args:
            name (str): Name of the agent
            config (Dict[str, Any], optional): Configuration for the agent
        """
        super().__init__(name, config)
        
        # Schema cache: {connection_string: {schema_data}}
        self.schema_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = self.config.get("schema_cache_ttl", 3600)  # 1 hour by default
        self.cache_timestamps: Dict[str, float] = {}
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data to extract and validate database schema.
        
        Args:
            input_data (Dict[str, Any]): Input data including connection parameters
            
        Returns:
            Dict[str, Any]: Results including schema information
        """
        # Validate input
        if not self.validate_input(input_data, ["connection_params"]):
            return {
                "success": False,
                "error": "Missing required connection parameters",
                "schema_info": {}
            }
        
        connection_params = input_data["connection_params"]
        
        try:
            # Get schema information
            schema_info = self._get_schema_info(connection_params)
            
            if not schema_info:
                logger.error("Failed to retrieve schema information")
                return {
                    "success": False,
                    "error": "Failed to retrieve database schema",
                    "schema_info": {}
                }
            
            # Store schema in state
            self.update_state({"schema_info": schema_info})
            
            # Return success
            result = {
                "success": True,
                "schema_info": schema_info,
                "tables": list(schema_info.get("tables", {}).keys()),
                "schema_source": "cache" if self._is_from_cache(connection_params) else "fresh"
            }
            
            self.log_result(result)
            return result
            
        except Exception as e:
            logger.exception(f"Error in SchemaAgent: {str(e)}")
            return {
                "success": False,
                "error": f"Schema extraction error: {str(e)}",
                "schema_info": {}
            }
    
    def _get_connection_key(self, connection_params: Dict[str, Any]) -> str:
        """
        Generate a unique key for the connection parameters.
        
        Args:
            connection_params (Dict[str, Any]): Connection parameters
            
        Returns:
            str: Unique key for the connection
        """
        # Create a stable representation of connection parameters
        server = connection_params.get("server", "")
        database = connection_params.get("database", "")
        return f"{server}:{database}"
    
    def _is_cache_valid(self, connection_key: str) -> bool:
        """
        Check if the cached schema is still valid.
        
        Args:
            connection_key (str): Unique key for the connection
            
        Returns:
            bool: True if cache is valid, False otherwise
        """
        if connection_key not in self.cache_timestamps:
            return False
            
        timestamp = self.cache_timestamps[connection_key]
        current_time = time.time()
        
        return (current_time - timestamp) < self.cache_ttl
    
    def _is_from_cache(self, connection_params: Dict[str, Any]) -> bool:
        """
        Check if the schema for these connection params was served from cache.
        
        Args:
            connection_params (Dict[str, Any]): Connection parameters
            
        Returns:
            bool: True if schema was served from cache
        """
        connection_key = self._get_connection_key(connection_params)
        return connection_key in self.state.get("cache_used", set())
    
    def _get_schema_info(self, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get schema information from cache or by querying the database.
        
        Args:
            connection_params (Dict[str, Any]): Database connection parameters
            
        Returns:
            Dict[str, Any]: Schema information
        """
        connection_key = self._get_connection_key(connection_params)
        
        # Check cache first
        if connection_key in self.schema_cache and self._is_cache_valid(connection_key):
            logger.info(f"Using cached schema for {connection_key}")
            
            # Track that we used cache for this request
            cache_used = self.state.get("cache_used", set())
            cache_used.add(connection_key)
            self.update_state({"cache_used": cache_used})
            
            return self.schema_cache[connection_key]
        
        # Cache miss or expired, query the database
        logger.info(f"Fetching fresh schema for {connection_key}")
        
        # Connect to the database and get schema
        connector = SQLServerConnector(connection_params)
        try:
            connector.connect()
            
            # Get database DDL (tables, columns, relationships)
            schema_info = connector.get_database_ddl()
            
            # Enhance schema with additional metadata
            self._enhance_schema(schema_info)
            
            # Cache the results
            self.schema_cache[connection_key] = schema_info
            self.cache_timestamps[connection_key] = time.time()
            
            # Clear cache used tracking for this connection
            cache_used = self.state.get("cache_used", set())
            if connection_key in cache_used:
                cache_used.remove(connection_key)
                self.update_state({"cache_used": cache_used})
            
            return schema_info
            
        except Exception as e:
            logger.exception(f"Error fetching schema: {str(e)}")
            raise
        finally:
            connector.close()
    
    def _enhance_schema(self, schema_info: Dict[str, Any]) -> None:
        """
        Enhance schema with additional metadata for better matching.
        
        Args:
            schema_info (Dict[str, Any]): Schema information to enhance
        """
        # Add common aliases for tables
        if "tables" in schema_info:
            for table_name, table_info in schema_info["tables"].items():
                # Simple pluralization/singularization
                if table_name.endswith('s'):
                    table_info["aliases"] = [table_name, table_name[:-1]]
                else:
                    table_info["aliases"] = [table_name, f"{table_name}s"]
        
        # Add common aliases for columns
        if "tables" in schema_info:
            for table_name, table_info in schema_info["tables"].items():
                if "columns" in table_info:
                    for col_name, col_info in table_info["columns"].items():
                        # Add aliases for common patterns
                        aliases = [col_name]
                        
                        # ID -> Identifier
                        if col_name.lower() == "id":
                            aliases.append("identifier")
                        
                        # created_at -> creation date
                        if col_name.lower() == "created_at":
                            aliases.extend(["creation date", "creation time"])
                        
                        # updated_at -> update date
                        if col_name.lower() == "updated_at":
                            aliases.extend(["update date", "update time"])
                        
                        col_info["aliases"] = aliases
    
    def invalidate_cache(self, connection_params: Optional[Dict[str, Any]] = None) -> None:
        """
        Invalidate the schema cache, either for a specific connection or all.
        
        Args:
            connection_params (Dict[str, Any], optional): Connection parameters
                If None, invalidate all cached schemas
        """
        if connection_params:
            connection_key = self._get_connection_key(connection_params)
            if connection_key in self.schema_cache:
                del self.schema_cache[connection_key]
                del self.cache_timestamps[connection_key]
                logger.info(f"Cache invalidated for {connection_key}")
        else:
            self.schema_cache.clear()
            self.cache_timestamps.clear()
            logger.info("All schema caches invalidated") 
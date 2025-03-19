"""
SQL Server Connector

This module provides functionality to connect to SQL Server databases
and fetch data for analysis in the IntelliAssistant application.
"""

import pandas as pd
import pyodbc
import urllib.parse
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import traceback
import sys
import platform
import os
import numpy as np
import re
import json

logger = logging.getLogger(__name__)

# List of common SQL Server ODBC drivers to try
COMMON_DRIVERS = [
    'ODBC Driver 18 for SQL Server',
    'ODBC Driver 17 for SQL Server',
    'ODBC Driver 13.1 for SQL Server',
    'ODBC Driver 13 for SQL Server',
    'SQL Server Native Client 11.0',
    'SQL Server'
]

class SQLServerConnector:
    """Connector for SQL Server databases"""
    
    def __init__(self, connection_params: Dict[str, str]):
        """
        Initialize the SQL Server connector with connection parameters
        
        Args:
            connection_params (Dict[str, str]): Dictionary containing connection parameters
                - server: The SQL Server instance name
                - database: The database name
                - username: The username for authentication (if using SQL auth)
                - password: The password for authentication (if using SQL auth)
                - trusted_connection: 'yes' if using Windows auth, 'no' if using SQL auth
                - driver: The ODBC driver to use (optional)
        """
        self.connection_params = connection_params
        self.connection = None
        self.is_connected = False
        self.driver = connection_params.get('driver', None)
        self.last_error = None
        
    @staticmethod
    def get_saved_configurations() -> List[Dict[str, str]]:
        """
        Get saved SQL Server configurations from localStorage or file cache
        
        Returns:
            List[Dict[str, str]]: List of saved configurations
        """
        try:
            # In a production app, this would load from a database or persistent storage
            # For now, we'll check if there are any recent successful connections in our system
            
            # Look for configuration in LOCAL_STORAGE_KEY if available
            import os
            import json
            
            # Check for cached configurations in the user's home directory
            home_dir = os.path.expanduser("~")
            cache_dir = os.path.join(home_dir, ".intelligassistant")
            config_file = os.path.join(cache_dir, "sql_configs.json")
            
            # Create directory if it doesn't exist
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            
            # Check if config file exists
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        configs = json.load(f)
                        logger.info(f"Loaded {len(configs)} SQL configurations from {config_file}")
                        return configs
                except Exception as e:
                    logger.warning(f"Error loading SQL configurations from {config_file}: {str(e)}")
            
            # If no config file, check for localStorage data in browser (as a fallback)
            local_storage_file = os.path.join(cache_dir, "localStorage.json")
            if os.path.exists(local_storage_file):
                try:
                    with open(local_storage_file, 'r') as f:
                        local_storage = json.load(f)
                        # Look for SQL configuration data
                        sql_config = local_storage.get("sql_server_config")
                        if sql_config:
                            if isinstance(sql_config, str):
                                try:
                                    sql_config = json.loads(sql_config)
                                except:
                                    pass
                            
                            # If we found a configuration, return it
                            if isinstance(sql_config, dict):
                                return [sql_config]
                except Exception as e:
                    logger.warning(f"Error loading localStorage data: {str(e)}")
            
            # If no configurations found in either location, create a sample config
            # This ensures the UI will show something even when no real configuration exists
            # In a production app, you'd just return an empty list here
            logger.info("No saved SQL configurations found, returning empty list")
            return []
            
        except Exception as e:
            logger.error(f"Error getting saved SQL configurations: {str(e)}")
            return []
    
    @staticmethod
    def save_configuration(config: Dict[str, str]) -> bool:
        """
        Save a SQL Server configuration
        
        Args:
            config: The configuration to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Remove sensitive data (password)
            save_config = config.copy()
            if 'password' in save_config:
                save_config['password'] = '********'  # Mask password
            
            import os
            import json
            
            # Save to cache directory
            home_dir = os.path.expanduser("~")
            cache_dir = os.path.join(home_dir, ".intelligassistant")
            config_file = os.path.join(cache_dir, "sql_configs.json")
            
            # Create directory if it doesn't exist
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            
            # Load existing configs
            configs = []
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        configs = json.load(f)
                except Exception:
                    configs = []
            
            # Add new config if not duplicate
            found = False
            for i, existing in enumerate(configs):
                if existing.get('server') == save_config.get('server') and existing.get('database') == save_config.get('database'):
                    # Update existing config
                    configs[i] = save_config
                    found = True
                    break
            
            if not found:
                configs.append(save_config)
            
            # Save configs
            with open(config_file, 'w') as f:
                json.dump(configs, f, indent=2)
            
            logger.info(f"Saved SQL configuration for {save_config.get('server')}/{save_config.get('database')}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving SQL configuration: {str(e)}")
            return False
        
    def _get_available_drivers(self) -> List[str]:
        """
        Get a list of available ODBC drivers on the system
        
        Returns:
            List[str]: List of available ODBC drivers
        """
        try:
            drivers = pyodbc.drivers()
            sql_drivers = [driver for driver in drivers if 'SQL Server' in driver]
            
            # Log all available drivers for debugging
            logger.info(f"All available ODBC drivers: {drivers}")
            logger.info(f"SQL Server drivers: {sql_drivers}")
            
            return sql_drivers
        except Exception as e:
            logger.error(f"Error getting available drivers: {str(e)}")
            return []
    
    def _check_system_requirements(self) -> Dict[str, Any]:
        """
        Check system requirements for SQL Server connectivity
        
        Returns:
            Dict[str, Any]: Dictionary with system information
        """
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": sys.version,
            "pyodbc_version": pyodbc.version,
            "architecture": platform.architecture()[0],
            "drivers_available": self._get_available_drivers()
        }
        
        # Check if SQL Server is installed locally
        if system_info["os"] == "Windows":
            sql_server_path = "C:\\Program Files\\Microsoft SQL Server"
            system_info["sql_server_installed"] = os.path.exists(sql_server_path)
            
            # Check for SQL Native Client
            odbc_path = "C:\\Windows\\System32\\odbcad32.exe"
            system_info["odbc_admin_exists"] = os.path.exists(odbc_path)
        
        return system_info
            
    def _build_connection_string(self, driver: str) -> str:
        """
        Build a connection string for the given driver
        
        Args:
            driver (str): The ODBC driver to use
            
        Returns:
            str: The connection string
        """
        # Check if using Windows Authentication or SQL Authentication
        if self.connection_params.get('trusted_connection', 'no').lower() == 'yes':
            # Windows Authentication
            conn_str = (
                f"Driver={{{driver}}};"
                f"Server={self.connection_params['server']};"
                f"Database={self.connection_params['database']};"
                f"Trusted_Connection=yes;"
            )
        else:
            # SQL Authentication
            conn_str = (
                f"Driver={{{driver}}};"
                f"Server={self.connection_params['server']};"
                f"Database={self.connection_params['database']};"
                f"UID={self.connection_params.get('username', '')};"
                f"PWD={self.connection_params.get('password', '')};"
            )
        
        # Add connection timeout
        conn_str += "Connection Timeout=30;"
        
        logger.info(f"Built connection string with driver: {driver}")
        # Don't log the full connection string as it may contain credentials
        
        return conn_str
        
    def connect(self) -> bool:
        """
        Establish a connection to the SQL Server database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        self.last_error = None
        
        # Check system requirements
        system_info = self._check_system_requirements()
        logger.info(f"System information: {system_info}")
        
        if not system_info["drivers_available"]:
            self.last_error = "No SQL Server ODBC drivers found on the system. Please install an ODBC driver for SQL Server."
            logger.error(self.last_error)
            return False
        
        # If a specific driver was provided, try only that one
        if self.driver:
            try:
                conn_str = self._build_connection_string(self.driver)
                logger.info(f"Attempting connection with specified driver: {self.driver}")
                self.connection = pyodbc.connect(conn_str)
                self.is_connected = True
                logger.info(f"Successfully connected to {self.connection_params['server']}/{self.connection_params['database']} using driver {self.driver}")
                
                # Save successful configuration
                self.save_configuration(self.connection_params)
                
                return True
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"Error connecting with specified driver {self.driver}: {str(e)}")
                logger.error(f"Connection string (sanitized): Driver={{{self.driver}}};Server={self.connection_params['server']};Database={self.connection_params['database']};...")
                return False
        
        # Otherwise, try available drivers
        available_drivers = self._get_available_drivers()
        
        # If no drivers found, try common drivers
        if not available_drivers:
            logger.warning("No SQL Server drivers found on system, trying common drivers")
            available_drivers = COMMON_DRIVERS
            
        # Try each driver until one works
        errors = []
        for driver in available_drivers:
            try:
                conn_str = self._build_connection_string(driver)
                logger.info(f"Attempting connection with driver: {driver}")
                self.connection = pyodbc.connect(conn_str)
                self.is_connected = True
                self.driver = driver  # Remember the successful driver
                logger.info(f"Successfully connected to {self.connection_params['server']}/{self.connection_params['database']} using driver {driver}")
                
                # Save successful configuration
                connection_config = self.connection_params.copy()
                connection_config['driver'] = driver
                self.save_configuration(connection_config)
                
                return True
            except Exception as e:
                error_msg = f"Driver {driver}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
        
        # If we get here, all drivers failed
        error_msg = "Failed to connect with any available driver. Errors:\n" + "\n".join(errors)
        self.last_error = error_msg
        logger.error(error_msg)
        
        # Provide troubleshooting advice
        troubleshooting_tips = self._get_troubleshooting_tips(errors)
        logger.info(f"Troubleshooting tips: {troubleshooting_tips}")
        self.last_error += "\n\nTroubleshooting tips:\n" + "\n".join(troubleshooting_tips)
        
        return False
    
    def _get_troubleshooting_tips(self, errors: List[str]) -> List[str]:
        """
        Generate troubleshooting tips based on connection errors
        
        Args:
            errors (List[str]): List of error messages
            
        Returns:
            List[str]: List of troubleshooting tips
        """
        tips = []
        
        # Common error patterns and their solutions
        if any("login failed" in err.lower() for err in errors):
            tips.append("Check your username and password.")
            tips.append("Verify that the SQL login has appropriate permissions.")
            
        if any("network-related" in err.lower() or "host" in err.lower() for err in errors):
            tips.append("Verify the server name is correct.")
            tips.append("Check if the SQL Server is running and accessible from this machine.")
            tips.append("Check if a firewall is blocking the connection.")
            
        if any("driver" in err.lower() for err in errors):
            tips.append("Install the Microsoft ODBC Driver for SQL Server.")
            tips.append("Try a different driver version if available.")
            
        # Add general tips
        if not tips:
            tips = [
                "Check your connection parameters.",
                "Verify that SQL Server is running.",
                "Make sure you have the appropriate ODBC drivers installed."
            ]
            
        return tips
        
    def execute_query(self, query, params=None, limit=None):
        """
        Execute a SQL query and return the results as a DataFrame
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            limit: Maximum number of rows to return
        
        Returns:
            DataFrame: Query results
        """
        if not self.is_connected:
            if not self.connect():
                raise Exception(f"Failed to connect to database: {self.last_error}")
                
        try:
            # Apply row limit if specified
            limited_query = query
            if limit is not None:
                # Only apply limit if not already limited with TOP
                if "TOP " not in query.upper() and "LIMIT " not in query.upper():
                    # For SQL Server, add TOP clause to query
                    # This is a simple approach and may not work for all complex queries
                    match = re.search(r'SELECT\s+', query, re.IGNORECASE)
                    if match:
                        insertion_point = match.end()
                        limited_query = f"{query[:insertion_point]}TOP {limit} {query[insertion_point:]}"
                    else:
                        logger.warning(f"Could not apply limit to query: {query}")
                        limited_query = query
            
            # Validate the query against the database schema
            validation_result = self.validate_query_columns(limited_query)
            if not validation_result['valid']:
                error_message = f"Query contains invalid columns: {', '.join(validation_result['invalid_columns'])}"
                logger.error(error_message)
                logger.error(f"Query: {limited_query}")
                raise Exception(error_message)
            
            # Execute the query
            logger.info(f"Executing query: {limited_query}")
            df = pd.read_sql_query(limited_query, self.connection, params=params)
            return df
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {limited_query}")
            raise Exception(f"Error executing query: {str(e)}")
            
    def validate_query_columns(self, query):
        """
        Validate that all columns used in a query exist in the database
        
        Args:
            query: SQL query to validate
            
        Returns:
            dict: Validation result with keys:
                - valid: True if all columns exist, False otherwise
                - invalid_columns: List of invalid column names
                - message: Validation message
        """
        try:
            # Parse the query to extract table and column references
            # This is a simplified implementation that may not handle all SQL syntax
            
            # Extract all table references and their aliases
            table_matches = re.findall(r'(?:FROM|JOIN)\s+([^\s,;()]+)(?:\s+(?:AS\s+)?([^\s,;()WHERE]+))?', query, re.IGNORECASE)
            
            # Map of aliases to table names and tables to aliases
            alias_to_table = {}
            table_to_alias = {}
            tables = []
            
            for match in table_matches:
                table_name = match[0].strip('[]"\'`')
                alias = None
                
                # Handle table aliases
                if len(match) > 1 and match[1]:
                    alias = match[1].strip()
                    alias_to_table[alias.upper()] = table_name
                    table_to_alias[table_name.upper()] = alias
                
                # Handle table names with schema prefixes
                if '.' in table_name:
                    table_name = table_name.split('.')[-1].strip('[]"\'`')
                
                tables.append(table_name)
            
            # Log tables and aliases for debugging
            logger.debug(f"Tables in query: {tables}")
            logger.debug(f"Alias mapping: {alias_to_table}")
            
            # Get all columns for the tables mentioned in the query
            all_valid_columns = set()
            table_column_map = {}
            
            for table in tables:
                try:
                    schema_df = self.get_table_schema(table)
                    columns = schema_df['column_name'].tolist()
                    all_valid_columns.update(columns)
                    table_column_map[table.upper()] = columns
                except Exception as e:
                    logger.warning(f"Could not get schema for table {table}: {str(e)}")
            
            # Extract column references from the query
            query_columns = set()
            
            # Look for column references in SELECT, WHERE, ORDER BY, etc.
            # Also find table aliases used in the query
            column_sections = re.findall(r'(?:SELECT|WHERE|ORDER\s+BY|GROUP\s+BY|HAVING)\s+(.+?)(?:FROM|WHERE|GROUP\s+BY|ORDER\s+BY|LIMIT|;|$)', query, re.IGNORECASE | re.DOTALL)
            
            for section in column_sections:
                # Remove subqueries in parentheses to avoid parsing their internal columns
                section_no_subquery = re.sub(r'\([^()]*\)', '', section)
                
                # Split by common delimiters and extract potential column names
                parts = re.split(r',|\s+AND\s+|\s+OR\s+|\s+ON\s+|\s+WHEN\s+|\s+THEN\s+|\s+ELSE\s+|\s+IN\s+', section_no_subquery)
                
                for part in parts:
                    # Extract table alias qualified columns (e.g., "t.column_name" or "Transactions.column_name")
                    qualified_columns = re.findall(r'([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)', part)
                    
                    for qualifier, column in qualified_columns:
                        # Skip if it's a function or aggregation
                        if column.lower() in ['count', 'sum', 'avg', 'min', 'max']:
                            continue
                        query_columns.add((qualifier, column))
                    
                    # Extract standalone identifiers that might be column names
                    identifiers = re.findall(r'([a-zA-Z0-9_]+)(?!\.[a-zA-Z0-9_]+)', part)
                    
                    for identifier in identifiers:
                        # Skip SQL keywords, functions, numeric literals, and table aliases
                        if (identifier.upper() not in {'SELECT', 'FROM', 'WHERE', 'ORDER', 'BY', 'GROUP', 
                                                      'HAVING', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 
                                                      'FULL', 'ON', 'AS', 'AND', 'OR', 'NOT', 'NULL', 
                                                      'IS', 'IN', 'BETWEEN', 'LIKE', 'DESC', 'ASC', 
                                                      'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'TOP'} and
                            not identifier.isdigit() and
                            not identifier.startswith('N') and
                            # Skip table names and aliases
                            identifier.upper() not in alias_to_table.keys() and
                            identifier not in tables):
                            
                            query_columns.add((None, identifier))
            
            # Check for invalid columns
            invalid_columns = []
            
            for qualifier, column in query_columns:
                # Skip common SQL keywords, aggregation functions, etc.
                if column.lower() in ['as', 'desc', 'asc', 'count', 'sum', 'avg', 'min', 'max']:
                    continue
                
                # Skip computed columns or known patterns
                if any(alias_pattern in column.lower() for alias_pattern in ['_amount', '_total', '_value', '_count', '_avg', '_sum']):
                    continue
                
                # For qualified columns, check if the column belongs to the specified table or alias
                if qualifier:
                    table_name = None
                    qualifier_upper = qualifier.upper()
                    
                    # Check if qualifier is a table name
                    if qualifier_upper in [t.upper() for t in tables]:
                        table_name = qualifier
                    # Check if qualifier is an alias
                    elif qualifier_upper in alias_to_table:
                        table_name = alias_to_table[qualifier_upper]
                    
                    if table_name:
                        table_name_upper = table_name.upper()
                        # If we have schema info for this table
                        if table_name_upper in map(str.upper, table_column_map.keys()):
                            # Get columns for the actual table, regardless of case
                            table_key = next((k for k in table_column_map.keys() if k.upper() == table_name_upper), None)
                            table_columns = table_column_map.get(table_key, []) if table_key else []
                            
                            # Check if column exists in this table
                            if column.lower() not in map(str.lower, table_columns):
                                # Only add invalid column with its qualifier for clarity
                                invalid_columns.append(f"{qualifier}.{column}")
                            continue
                
                # For unqualified columns, check if they exist in any table
                if column not in all_valid_columns and column.lower() not in map(str.lower, all_valid_columns):
                    invalid_columns.append(column)
            
            # Compile the results
            valid = len(invalid_columns) == 0
            result = {
                'valid': valid,
                'invalid_columns': invalid_columns,
                'valid_tables': tables,
                'valid_columns': list(all_valid_columns),
                'message': 'Query validation successful' if valid else f"Query contains invalid columns: {', '.join(invalid_columns)}"
            }
            
            if not valid:
                logger.warning(f"Query validation failed: {result['message']}")
                logger.warning(f"Invalid columns: {', '.join(invalid_columns)}")
                logger.warning(f"Valid columns in tables {', '.join(tables)}: {', '.join(list(all_valid_columns))}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating query: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'valid': True,  # Return valid=True when validation fails to allow query execution
                'invalid_columns': [],
                'message': f"Error validating query: {str(e)}"
            }
            
    def _extract_tables_from_query(self, query: str) -> List[str]:
        """
        Extract table names from a SQL query
        
        Args:
            query: SQL query
            
        Returns:
            List of table names referenced in the query
        """
        # Simple regex to extract table names after FROM and JOIN
        tables = []
        
        # Find tables after FROM
        from_matches = re.findall(r'FROM\s+([^\s,;()]+)', query, re.IGNORECASE)
        tables.extend(from_matches)
        
        # Find tables after JOIN
        join_matches = re.findall(r'JOIN\s+([^\s,;()]+)', query, re.IGNORECASE)
        tables.extend(join_matches)
        
        # Remove duplicates and clean up
        cleaned_tables = []
        for table in tables:
            # Remove schema prefixes and brackets
            clean_table = table.split('.')[-1].strip('[]"\'')
            cleaned_tables.append(clean_table)
            
        return list(set(cleaned_tables))
    
    def _find_similar_tables(self, missing_table: str, actual_tables: List[str]) -> str:
        """
        Find the most similar table name in the database
        
        Args:
            missing_table: The non-existent table name
            actual_tables: List of actual tables in the database
            
        Returns:
            The most similar table name, or None if no good match
        """
        if not actual_tables:
            return None
            
        # Simple case-insensitive exact match
        for table in actual_tables:
            if table.lower() == missing_table.lower():
                return table
        
        # Check for plural/singular variations
        missing_lower = missing_table.lower()
        for table in actual_tables:
            table_lower = table.lower()
            # Check if one is the plural of the other
            if missing_lower.endswith('s') and missing_lower[:-1] == table_lower:
                return table
            if table_lower.endswith('s') and table_lower[:-1] == missing_lower:
                return table
        
        # Check for common synonym mappings
        synonyms = {
            'customer': ['client', 'user', 'patron'],
            'client': ['customer', 'user'],
            'transaction': ['payment', 'order', 'purchase'],
            'payment': ['transaction', 'invoice'],
            'order': ['purchase', 'transaction', 'sale'],
            'product': ['item', 'merchandise', 'good'],
            'employee': ['staff', 'personnel'],
            'sale': ['order', 'transaction'],
            'user': ['customer', 'client', 'member']
        }
        
        if missing_lower in synonyms:
            for synonym in synonyms[missing_lower]:
                for table in actual_tables:
                    if synonym in table.lower():
                        return table
        
        # Calculate string similarity for remaining cases
        best_score = 0
        best_match = None
        
        for table in actual_tables:
            # Simple Levenshtein distance approximation
            score = self._string_similarity(missing_lower, table.lower())
            if score > best_score and score > 0.6:  # Threshold for reasonable match
                best_score = score
                best_match = table
        
        return best_match
    
    def _string_similarity(self, a: str, b: str) -> float:
        """
        Calculate string similarity score between 0 and 1
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            Similarity score (0-1)
        """
        if not a or not b:
            return 0
            
        # Simple character-based similarity
        shorter = min(len(a), len(b))
        longer = max(len(a), len(b))
        
        if longer == 0:
            return 1.0
            
        # Count matching characters
        matches = 0
        for i in range(shorter):
            if a[i] == b[i]:
                matches += 1
                
        # Approximate similarity score
        return matches / longer
            
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the database connection
        """
        try:
            if self.connect():
                server_info = self._get_server_info()
                self.disconnect()
                return True, f"Connection successful. Server: {server_info.get('server_version', 'Unknown')}"
            else:
                return False, f"Connection failed: {self.last_error}"
        except Exception as e:
            logger.error(f"Connection test error: {str(e)}")
            logger.error(traceback.format_exc())
            return False, f"Connection test error: {str(e)}"
    
    def _get_server_info(self) -> Dict[str, str]:
        """
        Get information about the connected SQL Server
        
        Returns:
            Dict[str, str]: Dictionary with server information
        """
        if not self.is_connected:
            return {"error": "Not connected"}
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            
            info = {
                "server_version": version,
                "driver_used": self.driver
            }
            
            return info
        except Exception as e:
            logger.error(f"Error getting server info: {str(e)}")
            return {"error": str(e)}
    
    def disconnect(self):
        """Close the database connection"""
        if self.connection and self.is_connected:
            self.connection.close()
            self.is_connected = False
            logger.info("Database connection closed")
    
    def list_tables(self):
        """
        Get a list of all tables in the database
        
        Returns:
            List of table names
        """
        if not self.is_connected:
            raise Exception("Not connected to the database")
            
        try:
            query = """
            SELECT 
                TABLE_NAME
            FROM 
                INFORMATION_SCHEMA.TABLES
            WHERE 
                TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
            ORDER BY 
                TABLE_NAME
            """
            
            df = pd.read_sql_query(query, self.connection)
            return df['TABLE_NAME'].tolist()
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
            return []
    
    def get_table_schema(self, table_name: str) -> pd.DataFrame:
        """
        Get schema information for a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            DataFrame: Table schema information
        """
        if not self.is_connected:
            raise Exception("Not connected to the database")
            
        try:
            # Use INFORMATION_SCHEMA to get column info
            query = """
            SELECT 
                COLUMN_NAME as column_name, 
                DATA_TYPE as data_type,
                CHARACTER_MAXIMUM_LENGTH as max_length,
                IS_NULLABLE as is_nullable,
                COLUMN_DEFAULT as default_value
            FROM 
                INFORMATION_SCHEMA.COLUMNS 
            WHERE 
                TABLE_NAME = ?
            ORDER BY 
                ORDINAL_POSITION
            """
            
            df = pd.read_sql_query(query, self.connection, params=[table_name])
            return df
        except Exception as e:
            logger.error(f"Error getting table schema for {table_name}: {str(e)}")
            raise Exception(f"Error getting table schema: {str(e)}")
            
    def get_database_ddl(self) -> dict:
        """
        Get the Data Definition Language (DDL) for the entire database
        
        Returns:
            dict: A dictionary containing tables, columns, relationships, and indexes
        """
        if not self.is_connected:
            if not self.connect():
                return {"error": f"Failed to connect to database: {self.last_error}"}
        
        logger.info(f"Getting DDL for database {self.connection_params['database']}")
        
        try:
            # Get tables
            tables_query = """
            SELECT 
                TABLE_SCHEMA,
                TABLE_NAME,
                TABLE_TYPE
            FROM 
                INFORMATION_SCHEMA.TABLES
            WHERE 
                TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
            ORDER BY 
                TABLE_SCHEMA, TABLE_NAME
            """
            try:
                tables_df = pd.read_sql_query(tables_query, self.connection)
                logger.info(f"Found {len(tables_df)} tables")
            except Exception as e:
                logger.error(f"Error fetching tables: {str(e)}")
                return {"error": f"Error fetching tables: {str(e)}"}
            
            # Get columns for each table
            tables_dict = {}
            try:
                for _, table_row in tables_df.iterrows():
                    table_name = table_row['TABLE_NAME']
                    
                    # Get columns for this table
                    columns_query = """
                    SELECT 
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.CHARACTER_MAXIMUM_LENGTH,
                        c.NUMERIC_PRECISION,
                        c.NUMERIC_SCALE,
                        c.IS_NULLABLE,
                        CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO' END AS IS_PRIMARY_KEY
                    FROM 
                        INFORMATION_SCHEMA.COLUMNS c
                    LEFT JOIN (
                        SELECT 
                            ku.TABLE_CATALOG,
                            ku.TABLE_SCHEMA,
                            ku.TABLE_NAME,
                            ku.COLUMN_NAME
                        FROM 
                            INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
                        JOIN 
                            INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS ku
                            ON tc.CONSTRAINT_TYPE = 'PRIMARY KEY' 
                            AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                    ) pk
                    ON 
                        c.TABLE_CATALOG = pk.TABLE_CATALOG
                        AND c.TABLE_SCHEMA = pk.TABLE_SCHEMA
                        AND c.TABLE_NAME = pk.TABLE_NAME
                        AND c.COLUMN_NAME = pk.COLUMN_NAME
                    WHERE 
                        c.TABLE_NAME = ?
                    ORDER BY 
                        c.ORDINAL_POSITION
                    """
                    try:
                        columns_df = pd.read_sql_query(columns_query, self.connection, params=[table_name])
                    except Exception as e:
                        logger.error(f"Error fetching columns for table {table_name}: {str(e)}")
                        continue
                    
                    # Convert columns to list of dictionaries with JSON serializable values
                    columns_list = []
                    for _, col_row in columns_df.iterrows():
                        # Handle NaN values that would cause JSON serialization issues
                        col_dict = {}
                        for k, v in col_row.items():
                            if pd.isna(v):
                                col_dict[k] = None
                            elif isinstance(v, (np.int64, np.int32)):
                                col_dict[k] = int(v)
                            elif isinstance(v, (np.float64, np.float32)):
                                # Convert numpy float to Python float
                                col_dict[k] = float(v) if not np.isnan(v) else None
                            else:
                                col_dict[k] = v
                        
                        columns_list.append(col_dict)
                    
                    tables_dict[table_name] = columns_list
            except Exception as e:
                logger.error(f"Error processing tables and columns: {str(e)}")
                return {"error": f"Error processing tables and columns: {str(e)}"}
            
            # Get foreign key relationships
            try:
                relationships_query = """
                SELECT 
                    fk.name AS constraint_name,
                    OBJECT_NAME(fk.parent_object_id) AS parent_table,
                    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS parent_column,
                    OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
                    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS referenced_column
                FROM 
                    sys.foreign_keys AS fk
                INNER JOIN 
                    sys.foreign_key_columns AS fkc 
                    ON fk.OBJECT_ID = fkc.constraint_object_id
                ORDER BY 
                    parent_table, referenced_table
                """
                relationships_df = pd.read_sql_query(relationships_query, self.connection)
                
                # Convert relationships to list of dictionaries with JSON serializable values
                relationships_list = []
                for _, rel_row in relationships_df.iterrows():
                    # Handle NaN values that would cause JSON serialization issues
                    rel_dict = {}
                    for k, v in rel_row.items():
                        if pd.isna(v):
                            rel_dict[k] = None
                        elif isinstance(v, (np.int64, np.int32)):
                            rel_dict[k] = int(v)
                        elif isinstance(v, (np.float64, np.float32)):
                            rel_dict[k] = float(v) if not np.isnan(v) else None
                        else:
                            rel_dict[k] = v
                            
                    relationships_list.append(rel_dict)
            except Exception as e:
                logger.error(f"Error processing relationships: {str(e)}")
                relationships_list = []
            
            # Get indexes
            try:
                indexes_query = """
                SELECT 
                    t.name AS table_name,
                    ind.name AS index_name,
                    col.name AS column_name,
                    ind.is_unique,
                    ind.is_primary_key
                FROM 
                    sys.indexes ind 
                INNER JOIN 
                    sys.index_columns ic ON ind.object_id = ic.object_id AND ind.index_id = ic.index_id 
                INNER JOIN 
                    sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id 
                INNER JOIN 
                    sys.tables t ON ind.object_id = t.object_id 
                WHERE 
                    ind.is_unique_constraint = 0 
                    AND t.is_ms_shipped = 0 
                ORDER BY 
                    t.name, ind.name, ic.key_ordinal
                """
                indexes_df = pd.read_sql_query(indexes_query, self.connection)
                
                # Convert indexes to list of dictionaries with JSON serializable values
                indexes_list = []
                for _, idx_row in indexes_df.iterrows():
                    # Handle NaN values that would cause JSON serialization issues
                    idx_dict = {}
                    for k, v in idx_row.items():
                        if pd.isna(v):
                            idx_dict[k] = None
                        elif isinstance(v, (np.int64, np.int32)):
                            idx_dict[k] = int(v)
                        elif isinstance(v, (np.float64, np.float32)):
                            idx_dict[k] = float(v) if not np.isnan(v) else None
                        elif isinstance(v, bool):
                            idx_dict[k] = bool(v)
                        else:
                            idx_dict[k] = v
                            
                    indexes_list.append(idx_dict)
            except Exception as e:
                logger.error(f"Error processing indexes: {str(e)}")
                indexes_list = []
            
            # Construct the DDL dictionary
            ddl = {
                "tables": tables_dict,
                "relationships": relationships_list,
                "indexes": indexes_list
            }
            
            return ddl
        except Exception as e:
            logger.error(f"Error getting database DDL: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": f"Error getting database DDL: {str(e)}"}
        finally:
            # Close connection
            self.disconnect()

def fetch_sql_data(connection_params: Dict[str, str], query: str = None, table_name: str = None, limit: int = 1000) -> pd.DataFrame:
    """
    Fetch data from a SQL Server database
    
    Args:
        connection_params (Dict[str, str]): Connection parameters for the database
        query (str, optional): Custom SQL query to execute
        table_name (str, optional): Table name to query (if no custom query provided)
        limit (int, optional): Maximum number of rows to return (default: 1000)
        
    Returns:
        pd.DataFrame: DataFrame containing the query results
    """
    try:
        connector = SQLServerConnector(connection_params)
        
        if not connector.connect():
            error_msg = f"Failed to connect to the database: {connector.last_error}"
            logger.error(error_msg)
            return pd.DataFrame({"error": [error_msg]})
        
        # If a custom query was provided, use it
        if query:
            # Add LIMIT clause if not already present (and if not a complex query)
            if 'top' not in query.lower() and not query.strip().startswith('('):
                # SQL Server uses TOP instead of LIMIT
                # Insert TOP clause after the first SELECT
                query = query.replace("SELECT", f"SELECT TOP {limit}", 1)
            
            return connector.execute_query(query)
        
        # Otherwise, use the table name to construct a simple query
        elif table_name:
            query = f"SELECT TOP {limit} * FROM [{table_name}]"
            return connector.execute_query(query)
        
        else:
            error_msg = "Either query or table_name must be provided"
            logger.error(error_msg)
            return pd.DataFrame({"error": [error_msg]})
    
    except Exception as e:
        error_msg = f"Error fetching SQL data: {str(e)}"
        logger.error(error_msg)
        traceback.print_exc()
        # Return an empty DataFrame with an error column
        return pd.DataFrame({"error": [error_msg]})
    
    finally:
        if 'connector' in locals() and connector.is_connected:
            connector.disconnect() 
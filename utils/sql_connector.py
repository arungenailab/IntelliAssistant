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
        
        # Check for common error patterns
        has_access_denied = any("access denied" in err.lower() for err in errors)
        has_not_exist = any("does not exist" in err.lower() for err in errors)
        has_driver_error = any("driver could not be loaded" in err.lower() for err in errors)
        has_timeout = any("timeout" in err.lower() for err in errors)
        
        if has_access_denied:
            tips.append("- Check your username and password if using SQL Authentication")
            tips.append("- Ensure the user has permissions to access the database")
            
        if has_not_exist:
            tips.append("- Verify the SQL Server instance name is correct")
            tips.append("- Make sure SQL Server is running")
            tips.append("- Check if the server name should include an instance name (e.g., SERVER\\INSTANCE)")
            
        if has_driver_error:
            tips.append("- Install the Microsoft ODBC Driver for SQL Server")
            tips.append("- For Windows: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
            tips.append("- For Linux: https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server")
            
        if has_timeout:
            tips.append("- Check if the SQL Server is accessible from your network")
            tips.append("- Verify firewall settings allow connections to SQL Server (typically port 1433)")
            
        # General tips
        tips.append("- Use SQL Server Configuration Manager to verify SQL Server is running and network protocols are enabled")
        tips.append("- Try connecting with SQL Server Management Studio to verify the server is accessible")
        
        return tips
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the connection to the SQL Server database
        
        Returns:
            Tuple[bool, str]: (Success, Message)
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
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute an SQL query and return the results as a DataFrame
        
        Args:
            query (str): The SQL query to execute
            
        Returns:
            pd.DataFrame: DataFrame containing the query results
        """
        try:
            if not self.is_connected:
                success = self.connect()
                if not success:
                    raise Exception(f"Failed to connect to the database: {self.last_error}")
            
            # Execute the query and fetch results into a DataFrame
            df = pd.read_sql(query, self.connection)
            logger.info(f"Query executed successfully, returned {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
        
    def list_tables(self) -> List[str]:
        """
        Get a list of all tables in the database
        
        Returns:
            List[str]: List of table names
        """
        try:
            if not self.is_connected:
                logger.info("Not connected, attempting to connect")
                success = self.connect()
                if not success:
                    logger.error(f"Failed to connect to the database: {self.last_error}")
                    raise Exception(f"Failed to connect to the database: {self.last_error}")
            
            logger.info("Executing query to get table list")
            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            ORDER BY TABLE_NAME
            """
            
            df = pd.read_sql(query, self.connection)
            tables = df['TABLE_NAME'].tolist()
            logger.info(f"Retrieved {len(tables)} tables from database")
            return tables
            
        except Exception as e:
            logger.error(f"Error getting table list: {str(e)}")
            return []
    
    def get_table_schema(self, table_name: str) -> pd.DataFrame:
        """
        Get schema information for a specific table
        
        Args:
            table_name (str): The name of the table
            
        Returns:
            pd.DataFrame: DataFrame containing column information
        """
        try:
            if not self.is_connected:
                success = self.connect()
                if not success:
                    raise Exception(f"Failed to connect to the database: {self.last_error}")
            
            query = f"""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                CHARACTER_MAXIMUM_LENGTH, 
                IS_NULLABLE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}' 
            ORDER BY ORDINAL_POSITION
            """
            
            df = pd.read_sql(query, self.connection)
            logger.info(f"Retrieved schema for table {table_name}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting table schema: {str(e)}")
            return pd.DataFrame()

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
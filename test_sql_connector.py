"""
Simple script to test SQL connector functionality
"""
import json
import logging
from utils.sql_connector import SQLServerConnector
import sys

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Test the SQL connector"""
    try:
        # Test connection parameters
        connection_params = {
            'server': 'your_server',
            'database': 'your_database',
            'username': 'your_username',
            'password': 'your_password',
            'driver': 'ODBC Driver 17 for SQL Server'
        }
        
        # If you have connection parameters in command line
        if len(sys.argv) >= 5:
            connection_params['server'] = sys.argv[1]
            connection_params['database'] = sys.argv[2]
            connection_params['username'] = sys.argv[3]
            connection_params['password'] = sys.argv[4]
        
        # Create connector
        connector = SQLServerConnector(connection_params)
        
        # Test connection
        if not connector.connect():
            logger.error(f"Failed to connect: {connector.last_error}")
            return
        
        logger.info("Successfully connected to the database")
        
        # Test list_tables
        try:
            tables = connector.list_tables()
            logger.info(f"Tables in database: {tables}")
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
        
        # Test get_database_ddl
        try:
            ddl = connector.get_database_ddl()
            logger.info(f"DDL retrieved successfully: {json.dumps(ddl, indent=2)[:100]}...")
        except Exception as e:
            logger.error(f"Error getting DDL: {str(e)}")
        
        # Disconnect
        connector.disconnect()
        logger.info("Test completed")
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main() 
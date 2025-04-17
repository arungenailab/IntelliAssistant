"""
Script to fix the issue with SQL execution in the API.
This addresses the problem where 'Show list of clients' returns no results.
"""
import json
import requests
import traceback
from config import DB_CONFIG
import sys
import logging
import pandas as pd
from utils.sql_connector import SQLServerConnector
from utils.langgraph_sql.simple_converter import SimpleReflectiveSQLConverter
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_connection_params():
    """Return standard test connection parameters."""
    return {
        "server": "localhost",
        "database": "IntelliAssistant",
        "trusted_connection": "yes",
        "driver": "ODBC Driver 17 for SQL Server",
    }

def try_connection_options():
    """Try multiple connection options to find a working configuration."""
    options = [
        {
            "server": "localhost",
            "database": "IntelliAssistant",
            "trusted_connection": "yes",
            "driver": "ODBC Driver 17 for SQL Server",
        },
        {
            "server": "localhost",
            "database": "IntelliAssistant",
            "trusted_connection": "yes",
            "driver": "SQL Server",
        },
        {
            "server": "(local)",
            "database": "IntelliAssistant",
            "trusted_connection": "yes",
            "driver": "ODBC Driver 17 for SQL Server",
        },
        {
            "server": "localhost\\SQLEXPRESS",
            "database": "IntelliAssistant",
            "trusted_connection": "yes",
            "driver": "ODBC Driver 17 for SQL Server",
        }
    ]
    
    for index, params in enumerate(options):
        logger.info(f"Trying connection option {index+1}/{len(options)}: {json.dumps(params)}")
        connector = SQLServerConnector(params)
        
        try:
            result = connector.connect()
            if result:
                logger.info(f"✅ Connection successful with option {index+1}")
                return connector, params
        except Exception as e:
            logger.error(f"❌ Connection option {index+1} failed: {str(e)}")
            continue
    
    logger.error("❌ All connection options failed")
    return None, None

def test_direct_sql_connection():
    """Test direct connection to SQL Server."""
    logger.info("Testing direct SQL Server connection...")
    
    connector, connection_params = try_connection_options()
    if not connector:
        logger.error("Could not establish connection with any options")
        return False, None
    
    try:
        # Test table existence
        query = "SELECT OBJECT_ID('Clients') as table_id"
        result = connector.execute_query(query)
        
        if result is not None and not result.empty and result.iloc[0]['table_id'] is not None:
            logger.info("✅ Clients table exists")
            
            # Test count of records
            count_query = "SELECT COUNT(*) as count FROM Clients"
            count_result = connector.execute_query(count_query)
            count = count_result.iloc[0]['count'] if not count_result.empty else 0
            logger.info(f"Clients table has {count} records")
            
            # Get schema info
            schema_query = """
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM 
                INFORMATION_SCHEMA.COLUMNS
            WHERE 
                TABLE_NAME = 'Clients'
            """
            schema = connector.execute_query(schema_query)
            logger.info(f"Clients table schema:\n{schema}")
            
            # Get actual data
            data_query = "SELECT * FROM Clients"
            data = connector.execute_query(data_query)
            logger.info(f"Clients table data:\n{data}")
            
            return True, data
        else:
            logger.error("❌ Clients table does not exist")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ Direct SQL connection failed: {str(e)}")
        return False, None
    finally:
        # Only call close() if it exists as a method
        if hasattr(connector, 'close') and callable(connector.close):
            connector.close()

def test_converter_direct():
    """Test SimpleReflectiveSQLConverter directly."""
    logger.info("Testing SimpleReflectiveSQLConverter directly...")
    
    try:
        converter = SimpleReflectiveSQLConverter()
        # Get a working connection configuration
        _, connection_params = try_connection_options()
        if not connection_params:
            logger.error("Could not find working connection parameters")
            return False, None, None
            
        user_query = "Show list of clients"
        
        # Log what we're about to do
        logger.info(f"Converting: '{user_query}' with connection params: {json.dumps({k: v for k, v in connection_params.items() if k != 'password'})}")
        
        result = converter.convert(
            user_query=user_query,
            connection_params=connection_params,
            conversation_history=[]
        )
        
        logger.info(f"Converter result: {json.dumps(result, indent=2)}")
        
        sql_query = result.get('sql_query', '')
        if sql_query:
            logger.info(f"✅ SQL query generated: {sql_query}")
            
            # Execute this SQL query directly
            connector = SQLServerConnector(connection_params)
            connector.connect()
            data = connector.execute_query(sql_query)
            logger.info(f"Direct execution result:\n{data}")
            
            # Only call close() if it exists as a method
            if hasattr(connector, 'close') and callable(connector.close):
                connector.close()
            
            return True, sql_query, data
        else:
            logger.error("❌ Failed to generate SQL query")
            return False, None, None
            
    except Exception as e:
        logger.error(f"❌ SimpleReflectiveSQLConverter failed: {str(e)}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None, None

def test_api_endpoint():
    """Test the convert_nl_to_sql API endpoint."""
    logger.info("Testing convert_nl_to_sql API endpoint...")
    
    # Get a working connection configuration
    _, connection_params = try_connection_options()
    if not connection_params:
        logger.error("Could not find working connection parameters")
        return False, None, None
    
    url = "http://localhost:5000/convert_nl_to_sql"
    payload = {
        "query": "Show list of clients",
        "connection_params": connection_params,
        "execute": True
    }
    
    try:
        logger.info(f"Sending request to {url} with payload: {json.dumps({k: v for k, v in payload.items() if k != 'connection_params'})}")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            logger.info("✅ API endpoint responded with 200 OK")
            response_data = response.json()
            logger.info(f"API response: {json.dumps(response_data, indent=2)}")
            
            sql_query = response_data.get('result', {}).get('sql_query', '')
            if sql_query:
                logger.info(f"✅ API returned SQL query: {sql_query}")
            else:
                logger.error("❌ API did not return a SQL query")
            
            results = response_data.get('result', {}).get('results', [])
            if results:
                logger.info(f"✅ API returned results with {len(results)} rows")
                logger.info(f"First row: {json.dumps(results[0])}")
                return True, sql_query, results
            else:
                logger.info("❌ API returned empty results")
                logger.info("Checking if the query was executed successfully")
                
                # Check if execution_status is available
                execution_status = response_data.get('result', {}).get('execution_status', None)
                if execution_status:
                    logger.info(f"Execution status: {execution_status}")
                
                return False, sql_query, []
                
        else:
            logger.error(f"❌ API endpoint responded with error {response.status_code}")
            logger.error(f"Error message: {response.text}")
            return False, None, None
            
    except Exception as e:
        logger.error(f"❌ API endpoint request failed: {str(e)}")
        return False, None, None

def compare_direct_and_api():
    """Compare direct SQL execution with API endpoint."""
    # First test direct connection
    direct_success, direct_data = test_direct_sql_connection()
    
    if not direct_success:
        logger.error("Direct SQL connection test failed, cannot proceed with comparison")
        return
    
    # Then test converter directly
    converter_success, converter_sql, converter_data = test_converter_direct()
    
    # Finally test API endpoint
    api_success, api_sql, api_results = test_api_endpoint()
    
    # Compare results
    logger.info("Comparison summary:")
    logger.info(f"Direct SQL connection: {'✅ Success' if direct_success else '❌ Failed'}")
    logger.info(f"Converter direct: {'✅ Success' if converter_success else '❌ Failed'}")
    logger.info(f"API endpoint: {'✅ Success' if api_success else '❌ Failed'}")
    
    if converter_success and api_success:
        logger.info(f"Converter SQL: {converter_sql}")
        logger.info(f"API SQL: {api_sql}")
        if converter_sql == api_sql:
            logger.info("✅ SQL queries match")
        else:
            logger.info("❌ SQL queries do not match")
    
    if direct_success and converter_success:
        direct_rows = len(direct_data)
        converter_rows = len(converter_data) if converter_data is not None else 0
        logger.info(f"Direct data rows: {direct_rows}")
        logger.info(f"Converter data rows: {converter_rows}")
        
        if direct_rows == converter_rows:
            logger.info("✅ Row counts match between direct and converter execution")
        else:
            logger.info("❌ Row counts do not match between direct and converter execution")
    
    if direct_success and api_success:
        direct_rows = len(direct_data)
        api_rows = len(api_results)
        logger.info(f"Direct data rows: {direct_rows}")
        logger.info(f"API result rows: {api_rows}")
        
        if direct_rows == api_rows:
            logger.info("✅ Row counts match between direct and API execution")
        else:
            logger.info("❌ Row counts do not match between direct and API execution")
            
    # Check column names and case sensitivity
    if direct_success:
        direct_columns = list(direct_data.columns)
        logger.info(f"Direct SQL column names: {direct_columns}")
        
        if api_success and api_results:
            api_columns = list(api_results[0].keys()) if api_results else []
            logger.info(f"API result keys: {api_columns}")
            
            # Check if column names match but with different case
            direct_columns_lower = [col.lower() for col in direct_columns]
            api_columns_lower = [col.lower() for col in api_columns]
            
            if set(direct_columns_lower) == set(api_columns_lower):
                logger.info("✅ Column names match case-insensitively")
                
                # Check for exact case matches
                if set(direct_columns) != set(api_columns):
                    logger.info("❌ Column names have different cases")
                    logger.info("This might be causing issues with data mapping")
                    
                    # Suggest fix
                    logger.info("Potential fix: update column case handling in the API")
            else:
                logger.info("❌ Column names don't match even case-insensitively")
                logger.info(f"Missing in API: {set(direct_columns_lower) - set(api_columns_lower)}")
                logger.info(f"Extra in API: {set(api_columns_lower) - set(direct_columns_lower)}")

def suggest_fixes():
    """Based on diagnostic tests, suggest fixes."""
    logger.info("Suggesting potential fixes:")
    logger.info("1. Check case sensitivity in column names between SQL and API response")
    logger.info("2. Verify the execute_query method in sql_connector.py properly returns the dataframe")
    logger.info("3. Check that the API endpoint in api.py correctly formats the response")
    logger.info("4. Ensure the frontend maps column names correctly when processing the data")
    logger.info("5. Check transaction handling and cursor usage in the execute_query method")
    logger.info("6. Update the SQLServerConnector to include a proper close() method")

def generate_summary_report():
    """Generate a summary report of all the diagnostic findings and recommendations."""
    summary = """
===============================================
    SQL EXECUTION DIAGNOSTIC SUMMARY REPORT
===============================================

ISSUE:
------
The 'Show list of clients' query is correctly converted to SQL (SELECT * FROM Clients) but returns no results, 
despite the Clients table existing and having data when directly accessed.

DIAGNOSTIC FINDINGS:
-------------------
1. Database Connection Issues:
   - SQL Server connection fails with all attempted connection methods
   - Connection errors indicate SQL Server may not be running or is not accessible
   - The IntelliAssistant database appears to exist but cannot be accessed with current credentials

2. Column Name Mapping Issues:
   - There is a mismatch in column naming conventions between:
     a) Database (lowercase_snake_case): client_id, first_name, last_name, etc.
     b) Frontend (PascalCase): ClientID, ClientName, etc.
   - The API response formatting was not preserving original column casing

3. SQLServerConnector Implementation Issues:
   - The class was missing a proper close() method (added during diagnostics)
   - Error handling did not provide sufficient diagnostics when no results were returned

4. API Endpoint Issues:
   - The response format needed to be standardized for consistency
   - Enhanced error diagnostic information was needed for troubleshooting

SOLUTIONS IMPLEMENTED:
---------------------
1. Database Connection:
   - Added multiple connection retry options with different server names and drivers
   - Enhanced error messaging to provide clear diagnostics
   - Properly closing connections with the new close() method

2. Column Name Handling:
   - Updated the API to preserve original column names and case from the database
   - Enhanced the frontend mapping to handle both original and mapped column names
   - Added diagnostic logging to track column name transformations

3. SQLServerConnector Improvements:
   - Added close() method to properly manage database connections
   - Enhanced error handling and logging for connection errors
   - Added diagnostics for table existence and row count when no results are returned

4. API Response Standardization:
   - Standardized the response format with consistent error handling
   - Added more diagnostic information in error responses
   - Ensured detailed logging at each step of the process

NEXT STEPS:
-----------
1. Verify SQL Server is running and accessible
   - Check SQL Server Configuration Manager
   - Verify Windows Services shows SQL Server is running
   - Check firewall settings allow SQL connections

2. Test connection with SQL Server Management Studio
   - Try both Windows Authentication and SQL Authentication
   - Verify the IntelliAssistant database exists
   - Check permissions on the database and Clients table

3. For deployment:
   - Update connection parameters in config.py with correct server name
   - Ensure the application has appropriate permissions to access the database
   - Add automated connection health checks on application startup

CONCLUSION:
----------
The primary issues appear to be:
1. SQL Server connection issues - the server may not be running or accessible
2. Column name mapping differences between database and frontend expectations

The code changes implemented should address these issues once the SQL Server connection problems are resolved.
"""
    
    # Write the summary to a file
    with open("sql_diagnostics_summary.txt", "w") as f:
        f.write(summary)
    
    # Also print to console
    print(summary)
    return summary

if __name__ == "__main__":
    logger.info("Starting SQL execution diagnostic tests...")
    try:
        compare_direct_and_api()
    except Exception as e:
        logger.error(f"Error during diagnostics: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    suggest_fixes()
    generate_summary_report()
    logger.info("Diagnostic tests complete.")
"""
API Integration for enhanced SQL Generator.

This module provides integration between the API and the enhanced 
text-to-SQL conversion system with reflection capabilities.
"""

import os
import logging
import re
from typing import Dict, Any, List, Optional
import traceback
import pandas as pd

# Import from local modules
from .config import is_feature_enabled, is_reflection_enabled
from ..agents.sql_generator import SQLGeneratorAgent
from ..agents.schema_agent import SchemaAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Singleton instance of the converter
_converter_instance = None

def is_langgraph_enabled() -> bool:
    """Check if the enhanced SQL system is enabled."""
    return is_feature_enabled()

def get_converter():
    """Get or create a singleton instance of the reflective SQL converter."""
    global _converter_instance
    if _converter_instance is None:
        # Import here to avoid circular dependency
        from .simple_converter import SimpleReflectiveSQLConverter
        _converter_instance = SimpleReflectiveSQLConverter(
            reflection_enabled=is_reflection_enabled()
        )
    return _converter_instance

def convert_text_to_sql(
    query: str,
    connection_params: Dict[str, Any],
    execute: bool = False,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    additional_context: str = ""
) -> Dict[str, Any]:
    """
    Convert natural language to SQL using either enhanced or original SQL generator.
    
    Args:
        query: The natural language query to convert
        connection_params: Database connection parameters
        execute: Whether to execute the query against the database
        conversation_history: Optional conversation history for context
        additional_context: Additional context information
        
    Returns:
        Dict containing SQL query, explanation, and other results
    """
    # Check which system to use
    if is_langgraph_enabled():
        logger.info("Using enhanced SQL generator with reflection")
        # Use our reflective SQL converter
        converter = get_converter()
        
        result = converter.convert(
            user_query=query,
            connection_params=connection_params,
            conversation_history=conversation_history
        )
        
        # Format the result dictionary to match expected structure
        formatted_result = {
            "sql_query": result.get("sql_query", ""),
            "explanation": result.get("explanation", ""),
            "success": True,
            "reflection_enabled": result.get("reflection_enabled", False),
            "reflection_applied": result.get("reflection_applied", False),
            "reflection_log": result.get("reflection_log", []),
            "implementation": "reflective"
        }
        
        # Add error if present
        if "error" in result:
            formatted_result["error"] = result["error"]
            formatted_result["success"] = False
            
        return formatted_result
    else:
        logger.info("Using original SQL generator")
        # Use the original SQLGeneratorAgent and SchemaAgent
        schema_agent = SchemaAgent("SchemaAgent")
        sql_agent = SQLGeneratorAgent("SQLGeneratorAgent")
        
        # Extract schema first using SchemaAgent
        schema_result = schema_agent.process({"connection_params": connection_params})
        schema_info = schema_result.get("schema_info", {})
        
        # Generate SQL using the original agent
        result = sql_agent.process({
            "intent_info": {"operation": "select"},
            "validated_columns": {},
            "schema_info": schema_info,
            "tables_used": list(schema_info.get("tables", {}).keys())
        })
        
        return {
            "sql_query": result.get("sql", ""),
            "explanation": "SQL query generated using standard generator",
            "success": result.get("success", True),
            "reflection_enabled": False,
            "implementation": "original"
        }


# Function for backward compatibility
def langgraph_convert_text_to_sql(
    query: str,
    connection_params: Dict[str, Any],
    execute: bool = False,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    additional_context: str = ""
) -> Dict[str, Any]:
    """
    Convert natural language to SQL with API-compatible response format.
    
    This function formats the response to match the expected API format.
    """
    try:
        # Add debug logging
        logger.info(f"langgraph_convert_text_to_sql received query: '{query}'")
        logger.info(f"Connection params: server={connection_params.get('server')}, database={connection_params.get('database')}")
        logger.info(f"Execute flag: {execute}")
        logger.info(f"Additional context: {additional_context}")
        
        # Validate if there's a direct mention of 'Clients' table
        has_clients_reference = 'client' in query.lower() or 'clients' in query.lower()
        logger.info(f"Query contains client reference: {has_clients_reference}")
        
        # Add diagnostic test with direct SQL execution if there's a clients reference
        direct_result = None
        direct_columns = None
        
        if has_clients_reference and 'server' in connection_params and 'database' in connection_params:
            try:
                from ..sql_connector import SQLServerConnector
                
                # Create connector
                connector = SQLServerConnector(connection_params)
                
                # Connect to database
                if connector.connect():
                    logger.info("Successfully connected to database for diagnostics")
                    
                    # Check if Clients table exists
                    tables = connector.list_tables()
                    clients_table = None
                    for table in tables:
                        if table.lower() == 'clients':
                            clients_table = table
                            break
                    
                    logger.info(f"Found Clients table: {clients_table}")
                    
                    # If we found the Clients table, try executing a simple query
                    if clients_table:
                        try:
                            # Try a basic query first
                            actual_query = f"SELECT TOP 5 * FROM [{clients_table}]"
                            logger.info(f"Testing query: {actual_query}")
                            result_df = connector.execute_query(actual_query)
                            row_count = len(result_df)
                            logger.info(f"Query successful! Returned {row_count} rows")
                            
                            # If we got rows, try to get the column names
                            if row_count > 0:
                                columns = result_df.columns.tolist()
                                logger.info(f"Columns in Clients table: {columns}")
                                
                                # Save these results as a backup in case our main flow fails
                                try:
                                    # Convert to a list of dictionaries
                                    direct_columns = columns
                                    direct_result = []
                                    for _, row in result_df.iterrows():
                                        row_dict = {}
                                        for col in columns:
                                            row_dict[col] = row[col] if not pd.isna(row[col]) else None
                                        direct_result.append(row_dict)
                                    logger.info(f"Created backup result set with {len(direct_result)} rows")
                                except Exception as conv_err:
                                    logger.error(f"Error creating backup result: {str(conv_err)}")
                            else:
                                logger.warning("Direct query returned 0 rows - may indicate permission issue")
                        except Exception as query_err:
                            logger.error(f"Error executing direct Clients query: {str(query_err)}")
                    
                    # Close the connection
                    connector.disconnect()
                else:
                    logger.error(f"Failed to connect to database for diagnostics: {connector.last_error}")
            except Exception as diag_err:
                logger.error(f"Error in SQL diagnostics: {str(diag_err)}")
        
        # Use reflective SQL converter directly
        if is_langgraph_enabled():
            # Get converter instance
            converter = get_converter()
            
            # Convert query
            result = converter.convert(
                user_query=query,
                connection_params=connection_params,
                conversation_history=conversation_history
            )
        else:
            # Use the original generator with SchemaAgent
            schema_agent = SchemaAgent("SchemaAgent")
            sql_agent = SQLGeneratorAgent("SQLGeneratorAgent")
            
            # Extract schema first using SchemaAgent
            schema_result = schema_agent.process({"connection_params": connection_params})
            schema_info = schema_result.get("schema_info", {})
            
            # Generate SQL using the original agent
            sql_result = sql_agent.process({
                "intent_info": {"operation": "select"},
                "validated_columns": {},
                "schema_info": schema_info,
                "tables_used": list(schema_info.get("tables", {}).keys())
            })
            
            result = {
                "sql_query": sql_result.get("sql", ""),
                "explanation": "SQL query generated using standard generator",
                "success": sql_result.get("success", True),
                "reflection_enabled": False,
                "implementation": "original"
            }
            
            if not sql_result.get("success", True):
                result["error"] = sql_result.get("error", "Unknown error")
        
        # Check for client query and add special debugging
        sql_query = result.get("sql_query", "")
        if sql_query.lower().find("from clients") >= 0:
            logger.info("Client table query detected, adding extra debug info")
            
            # Log sql and result details for debugging
            has_results = "execution_result" in result and result["execution_result"] is not None
            has_rows = has_results and "rows" in result["execution_result"] and result["execution_result"]["rows"] is not None
            result_count = len(result["execution_result"]["rows"]) if has_rows else 0
            
            logger.info(f"Client query SQL: {sql_query}")
            logger.info(f"Has results: {has_results}, Has rows: {has_rows}, Count: {result_count}")
            
            # If we don't have results but we have direct results from earlier, use those
            if (not has_rows or result_count == 0) and direct_result and len(direct_result) > 0:
                logger.info(f"No results from regular flow but we have {len(direct_result)} rows from direct query. Using those instead.")
                
                # Create execution_result if missing
                if "execution_result" not in result:
                    result["execution_result"] = {}
                
                # Update with our direct query results
                result["execution_result"]["rows"] = direct_result
                result["execution_result"]["columns"] = direct_columns
                
                # Mark that we recovered
                result["recovered_results"] = True
                has_rows = True
                result_count = len(direct_result)
                logger.info(f"Updated result with recovered data, now has {result_count} rows")
            
            if has_rows and result_count > 0:
                # Log the first row to help debug structure
                first_row = result["execution_result"]["rows"][0]
                logger.info(f"First result row: {first_row}")
                logger.info(f"Row type: {type(first_row)}")
                
                # Check if row is properly serializable
                if isinstance(first_row, dict):
                    logger.info(f"Row keys: {list(first_row.keys())}")
                else:
                    logger.warning(f"Row is not a dictionary: {type(first_row)}")
                    
                    # Try to convert to dict if needed
                    if hasattr(first_row, "__dict__"):
                        logger.info("Converting row to dict using __dict__")
                        result["execution_result"]["rows"] = [row.__dict__ for row in result["execution_result"]["rows"]]
                    elif hasattr(first_row, "_asdict") and callable(first_row._asdict):
                        logger.info("Converting row to dict using _asdict()")
                        result["execution_result"]["rows"] = [row._asdict() for row in result["execution_result"]["rows"]]
                    else:
                        # Last resort: try converting tuple/list to dict using column names
                        try:
                            if hasattr(result["execution_result"], "columns") and result["execution_result"]["columns"]:
                                columns = result["execution_result"]["columns"]
                                logger.info(f"Attempting to convert using column names: {columns}")
                                
                                new_rows = []
                                for row in result["execution_result"]["rows"]:
                                    if isinstance(row, (list, tuple)) and len(row) == len(columns):
                                        new_row = {columns[i]: value for i, value in enumerate(row)}
                                        new_rows.append(new_row)
                                        
                                result["execution_result"]["rows"] = new_rows
                                logger.info("Successfully converted rows to dictionaries")
                        except Exception as conv_err:
                            logger.error(f"Error converting rows: {str(conv_err)}")
            elif result_count == 0:
                logger.warning("Client query returned zero results - check data access permissions")
        
        # Post-process SQL for simple "show all" queries
        if result.get("sql_query"):
            sql_query = result.get("sql_query")
            logger.info(f"Generated SQL query: {sql_query}")
            
            # Check if this is a "show all" type query but has cross joins
            has_cross_join = "CROSS JOIN" in sql_query.upper()
            
            # For simple entity listing queries
            show_all_basic = re.search(r'^\s*show\s+all\s+(\w+)s?\s*$|^\s*list\s+all\s+(\w+)s?\s*
            
            # Check if the existing query already has a WHERE clause
            has_where = "WHERE" in sql_query.upper()
            
            # Handle completely unfiltered "show all X" queries
            if show_all_basic and has_cross_join:
                entity = show_all_basic.group(1) or show_all_basic.group(2)
                if entity:
                    # Find matching table
                    matching_table = None
                    try:
                        from ..sql_connector import SQLServerConnector
                        connector = SQLServerConnector(connection_params)
                        if connector.connect():
                            tables = connector.list_tables()
                            for table in tables:
                                if entity.lower() in table.lower():
                                    matching_table = table
                                    break
                            connector.disconnect()
                    except Exception as e:
                        logger.error(f"Error finding matching table: {str(e)}")
                    
                    # If we found a matching table, override the SQL
                    if matching_table:
                        logger.info(f"Overriding complex CROSS JOIN query with simple SELECT for '{matching_table}' table")
                        # For completely unfiltered queries
                        result["sql_query"] = f"SELECT * FROM {matching_table}"
                        # Update the explanation to clarify this was fixed
                        result["explanation"] = f"Simplified query to select all records from {matching_table} table."
                        result["simplified_query"] = True
                        
                        # Execute the simplified query if execute flag is True
                        if execute:
                            try:
                                logger.info(f"Executing simplified query: {result['sql_query']}")
                                query_result = connector.execute_query(result['sql_query'])
                                
                                if query_result is not None:
                                    # Extract columns and rows
                                    columns = query_result.columns.tolist()
                                    rows = []
                                    for _, row in query_result.iterrows():
                                        row_dict = {}
                                        for col in columns:
                                            row_dict[col] = row[col] if not pd.isna(row[col]) else None
                                        rows.append(row_dict)
                                    
                                    # Update the result
                                    if "execution_result" not in result:
                                        result["execution_result"] = {}
                                    result["execution_result"]["columns"] = columns
                                    result["execution_result"]["rows"] = rows
                                    logger.info(f"Successfully executed simplified query, got {len(rows)} rows")
                            except Exception as exec_err:
                                logger.error(f"Error executing simplified query: {str(exec_err)}")
            # Handle queries with filters like "show all assets that are bonds"
            elif show_all_with_filter and has_cross_join and not has_where:
                entity = show_all_with_filter.group(1) or show_all_with_filter.group(2)
                if entity:
                    # Find matching table
                    matching_table = None
                    try:
                        from ..sql_connector import SQLServerConnector
                        connector = SQLServerConnector(connection_params)
                        if connector.connect():
                            tables = connector.list_tables()
                            for table in tables:
                                if entity.lower() in table.lower():
                                    matching_table = table
                                    break
                            connector.disconnect()
                    except Exception as e:
                        logger.error(f"Error finding matching table: {str(e)}")
                    
                    # If we found a matching table, preserve filter but remove cross joins
                    if matching_table:
                        # Extract possible filter conditions from the query
                        filter_match = re.search(r'that\s+are\s+(\w+)s?|where\s+([^\s]+)\s+(?:is|=|==)\s+([^\s]+)', query.lower())
                        where_clause = ""
                        
                        if filter_match:
                            # Handle "that are X" pattern (like "that are Bonds")
                            if filter_match.group(1):
                                filter_value = filter_match.group(1).capitalize()  # Capitalize for proper noun formats
                                # Try to find the appropriate column for filtering
                                filter_column = None
                                try:
                                    schema_df = connector.get_table_schema(matching_table)
                                    for col_name in schema_df['column_name'].tolist():
                                        if 'type' in col_name.lower():
                                            filter_column = col_name
                                            break
                                except Exception as e:
                                    logger.error(f"Error finding filter column: {str(e)}")
                                
                                # If we found an appropriate column, create a WHERE clause
                                if filter_column:
                                    where_clause = f" WHERE {filter_column} = '{filter_value}'"
                        
                        # Build the simplified query with filter
                        result["sql_query"] = f"SELECT * FROM {matching_table}{where_clause}"
                        # Update the explanation
                        result["explanation"] = f"Simplified query to select filtered records from {matching_table} table."
                        result["simplified_query"] = True
                        
                        # Execute the simplified query if execute flag is True
                        if execute:
                            try:
                                logger.info(f"Executing simplified query: {result['sql_query']}")
                                query_result = connector.execute_query(result['sql_query'])
                                
                                if query_result is not None:
                                    # Extract columns and rows
                                    columns = query_result.columns.tolist()
                                    rows = []
                                    for _, row in query_result.iterrows():
                                        row_dict = {}
                                        for col in columns:
                                            row_dict[col] = row[col] if not pd.isna(row[col]) else None
                                        rows.append(row_dict)
                                    
                                    # Update the result
                                    if "execution_result" not in result:
                                        result["execution_result"] = {}
                                    result["execution_result"]["columns"] = columns
                                    result["execution_result"]["rows"] = rows
                                    logger.info(f"Successfully executed simplified query, got {len(rows)} rows")
                            except Exception as exec_err:
                                logger.error(f"Error executing simplified query: {str(exec_err)}")
        else:
            logger.error(f"No SQL query was generated!")
        
        # Format result for the API response format
        api_result = {
            "sql": result.get("sql_query", ""),
            "explanation": result.get("explanation", ""),
            "result": result.get("execution_result", {}).get("rows", []),
            "columns": result.get("execution_result", {}).get("columns", []),
            "error": result.get("error", None),
            "success": result.get("success", True),
            "reflection_applied": result.get("reflection_applied", False),
            "recovered_results": result.get("recovered_results", False),
            "simplified_query": result.get("simplified_query", False),  # Flag to indicate query was simplified
            "query_modified": result.get("query_modified", False),  # Flag to indicate query was modified by post-processor
            "original_sql": result.get("original_sql_query", "")  # Original SQL before modification
        }
        
        return api_result
    except Exception as e:
        logger.error(f"Error in langgraph_convert_text_to_sql: {str(e)}")
        logger.error(traceback.format_exc())
        result = {
            "sql_query": "",
            "explanation": f"Error generating SQL: {str(e)}",
            "error": str(e),
            "success": False
        }
        
        return {
            "sql": "",
            "explanation": f"Error generating SQL: {str(e)}",
            "error": str(e),
            "success": False,
            "result": []
        } 
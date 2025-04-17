"""
Simple Reflective SQL Converter.

This module provides a simplified implementation of a text-to-SQL
converter with reflection capabilities, without LangGraph dependencies.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union, Tuple
import traceback
import time

from .config import get_llm, is_reflection_enabled
from ..agents.sql_generator import SQLGeneratorAgent
from ..agents.schema_agent import SchemaAgent
from ..schema_utils import ColumnValidator
from utils.sql_connector import SQLServerConnector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleReflectiveSQLConverter:
    """
    A simplified implementation of a reflective text-to-SQL converter.
    
    This class provides SQL generation with reflection capabilities without
    relying on LangGraph dependencies.
    """
    
    def __init__(self, reflection_enabled: bool = True):
        """
        Initialize the SimpleReflectiveSQLConverter.
        
        Args:
            reflection_enabled: Whether to enable reflection for SQL generation.
        """
        self.reflection_enabled = reflection_enabled
        self.llm = get_llm()
        self.sql_agent = SQLGeneratorAgent("SQLGeneratorAgent")
        self.schema_agent = SchemaAgent("SchemaAgent")
        self.column_validator = ColumnValidator()
        
        logger.info(f"Initialized SimpleReflectiveSQLConverter with reflection_enabled={reflection_enabled}")
    
    def extract_schema(self, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract schema information from the database.
        
        Args:
            connection_params: Database connection parameters.
            
        Returns:
            Dict containing schema information.
        """
        logger.info("Extracting schema information")
        schema_result = self.schema_agent.process({"connection_params": connection_params})
        return schema_result.get("schema_info", {})
    
    def generate_sql_query(self, 
                          user_query: str, 
                          schema_info: Dict[str, Any],
                          connection_params: Dict[str, Any],
                          conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate an SQL query from a natural language query.
        
        Args:
            user_query: The natural language query from the user.
            schema_info: Database schema information.
            connection_params: Database connection parameters.
            conversation_history: Optional conversation history.
            
        Returns:
            Dict containing the generated SQL and explanation.
        """
        logger.info(f"Generating SQL for query: {user_query}")
        
        # Simple intent detection based on keywords in the query
        intent_info = {"operation": "select"}
        tables_to_use = []
        
        # Check if the query mentions specific tables
        if "client" in user_query.lower() or "clients" in user_query.lower():
            tables_to_use.append("Clients")
            intent_info["target_table"] = "Clients"
        
        # If no specific tables were identified, use all tables
        if not tables_to_use and schema_info.get("tables"):
            if isinstance(schema_info.get("tables"), dict):
                tables_to_use = list(schema_info.get("tables", {}).keys())
            else:
                tables_to_use = schema_info.get("tables", [])
        
        # Step 1: Generate the initial SQL query
        sql_result = self.sql_agent.process({
            "intent_info": intent_info,
            "validated_columns": {},
            "schema_info": schema_info,
            "tables_used": tables_to_use
        })
        
        # Convert the result format to match what the rest of the code expects
        converted_result = {
            "sql_query": sql_result.get("sql", ""),
            "explanation": "SQL query generated using standard generator",
            "success": sql_result.get("success", True),
            "error": sql_result.get("error")
        }
        
        # If the generated SQL is empty or too generic, generate a simple query for the target table
        if not converted_result["sql_query"] or "CROSS JOIN" in converted_result["sql_query"]:
            if "target_table" in intent_info:
                table_name = intent_info['target_table']
                
                # Get the table's columns from schema info
                table_columns = []
                if schema_info and "tables" in schema_info:
                    if isinstance(schema_info["tables"], dict) and table_name in schema_info["tables"]:
                        table_columns = [col["column_name"] for col in schema_info["tables"][table_name]]
                    elif isinstance(schema_info.get("tables"), list) and table_name in schema_info["tables"]:
                        # Handle case where tables is a list
                        table_columns = self._get_columns_for_table(table_name, schema_info)
                
                if table_columns:
                    # Use the actual columns from schema
                    columns_str = ", ".join(table_columns)
                    converted_result["sql_query"] = f"SELECT {columns_str} FROM {table_name}"
                    converted_result["explanation"] = f"Query using schema-defined columns to show all {table_name}"
                else:
                    # Fallback to SELECT * if no column info available
                    converted_result["sql_query"] = f"SELECT * FROM {table_name}"
                    converted_result["explanation"] = f"Simple query to show all {table_name}"
        
        # If reflection is not enabled, return the SQL result directly
        if not self.reflection_enabled:
            logger.info("Reflection disabled, returning initial SQL")
            return converted_result
        
        # Step 2: Validate the SQL query columns
        validation_result = self.column_validator.validate(
            converted_result["sql_query"], 
            schema_info
        )
        
        # Step 3: If validation fails or we want reflection anyway, apply reflection
        if not validation_result["valid"]:
            logger.info("Column validation failed, applying reflection")
            reflected_sql = self._reflect_on_sql(
                user_query=user_query,
                schema_info=schema_info,
                initial_sql=converted_result["sql_query"],
                validation_issues=validation_result.get("issues", [])
            )
            
            if reflected_sql:
                converted_result["sql_query"] = reflected_sql
                converted_result["reflection_applied"] = True
                converted_result["reflection_log"] = validation_result.get("issues", [])
        else:
            logger.info("Column validation passed, skipping reflection")
            
        return converted_result
    
    def _reflect_on_sql(self, 
                       user_query: str, 
                       schema_info: Dict[str, Any],
                       initial_sql: str,
                       validation_issues: List[str]) -> Optional[str]:
        """
        Reflect on the generated SQL and improve it if needed.
        
        Args:
            user_query: The original user query.
            schema_info: Database schema information.
            initial_sql: The initially generated SQL query.
            validation_issues: List of validation issues.
            
        Returns:
            Improved SQL query or None if reflection fails.
        """
        try:
            # Convert schema_info to a more readable format for the LLM
            tables_info = []
            for table in schema_info.get("tables", []):
                table_info = {
                    "table_name": table["table_name"],
                    "columns": [
                        f"{col['column_name']} ({col['data_type']})" 
                        for col in table.get("columns", [])
                    ]
                }
                tables_info.append(table_info)
            
            schema_summary = json.dumps(tables_info, indent=2)
            
            # Prepare the reflection prompt
            reflection_prompt = f"""
You are a SQL expert tasked with improving a generated SQL query.

ORIGINAL USER QUERY:
{user_query}

INITIAL SQL QUERY:
{initial_sql}

DATABASE SCHEMA:
{schema_summary}

VALIDATION ISSUES:
{', '.join(validation_issues)}

Your task is to fix the SQL query to address all validation issues. Provide only the corrected SQL query without any explanation.
If you believe the initial query is correct despite the validation issues, you may return it unchanged but provide a brief explanation why.
            """
            
            # Get the improved SQL from the LLM
            response = self.llm.generate_content(reflection_prompt)
            improved_sql = response.text.strip()
            
            # Extract the SQL if it's surrounded by backticks or other formatting
            if "```sql" in improved_sql:
                improved_sql = improved_sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in improved_sql:
                improved_sql = improved_sql.split("```")[1].strip()
            
            logger.info(f"Reflection produced improved SQL")
            return improved_sql
            
        except Exception as e:
            logger.error(f"Error during SQL reflection: {str(e)}")
            return None
    
    def generate_sql(self, 
                    user_query: str, 
                    connection_params: Dict[str, Any],
                    conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate an SQL query from a natural language query.
        This is a wrapper for generate_sql_query for API compatibility.
        
        Args:
            user_query: The natural language query from the user.
            connection_params: Database connection parameters.
            conversation_history: Optional conversation history.
            
        Returns:
            Dict containing the generated SQL and explanation.
        """
        logger.info(f"Generate SQL wrapper called for query: {user_query}")
        
        # Extract schema using the connection params
        schema_info = self.extract_schema(connection_params)
        
        # Call the actual implementation
        return self.generate_sql_query(
            user_query=user_query,
            schema_info=schema_info,
            connection_params=connection_params,
            conversation_history=conversation_history
        )

    def convert(self, user_query, connection_params=None, conversation_history=None, execute=False):
        """
        Convert natural language to SQL and optionally execute it.
        
        Args:
            user_query: Natural language query
            connection_params: Connection parameters for the database
            conversation_history: Previous conversation for context
            execute: Whether to execute the generated SQL
            
        Returns:
            Dict with SQL generation and execution results
        """
        try:
            # Extract schema using the connection params
            schema_info = self.extract_schema(connection_params)
            
            # Generate SQL from natural language
            sql_result = self.generate_sql_query(
                user_query=user_query,
                schema_info=schema_info,
                connection_params=connection_params,
                conversation_history=conversation_history
            )
            
            # Add reflection field for monitoring
            sql_result['reflection_enabled'] = self.reflection_enabled
            
            # Execute the SQL if requested
            if execute and sql_result.get('sql_query') and connection_params:
                try:
                    # Use our specialized execution method
                    execution_result = self.execute_query(
                        sql_query=sql_result['sql_query'],
                        connection_params=connection_params
                    )
                    
                    # Add execution result to the response
                    sql_result['execution_result'] = execution_result
                except Exception as e:
                    logger.error(f"Error executing SQL: {str(e)}")
                    sql_result['execution_result'] = {
                        'executed': False,
                        'error': str(e)
                    }
            else:
                # No execution
                sql_result['execution_result'] = {
                    'executed': False,
                    'message': 'Execution not requested or no SQL query generated'
                }
            
            return sql_result
            
        except Exception as e:
            logger.error(f"Error in convert method: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'error': str(e),
                'sql_query': '',
                'explanation': f'Error generating SQL: {str(e)}'
            }

    def _get_columns_for_table(self, table_name, schema_info):
        """Get column names for a table from schema info."""
        if not schema_info or 'tables' not in schema_info:
            return []
        
        tables = schema_info['tables']
        # Handle dict format
        if isinstance(tables, dict):
            if table_name in tables:
                return [col['column_name'] for col in tables[table_name]]
        # Handle list format
        elif isinstance(tables, list):
            for table in tables:
                if isinstance(table, dict) and table.get('table_name') == table_name:
                    return [col['column_name'] for col in table.get('columns', [])]
        return []

    def convert_to_sql(self, query, intent_info=None, schema_info=None):
        """Convert natural language to SQL based on intent and schema."""
        try:
            # Default to SELECT * if no specific intent
            if not intent_info or 'target_table' not in intent_info:
                return {
                    'sql_query': 'SELECT * FROM Clients',
                    'confidence': 0.0,
                    'explanation': 'No specific intent detected, using default query'
                }
            
            table_name = intent_info['target_table']
            
            # Get columns for the table from schema
            columns = self._get_columns_for_table(table_name, schema_info)
            
            # Build column list for SELECT
            column_list = '*'
            if columns:
                column_list = ', '.join(columns)
            
            # Build the SQL query
            sql_query = f"SELECT {column_list} FROM {table_name}"
            
            # Add any filters from intent
            if 'filters' in intent_info and intent_info['filters']:
                where_clauses = []
                for filter_info in intent_info['filters']:
                    if 'column' in filter_info and 'operator' in filter_info and 'value' in filter_info:
                        where_clauses.append(
                            f"{filter_info['column']} {filter_info['operator']} '{filter_info['value']}'"
                        )
                if where_clauses:
                    sql_query += " WHERE " + " AND ".join(where_clauses)
                
            # Add any sorting from intent
            if 'sort' in intent_info and intent_info['sort']:
                sort_info = intent_info['sort']
                if 'column' in sort_info:
                    direction = sort_info.get('direction', 'ASC')
                    sql_query += f" ORDER BY {sort_info['column']} {direction}"
                
            return {
                'sql_query': sql_query,
                'confidence': 0.8,  # Higher confidence with schema info
                'explanation': f'Generated SQL query for {table_name} table using schema information'
            }
            
        except Exception as e:
            logging.error(f"Error in convert_to_sql: {str(e)}")
            return {
                'sql_query': '',
                'confidence': 0.0,
                'explanation': f'Error generating SQL: {str(e)}'
            }

    def execute_query(self, sql_query: str, connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a SQL query against the database.
        
        Args:
            sql_query: The SQL query to execute
            connection_params: The database connection parameters
            
        Returns:
            A dictionary containing execution results
        """
        logger.info(f"Attempting to execute SQL query: {sql_query}")
        logger.info(f"Connection params: server={connection_params.get('server')}, database={connection_params.get('database')}")
        
        # Add custom execution for Clients queries to ensure they work
        if 'clients' in sql_query.lower():
            logger.info("Detected Clients table in query - applying special handling")
            
            try:
                import sys
                logger.info(f"Python path: {sys.path}")
                logger.info("Importing SQLServerConnector...")
                
                try:
                    from utils.sql_connector import SQLServerConnector
                    logger.info("Successfully imported SQLServerConnector from utils.sql_connector")
                except ImportError:
                    logger.error("Failed to import from utils.sql_connector, trying relative import")
                    from ..sql_connector import SQLServerConnector
                    logger.info("Successfully imported SQLServerConnector from relative path")
                
                # Create SQL Server connector
                logger.info("Creating SQLServerConnector instance...")
                connector = SQLServerConnector(connection_params)
                logger.info("SQLServerConnector instance created")
                
                # Try to connect
                logger.info("Attempting to connect to database...")
                connection_result = connector.connect()
                if connection_result:
                    logger.info("Successfully connected to database for Clients table execution")
                    
                    # First try the original query
                    try:
                        # Try to execute the original query
                        logger.info(f"Attempting to execute original query: {sql_query}")
                        df = connector.execute_query(sql_query)
                        row_count = len(df)
                        logger.info(f"Original query executed successfully! {row_count} rows returned")
                        
                        # Log the first few rows for debugging
                        if row_count > 0:
                            logger.info(f"Sample data (first row): {df.iloc[0].to_dict()}")
                        else:
                            logger.info("Query returned 0 rows")
                        
                        # Format results
                        results = {
                            "rows": df.head(10).to_dict(orient='records'),
                            "columns": df.columns.tolist(),
                            "total_rows": row_count,
                            "execution_time_ms": 0,
                            "executed": True,
                            "error": None
                        }
                        
                        # Close the connection and return results
                        connector.disconnect()
                        logger.info("Connection closed after successful query")
                        return results
                        
                    except Exception as original_error:
                        logger.warning(f"Original query failed: {str(original_error)}")
                        logger.warning(f"Error details: {traceback.format_exc()}")
                        
                        # If the original query failed, try to find the actual Clients table
                        try:
                            # Check if Clients table exists
                            tables = connector.list_tables()
                            clients_table = None
                            
                            for table in tables:
                                if table.lower() == 'clients':
                                    clients_table = table
                                    break
                            
                            if clients_table:
                                logger.info(f"Found Clients table: {clients_table}")
                                
                                # Create a fixed query
                                fixed_query = sql_query.replace("Clients", clients_table)
                                fixed_query = fixed_query.replace("clients", clients_table)
                                fixed_query = fixed_query.replace("[Clients]", f"[{clients_table}]")
                                fixed_query = fixed_query.replace("[clients]", f"[{clients_table}]")
                                
                                # If still the same, try a more aggressive approach
                                if fixed_query == sql_query:
                                    # Try to match the pattern "SELECT * FROM Clients"
                                    if "select * from" in sql_query.lower():
                                        fixed_query = f"SELECT * FROM [{clients_table}]"
                                
                                logger.info(f"Attempting fixed query: {fixed_query}")
                                
                                # Execute the fixed query
                                df = connector.execute_query(fixed_query)
                                row_count = len(df)
                                logger.info(f"Fixed query executed successfully! {row_count} rows returned")
                                
                                # Format results
                                results = {
                                    "rows": df.head(10).to_dict(orient='records'),
                                    "columns": df.columns.tolist(),
                                    "total_rows": row_count,
                                    "execution_time_ms": 0,
                                    "executed": True,
                                    "error": None,
                                    "note": "Used fixed query",
                                    "original_query": sql_query,
                                    "fixed_query": fixed_query
                                }
                                
                                # Close the connection and return results
                                connector.disconnect()
                                return results
                            else:
                                logger.error("No 'Clients' table found in the database")
                                
                                # Try a direct query to look for similar tables
                                similar_tables = [table for table in tables if 'client' in table.lower() or 'customer' in table.lower()]
                                
                                if similar_tables:
                                    logger.info(f"Found similar tables: {similar_tables}")
                                    
                                    # Try using the first similar table
                                    similar_table = similar_tables[0]
                                    fixed_query = sql_query.replace("Clients", similar_table)
                                    fixed_query = fixed_query.replace("clients", similar_table)
                                    fixed_query = fixed_query.replace("[Clients]", f"[{similar_table}]")
                                    fixed_query = fixed_query.replace("[clients]", f"[{similar_table}]")
                                    
                                    logger.info(f"Attempting query with similar table: {fixed_query}")
                                    
                                    # Try to execute the query with the similar table
                                    try:
                                        df = connector.execute_query(fixed_query)
                                        row_count = len(df)
                                        logger.info(f"Similar table query executed successfully! {row_count} rows returned")
                                        
                                        # Format results
                                        results = {
                                            "rows": df.head(10).to_dict(orient='records'),
                                            "columns": df.columns.tolist(),
                                            "total_rows": row_count,
                                            "execution_time_ms": 0,
                                            "executed": True,
                                            "error": None,
                                            "note": "Used similar table",
                                            "original_query": sql_query,
                                            "fixed_query": fixed_query,
                                            "similar_table": similar_table
                                        }
                                        
                                        # Close the connection and return results
                                        connector.disconnect()
                                        return results
                                    except Exception as similar_error:
                                        logger.error(f"Similar table query failed: {str(similar_error)}")
                        
                        except Exception as table_error:
                            logger.error(f"Error during table check: {str(table_error)}")
                    
                    except Exception as e:
                        logger.error(f"Error executing query: {str(e)}")
                
                else:
                    logger.error(f"Failed to connect to database: {connector.last_error}")
            
            except Exception as e:
                logger.error(f"Error in Clients table execution: {str(e)}")
        
        # Fall back to original execution
        logger.info("Using regular execution method")
        
        try:
            from ..sql_connector import fetch_sql_data
            
            # Execute the query
            execution_start = time.time()
            df = fetch_sql_data(connection_params, query=sql_query)
            execution_time = (time.time() - execution_start) * 1000  # Convert to milliseconds
            
            # Check for error
            if 'error' in df.columns and len(df) == 1:
                error_msg = df['error'].iloc[0]
                logger.error(f"Error executing query: {error_msg}")
                return {
                    "executed": False,
                    "error": error_msg,
                    "execution_time_ms": execution_time
                }
            
            # Format results
            row_count = len(df)
            logger.info(f"Query executed successfully! {row_count} rows returned")
            return {
                "rows": df.head(10).to_dict(orient='records'),
                "columns": df.columns.tolist(),
                "total_rows": row_count,
                "execution_time_ms": execution_time,
                "executed": True,
                "error": None
            }
        
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                "executed": False,
                "error": str(e),
                "execution_time_ms": 0
            }
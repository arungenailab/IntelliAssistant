"""
Explanation Agent module for generating user-friendly explanations for SQL queries.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Set

from utils.agents.base_agent import BaseAgent
from utils.gemini_helper import get_gemini_response

# Configure logging
logger = logging.getLogger(__name__)

class ExplanationAgent(BaseAgent):
    """
    Agent responsible for generating user-friendly explanations
    for SQL queries and any modifications made during processing.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Explanation Agent.
        
        Args:
            name (str): Name of the agent
            config (Dict[str, Any], optional): Configuration for the agent
        """
        super().__init__(name, config)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data to generate an explanation for the SQL query.
        
        Args:
            input_data (Dict[str, Any]): Input data including the SQL query and context
            
        Returns:
            Dict[str, Any]: Results including the explanation
        """
        # Validate input
        if not self.validate_input(input_data, ["sql", "user_query"]):
            return {
                "success": False,
                "error": "Missing required SQL query or user query",
                "explanation": ""
            }
        
        sql_query = input_data["sql"]
        user_query = input_data["user_query"]
        validated_columns = input_data.get("validated_columns", {})
        unmapped_columns = input_data.get("unmapped_columns", [])
        schema_info = input_data.get("schema_info", {})
        intent_info = input_data.get("intent_info", {})
        
        try:
            # If there was an error in SQL generation, explain the error
            if not input_data.get("success", True) or not sql_query:
                error_msg = input_data.get("error", "Unknown error")
                explanation = self._generate_error_explanation(
                    error_msg, user_query, validated_columns, unmapped_columns
                )
            else:
                # Generate an explanation of the SQL query
                explanation = self._generate_query_explanation(
                    sql_query, user_query, validated_columns, schema_info, intent_info
                )
            
            # Add column mapping details if appropriate
            if validated_columns and len(validated_columns) > 0:
                column_mapping_explanation = self._generate_column_mapping_explanation(
                    validated_columns, unmapped_columns
                )
                explanation += "\n\n" + column_mapping_explanation
            
            # Store explanation in state
            self.update_state({"explanation": explanation})
            
            # Return success
            result = {
                "success": True,
                "explanation": explanation
            }
            
            self.log_result(result)
            return result
            
        except Exception as e:
            logger.exception(f"Error in ExplanationAgent: {str(e)}")
            return {
                "success": False,
                "error": f"Explanation generation error: {str(e)}",
                "explanation": "Unable to generate explanation due to an internal error."
            }
    
    def _generate_query_explanation(self, sql_query: str, user_query: str,
                                  validated_columns: Dict[str, Dict[str, Any]],
                                  schema_info: Dict[str, Any],
                                  intent_info: Dict[str, Any]) -> str:
        """
        Generate an explanation of the SQL query.
        
        Args:
            sql_query (str): SQL query to explain
            user_query (str): Original natural language query
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            schema_info (Dict[str, Any]): Schema information
            intent_info (Dict[str, Any]): Intent information
            
        Returns:
            str: Explanation of the SQL query
        """
        # For simple queries, use pattern-based explanation
        if self._is_simple_query(sql_query):
            return self._generate_pattern_explanation(sql_query, intent_info)
        
        # For complex queries, use LLM-based explanation
        return self._generate_llm_explanation(sql_query, user_query, validated_columns, schema_info)
    
    def _is_simple_query(self, sql_query: str) -> bool:
        """
        Check if a query is simple enough for pattern-based explanation.
        
        Args:
            sql_query (str): SQL query to check
            
        Returns:
            bool: True if the query is simple, False otherwise
        """
        sql_upper = sql_query.upper()
        
        # Simple SELECT query with no JOIN, GROUP BY, etc.
        if sql_upper.startswith("SELECT") and "JOIN" not in sql_upper and "GROUP BY" not in sql_upper:
            return True
        
        # Simple INSERT query
        if sql_upper.startswith("INSERT") and "SELECT" not in sql_upper:
            return True
        
        # Simple UPDATE query
        if sql_upper.startswith("UPDATE") and "JOIN" not in sql_upper:
            return True
        
        # Simple DELETE query
        if sql_upper.startswith("DELETE") and "JOIN" not in sql_upper:
            return True
        
        # Complex query
        return False
    
    def _generate_pattern_explanation(self, sql_query: str, intent_info: Dict[str, Any]) -> str:
        """
        Generate a pattern-based explanation for simple queries.
        
        Args:
            sql_query (str): SQL query to explain
            intent_info (Dict[str, Any]): Intent information
            
        Returns:
            str: Pattern-based explanation
        """
        sql_upper = sql_query.upper()
        
        # SELECT query
        if sql_upper.startswith("SELECT"):
            parts = self._parse_select_query(sql_query)
            
            explanation = f"This query retrieves data from the {parts['table']} table"
            
            if parts["columns"] != "*":
                explanation += f", specifically the {parts['columns']} column(s)"
            else:
                explanation += ", returning all columns"
            
            if parts["where"]:
                explanation += f", filtered by {parts['where']}"
            
            if parts["order_by"]:
                explanation += f", sorted by {parts['order_by']}"
            
            if parts["limit"]:
                explanation += f", limited to {parts['limit']} results"
            
            explanation += "."
            
            return explanation
        
        # INSERT query
        elif sql_upper.startswith("INSERT"):
            match = re.search(r"INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)", sql_query, re.IGNORECASE)
            if match:
                table = match.group(1)
                columns = match.group(2)
                return f"This query adds a new record to the {table} table with values for {columns}."
            else:
                return "This query adds a new record to the database."
        
        # UPDATE query
        elif sql_upper.startswith("UPDATE"):
            match = re.search(r"UPDATE\s+(\w+)\s+SET\s+([^WHERE]+)(?:WHERE\s+(.+))?", sql_query, re.IGNORECASE)
            if match:
                table = match.group(1)
                set_clause = match.group(2).strip()
                where_clause = match.group(3) if match.group(3) else None
                
                explanation = f"This query updates records in the {table} table, setting {set_clause}"
                
                if where_clause:
                    explanation += f" where {where_clause}"
                else:
                    explanation += " for all records"
                
                explanation += "."
                return explanation
            else:
                return "This query updates records in the database."
        
        # DELETE query
        elif sql_upper.startswith("DELETE"):
            match = re.search(r"DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?", sql_query, re.IGNORECASE)
            if match:
                table = match.group(1)
                where_clause = match.group(2) if match.group(2) else None
                
                explanation = f"This query deletes records from the {table} table"
                
                if where_clause:
                    explanation += f" where {where_clause}"
                else:
                    explanation += " (all records)"
                
                explanation += "."
                return explanation
            else:
                return "This query deletes records from the database."
        
        # Default explanation
        return "This SQL query interacts with the database based on your request."
    
    def _parse_select_query(self, sql_query: str) -> Dict[str, str]:
        """
        Parse a SELECT query into its components.
        
        Args:
            sql_query (str): SQL query to parse
            
        Returns:
            Dict[str, str]: Parsed components
        """
        parts = {
            "columns": "*",
            "table": "",
            "where": "",
            "order_by": "",
            "limit": ""
        }
        
        # Extract columns and table
        match = re.search(r"SELECT\s+(.+?)\s+FROM\s+(.+?)(?:\s+WHERE|\s+ORDER\s+BY|\s+LIMIT|\s*$)", 
                         sql_query, re.IGNORECASE | re.DOTALL)
        if match:
            parts["columns"] = match.group(1).strip()
            
            # Handle joins in the table clause
            table_clause = match.group(2).strip()
            if "JOIN" in table_clause.upper():
                parts["table"] = "multiple tables with joins"
            else:
                parts["table"] = table_clause
        
        # Extract WHERE clause
        match = re.search(r"WHERE\s+(.+?)(?:\s+ORDER\s+BY|\s+LIMIT|\s*$)", 
                         sql_query, re.IGNORECASE | re.DOTALL)
        if match:
            parts["where"] = match.group(1).strip()
        
        # Extract ORDER BY clause
        match = re.search(r"ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*$)", 
                         sql_query, re.IGNORECASE | re.DOTALL)
        if match:
            parts["order_by"] = match.group(1).strip()
        
        # Extract LIMIT clause
        match = re.search(r"LIMIT\s+(\d+)", sql_query, re.IGNORECASE)
        if match:
            parts["limit"] = match.group(1).strip()
        
        return parts
    
    def _generate_llm_explanation(self, sql_query: str, user_query: str,
                                validated_columns: Dict[str, Dict[str, Any]],
                                schema_info: Dict[str, Any]) -> str:
        """
        Generate an LLM-based explanation for complex queries.
        
        Args:
            sql_query (str): SQL query to explain
            user_query (str): Original natural language query
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            schema_info (Dict[str, Any]): Schema information
            
        Returns:
            str: LLM-based explanation
        """
        # Create context for the LLM
        context = ""
        if "tables" in schema_info:
            tables = list(schema_info["tables"].keys())
            context += f"Tables: {', '.join(tables)}\n"
        
        # Create a prompt for the LLM
        prompt = f"""
You are an expert at explaining SQL queries in simple terms. Explain the following SQL query in 1-2 short sentences:

USER QUERY: {user_query}

SQL QUERY: {sql_query}

{context}

Your explanation should be concise, non-technical, and focus on what the query does in relation to the user's request. 
Do not mention technical SQL details like "SELECT", "JOIN", etc. unless necessary. 
Explain as if talking to someone who doesn't know SQL.
"""
        
        try:
            # Get response from LLM
            explanation = get_gemini_response(prompt, response_format="text")
            
            if not explanation:
                return "This SQL query performs the database operation you requested."
            
            return explanation
            
        except Exception as e:
            logger.exception(f"Error generating explanation with LLM: {str(e)}")
            return "This SQL query performs the database operation you requested."
    
    def _generate_error_explanation(self, error_msg: str, user_query: str,
                                   validated_columns: Dict[str, Dict[str, Any]],
                                   unmapped_columns: List[str]) -> str:
        """
        Generate an explanation for SQL generation errors.
        
        Args:
            error_msg (str): Error message
            user_query (str): Original natural language query
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            unmapped_columns (List[str]): Unmapped columns
            
        Returns:
            str: Error explanation
        """
        # If there are unmapped columns, explain the column mapping issue
        if unmapped_columns and len(unmapped_columns) > 0:
            cols = ", ".join(f"'{col}'" for col in unmapped_columns)
            return f"I couldn't create a SQL query because I couldn't find these columns in the database: {cols}. Please check the column names or provide more information."
        
        # Handle common error patterns
        if "table not found" in error_msg.lower():
            match = re.search(r"table '(.+?)' not found", error_msg.lower())
            if match:
                table = match.group(1)
                return f"I couldn't create a SQL query because the table '{table}' wasn't found in the database. Please check the table name or provide more information."
        
        if "syntax error" in error_msg.lower():
            return "I encountered a syntax problem while creating the SQL query. Could you rephrase your request with more details about what you're looking for?"
        
        # General error explanation
        return f"I was unable to create a SQL query for your request. {error_msg}"
    
    def _generate_column_mapping_explanation(self, validated_columns: Dict[str, Dict[str, Any]],
                                           unmapped_columns: List[str]) -> str:
        """
        Generate an explanation for column mapping.
        
        Args:
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            unmapped_columns (List[str]): Unmapped columns
            
        Returns:
            str: Column mapping explanation
        """
        explanation = "Column details:"
        
        # Add fuzzy-matched columns explanation
        fuzzy_matches = []
        for col_name, col_info in validated_columns.items():
            if col_info.get("match_type") == "fuzzy":
                actual_column = col_info.get("column", "")
                confidence = col_info.get("confidence", 0)
                table = col_info.get("table", "")
                
                # Only include high-confidence fuzzy matches
                if confidence >= 0.8:
                    fuzzy_matches.append(f"'{col_name}' → '{table}.{actual_column}'")
        
        if fuzzy_matches:
            explanation += f"\n- Using similar column names: {', '.join(fuzzy_matches)}"
        
        # Add unmapped columns explanation
        if unmapped_columns and len(unmapped_columns) > 0:
            cols = ", ".join(f"'{col}'" for col in unmapped_columns)
            explanation += f"\n- Could not find these columns: {cols}"
        
        return explanation 
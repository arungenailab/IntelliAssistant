"""
SQL Generator Agent module for generating SQL queries based on validated intent and columns.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.agents.base_agent import BaseAgent
from utils.gemini_helper import get_gemini_response

# Configure logging
logger = logging.getLogger(__name__)

class SQLGeneratorAgent(BaseAgent):
    """
    Agent responsible for generating SQL queries based on validated 
    user intent and columns.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SQL Generator Agent.
        
        Args:
            name (str): Name of the agent
            config (Dict[str, Any], optional): Configuration for the agent
        """
        super().__init__(name, config)
        
        # SQL templates for different operations
        self.templates = {
            "select": "SELECT {columns} FROM {tables}{where}{group_by}{order_by}{limit}",
            "insert": "INSERT INTO {table} ({columns}) VALUES ({values})",
            "update": "UPDATE {table} SET {set_values}{where}",
            "delete": "DELETE FROM {table}{where}"
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data to generate a SQL query.
        
        Args:
            input_data (Dict[str, Any]): Input data including intent and validated columns
            
        Returns:
            Dict[str, Any]: Results including the generated SQL query
        """
        # Validate input
        required_fields = ["intent_info", "validated_columns", "schema_info", "tables_used"]
        if not self.validate_input(input_data, required_fields):
            return {
                "success": False,
                "error": "Missing required intent, columns, or schema information",
                "sql": ""
            }
        
        intent_info = input_data["intent_info"]
        validated_columns = input_data["validated_columns"]
        schema_info = input_data["schema_info"]
        tables_used = input_data["tables_used"]
        operation = intent_info.get("operation", "select").lower()
        
        try:
            # Generate SQL based on the operation
            if operation == "select":
                sql_query = self._generate_select_query(intent_info, validated_columns, 
                                                      schema_info, tables_used)
            elif operation == "insert":
                sql_query = self._generate_insert_query(intent_info, validated_columns, 
                                                      schema_info, tables_used)
            elif operation == "update":
                sql_query = self._generate_update_query(intent_info, validated_columns, 
                                                      schema_info, tables_used)
            elif operation == "delete":
                sql_query = self._generate_delete_query(intent_info, validated_columns, 
                                                      schema_info, tables_used)
            else:
                # Fallback to LLM for complex or unsupported operations
                sql_query = self._generate_with_llm(input_data)
            
            # Validate the generated SQL
            is_valid, error_msg = self._validate_sql(sql_query, schema_info)
            
            if not is_valid:
                logger.warning(f"Generated SQL validation failed: {error_msg}")
                # Try to fix the SQL or fall back to LLM
                sql_query = self._generate_with_llm(input_data, error_msg)
                is_valid, error_msg = self._validate_sql(sql_query, schema_info)
            
            # Store SQL in state
            self.update_state({
                "generated_sql": sql_query,
                "is_valid": is_valid,
                "error_msg": error_msg
            })
            
            # Return success
            result = {
                "success": is_valid,
                "sql": sql_query,
                "error": error_msg if not is_valid else None
            }
            
            self.log_result(result)
            return result
            
        except Exception as e:
            logger.exception(f"Error in SQLGeneratorAgent: {str(e)}")
            return {
                "success": False,
                "error": f"SQL generation error: {str(e)}",
                "sql": ""
            }
    
    def _generate_select_query(self, intent_info: Dict[str, Any], 
                              validated_columns: Dict[str, Dict[str, Any]],
                              schema_info: Dict[str, Any],
                              tables_used: List[str]) -> str:
        """
        Generate a SELECT query based on the intent and validated columns.
        
        Args:
            intent_info (Dict[str, Any]): Intent information
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            schema_info (Dict[str, Any]): Schema information
            tables_used (List[str]): List of tables used
            
        Returns:
            str: Generated SELECT query
        """
        # Determine columns to select
        columns_clause = self._build_columns_clause(intent_info, validated_columns, tables_used)
        
        # Determine tables and joins
        tables_clause = self._build_tables_clause(tables_used, schema_info)
        
        # Build WHERE clause
        where_clause = self._build_where_clause(intent_info)
        
        # Build GROUP BY clause
        group_by_clause = self._build_group_by_clause(intent_info)
        
        # Build ORDER BY clause
        order_by_clause = self._build_order_by_clause(intent_info)
        
        # Build LIMIT clause
        limit_clause = self._build_limit_clause(intent_info)
        
        # Format the template
        sql_query = self.templates["select"].format(
            columns=columns_clause,
            tables=tables_clause,
            where=where_clause,
            group_by=group_by_clause,
            order_by=order_by_clause,
            limit=limit_clause
        )
        
        return sql_query
    
    def _build_columns_clause(self, intent_info: Dict[str, Any],
                             validated_columns: Dict[str, Dict[str, Any]],
                             tables_used: List[str]) -> str:
        """
        Build the columns clause for a SELECT query.
        
        Args:
            intent_info (Dict[str, Any]): Intent information
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            tables_used (List[str]): List of tables used
            
        Returns:
            str: Columns clause
        """
        # If no specific columns were mentioned, use * with table prefix
        if not validated_columns:
            if len(tables_used) == 1:
                return "*"
            else:
                # Multiple tables, use table.* for each
                return ", ".join([f"{table}.*" for table in tables_used])
        
        # If aggregation is required
        if intent_info.get("requires_aggregation", False):
            agg_type = intent_info.get("aggregation_type", "count").upper()
            
            # If only one column is specified, apply aggregation to it
            if len(validated_columns) == 1:
                col_info = list(validated_columns.values())[0]
                col_name = col_info["column"]
                table_name = col_info["table"]
                
                if agg_type == "COUNT":
                    return f"COUNT({table_name}.{col_name})"
                else:
                    return f"{agg_type}({table_name}.{col_name})"
            
            # Multiple columns with aggregation
            columns = []
            for col_name, col_info in validated_columns.items():
                table_name = col_info["table"]
                if agg_type == "COUNT":
                    columns.append(f"{table_name}.{col_info['column']}")
                else:
                    # Only apply aggregation to numeric columns
                    data_type = col_info.get("data_type", "").lower()
                    if "int" in data_type or "float" in data_type or "decimal" in data_type:
                        columns.append(f"{agg_type}({table_name}.{col_info['column']})")
                    else:
                        columns.append(f"{table_name}.{col_info['column']}")
            
            return ", ".join(columns)
        
        # Regular column selection
        columns = []
        for col_name, col_info in validated_columns.items():
            table_name = col_info["table"]
            # Use fully qualified column names when multiple tables are involved
            if len(tables_used) > 1:
                columns.append(f"{table_name}.{col_info['column']}")
            else:
                columns.append(col_info['column'])
        
        return ", ".join(columns)
    
    def _build_tables_clause(self, tables_used: List[str], 
                            schema_info: Dict[str, Any]) -> str:
        """
        Build the tables clause with joins if necessary.
        
        Args:
            tables_used (List[str]): List of tables used
            schema_info (Dict[str, Any]): Schema information
            
        Returns:
            str: Tables clause
        """
        # Single table case
        if len(tables_used) <= 1:
            return tables_used[0] if tables_used else ""
        
        # Multiple tables - need to determine joins
        if "relationships" not in schema_info:
            # If no relationships defined, use simple cross join
            return " CROSS JOIN ".join(tables_used)
        
        # Start with the first table
        result = tables_used[0]
        used = set([tables_used[0]])
        remaining = set(tables_used[1:])
        
        # Try to find relationships for proper joins
        while remaining:
            found_join = False
            
            for rel in schema_info["relationships"]:
                parent_table = rel.get("parent_table", "")
                child_table = rel.get("child_table", "")
                parent_column = rel.get("parent_column", "")
                child_column = rel.get("child_column", "")
                
                # Check if this relationship connects a used table to a remaining one
                if parent_table in used and child_table in remaining:
                    result += f" LEFT JOIN {child_table} ON {parent_table}.{parent_column} = {child_table}.{child_column}"
                    used.add(child_table)
                    remaining.remove(child_table)
                    found_join = True
                    break
                elif child_table in used and parent_table in remaining:
                    result += f" LEFT JOIN {parent_table} ON {child_table}.{child_column} = {parent_table}.{parent_column}"
                    used.add(parent_table)
                    remaining.remove(parent_table)
                    found_join = True
                    break
            
            # If no proper join found, use cross join for the next table
            if not found_join and remaining:
                next_table = list(remaining)[0]
                result += f" CROSS JOIN {next_table}"
                used.add(next_table)
                remaining.remove(next_table)
        
        return result
    
    def _build_where_clause(self, intent_info: Dict[str, Any]) -> str:
        """
        Build the WHERE clause based on intent information.
        
        Args:
            intent_info (Dict[str, Any]): Intent information
            
        Returns:
            str: WHERE clause
        """
        if not intent_info.get("has_filters", False):
            return ""
        
        filters = intent_info.get("filters", [])
        if not filters:
            return ""
        
        # Convert filter conditions to SQL syntax (simplified for demo)
        # In a real implementation, you would need more sophisticated parsing
        filter_conditions = []
        for filter_text in filters:
            # Try to extract condition with regex
            if "=" in filter_text:
                parts = filter_text.split("=", 1)
                col = parts[0].strip()
                val = parts[1].strip()
                # Add quotes for string values
                if not val.isdigit() and not val.startswith("'") and not val.startswith('"'):
                    val = f"'{val}'"
                filter_conditions.append(f"{col} = {val}")
            elif ">" in filter_text:
                parts = filter_text.split(">", 1)
                col = parts[0].strip()
                val = parts[1].strip()
                filter_conditions.append(f"{col} > {val}")
            elif "<" in filter_text:
                parts = filter_text.split("<", 1)
                col = parts[0].strip()
                val = parts[1].strip()
                filter_conditions.append(f"{col} < {val}")
            elif "like" in filter_text.lower():
                parts = filter_text.lower().split("like", 1)
                col = parts[0].strip()
                val = parts[1].strip()
                if not val.startswith("'") and not val.startswith('"'):
                    val = f"'%{val}%'"
                filter_conditions.append(f"{col} LIKE {val}")
            else:
                # Simplistic approach for demo
                filter_conditions.append(filter_text)
        
        # If we couldn't parse any conditions, return empty
        if not filter_conditions:
            return ""
            
        return " WHERE " + " AND ".join(filter_conditions)
    
    def _build_group_by_clause(self, intent_info: Dict[str, Any]) -> str:
        """
        Build the GROUP BY clause based on intent information.
        
        Args:
            intent_info (Dict[str, Any]): Intent information
            
        Returns:
            str: GROUP BY clause
        """
        if not intent_info.get("has_grouping", False):
            return ""
        
        group_by = intent_info.get("group_by", [])
        if not group_by:
            return ""
        
        return " GROUP BY " + ", ".join(group_by)
    
    def _build_order_by_clause(self, intent_info: Dict[str, Any]) -> str:
        """
        Build the ORDER BY clause based on intent information.
        
        Args:
            intent_info (Dict[str, Any]): Intent information
            
        Returns:
            str: ORDER BY clause
        """
        if not intent_info.get("has_ordering", False):
            return ""
        
        order_by = intent_info.get("order_by", [])
        if not order_by:
            return ""
        
        clauses = []
        for item in order_by:
            if isinstance(item, dict):
                col = item.get("column", "")
                direction = item.get("direction", "").upper()
                if col:
                    if direction in ["ASC", "DESC"]:
                        clauses.append(f"{col} {direction}")
                    else:
                        clauses.append(col)
            elif isinstance(item, str):
                clauses.append(item)
        
        if not clauses:
            return ""
            
        return " ORDER BY " + ", ".join(clauses)
    
    def _build_limit_clause(self, intent_info: Dict[str, Any]) -> str:
        """
        Build the LIMIT clause based on intent information.
        
        Args:
            intent_info (Dict[str, Any]): Intent information
            
        Returns:
            str: LIMIT clause
        """
        if not intent_info.get("has_limit", False):
            return ""
        
        limit = intent_info.get("limit")
        if not limit:
            return ""
        
        try:
            limit_val = int(limit)
            return f" LIMIT {limit_val}"
        except (ValueError, TypeError):
            return ""
    
    def _generate_insert_query(self, intent_info: Dict[str, Any], 
                              validated_columns: Dict[str, Dict[str, Any]],
                              schema_info: Dict[str, Any],
                              tables_used: List[str]) -> str:
        """
        Generate an INSERT query based on the intent and validated columns.
        
        Args:
            intent_info (Dict[str, Any]): Intent information
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            schema_info (Dict[str, Any]): Schema information
            tables_used (List[str]): List of tables used
            
        Returns:
            str: Generated INSERT query
        """
        # For INSERT, we need exactly one table
        if not tables_used or len(tables_used) != 1:
            return ""
        
        table = tables_used[0]
        
        # Get columns and placeholder values
        columns = []
        values = []
        
        for col_name, col_info in validated_columns.items():
            # Only include columns from the target table
            if col_info["table"] == table:
                columns.append(col_info["column"])
                
                # Use placeholders for values in prepared statements
                values.append("?")
        
        # If no columns specified, return empty query
        if not columns:
            return ""
        
        # Format the template
        sql_query = self.templates["insert"].format(
            table=table,
            columns=", ".join(columns),
            values=", ".join(values)
        )
        
        return sql_query
    
    def _generate_update_query(self, intent_info: Dict[str, Any], 
                              validated_columns: Dict[str, Dict[str, Any]],
                              schema_info: Dict[str, Any],
                              tables_used: List[str]) -> str:
        """
        Generate an UPDATE query based on the intent and validated columns.
        
        Args:
            intent_info (Dict[str, Any]): Intent information
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            schema_info (Dict[str, Any]): Schema information
            tables_used (List[str]): List of tables used
            
        Returns:
            str: Generated UPDATE query
        """
        # For UPDATE, we need exactly one table
        if not tables_used or len(tables_used) != 1:
            return ""
        
        table = tables_used[0]
        
        # Build SET clause with placeholders
        set_values = []
        for col_name, col_info in validated_columns.items():
            # Only include columns from the target table
            if col_info["table"] == table:
                set_values.append(f"{col_info['column']} = ?")
        
        # If no columns to update, return empty query
        if not set_values:
            return ""
        
        # Build WHERE clause
        where_clause = self._build_where_clause(intent_info)
        
        # Format the template
        sql_query = self.templates["update"].format(
            table=table,
            set_values=", ".join(set_values),
            where=where_clause
        )
        
        return sql_query
    
    def _generate_delete_query(self, intent_info: Dict[str, Any], 
                              validated_columns: Dict[str, Dict[str, Any]],
                              schema_info: Dict[str, Any],
                              tables_used: List[str]) -> str:
        """
        Generate a DELETE query based on the intent.
        
        Args:
            intent_info (Dict[str, Any]): Intent information
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            schema_info (Dict[str, Any]): Schema information
            tables_used (List[str]): List of tables used
            
        Returns:
            str: Generated DELETE query
        """
        # For DELETE, we need exactly one table
        if not tables_used or len(tables_used) != 1:
            return ""
        
        table = tables_used[0]
        
        # Build WHERE clause (important for DELETE to avoid deleting all records)
        where_clause = self._build_where_clause(intent_info)
        
        # Format the template
        sql_query = self.templates["delete"].format(
            table=table,
            where=where_clause
        )
        
        return sql_query
    
    def _validate_sql(self, sql_query: str, schema_info: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate the generated SQL query.
        
        Args:
            sql_query (str): SQL query to validate
            schema_info (Dict[str, Any]): Schema information
            
        Returns:
            Tuple[bool, Optional[str]]: Tuple of (is_valid, error_message)
        """
        # Check if the query is empty or None
        if not sql_query or sql_query.strip() == "":
            return False, "Empty SQL query"
            
        # Check if the query has basic SQL structure
        sql_query = sql_query.strip()
        
        # Check if query starts with a valid SQL command
        valid_starts = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"]
        if not any(sql_query.upper().startswith(cmd) for cmd in valid_starts):
            return False, f"SQL query must start with one of: {', '.join(valid_starts)}"
        
        # Basic syntax validation
        try:
            # Check for unbalanced parentheses
            if sql_query.count('(') != sql_query.count(')'):
                return False, "Unbalanced parentheses in SQL query"
                
            # Check for FROM clause in SELECT statements
            if sql_query.upper().startswith("SELECT") and "FROM" not in sql_query.upper():
                return False, "SELECT statement missing FROM clause"
                
            # Check for malformed WHERE conditions
            if "WHERE" in sql_query.upper():
                where_idx = sql_query.upper().find("WHERE")
                after_where = sql_query[where_idx + 5:].strip()
                if not after_where or after_where.startswith(("ORDER", "GROUP", "HAVING", "LIMIT")):
                    return False, "WHERE clause is incomplete"
            
            # Check for missing table names
            if "FROM" in sql_query.upper() and not re.search(r"FROM\s+\w+", sql_query, re.IGNORECASE):
                return False, "FROM clause missing table name"
            
            # Add more validation as needed
            
            return True, None
            
        except Exception as e:
            logger.exception(f"Error validating SQL: {str(e)}")
            return False, f"SQL validation error: {str(e)}"
    
    def _generate_fallback_query(self, tables_used: List[str]) -> str:
        """
        Generate a fallback SQL query when other methods fail.
        This ensures we always have a valid SQL query to return.
        
        Args:
            tables_used (List[str]): List of tables to use in the query
            
        Returns:
            str: A simple but valid SQL query
        """
        # If no tables specified, use a default table
        if not tables_used:
            # Get the first table from schema info if available
            schema_info = self.state.get("schema_info", {})
            if "tables" in schema_info and schema_info["tables"]:
                table_name = next(iter(schema_info["tables"].keys()))
            else:
                # No tables found in schema, use a generic name
                table_name = "Transactions"  # Common default table
        else:
            table_name = tables_used[0]
        
        # Generate a basic SELECT query with TOP/LIMIT to ensure it's not too large
        if "SQLServer" in self.config.get("db_type", "").upper():
            return f"SELECT TOP 1000 * FROM {table_name}"
        else:
            return f"SELECT * FROM {table_name} LIMIT 1000"
    
    def _generate_with_llm(self, input_data: Dict[str, Any], 
                          error_msg: Optional[str] = None) -> str:
        """
        Generate SQL using a Language Learning Model (LLM).
        
        Args:
            input_data (Dict[str, Any]): Input data
            error_msg (Optional[str]): Error message from previous generation attempt
            
        Returns:
            str: Generated SQL query
        """
        try:
            # Extract required data
            schema_info = input_data["schema_info"]
            tables_used = input_data["tables_used"]
            intent_info = input_data["intent_info"]
            validated_columns = input_data.get("validated_columns", {})
            
            # Create schema context for the LLM
            schema_context = self._create_schema_context(schema_info, tables_used)
            
            # Format validated columns
            columns_context = self._format_validated_columns(validated_columns)
            
            # Build system prompt
            system_prompt = f"""
            You are an expert SQL query generator. Generate a valid SQL query based on the user's request.
            Use ONLY the tables and columns provided in the schema context.
            
            Schema Context:
            {schema_context}
            
            Validated Columns:
            {columns_context}
            
            {"Previous Error: " + error_msg if error_msg else ""}
            
            Instructions:
            1. ONLY use tables and columns from the provided schema
            2. Ensure proper joins are used when multiple tables are involved
            3. Return ONLY the SQL query without any explanation or markdown
            4. Use proper SQL syntax for the database type
            5. Do not use any columns or tables not listed in the schema
            6. Include table names for columns when joining multiple tables
            """
            
            # Build query prompt
            query_prompt = f"""
            Create a SQL query to {intent_info.get('description', 'retrieve data')}
            
            The query should:
            - Operation: {intent_info.get('operation', 'select')}
            {f"- Conditions: {intent_info.get('conditions', '')}" if intent_info.get('conditions') else ""}
            {f"- Sorting: {intent_info.get('order_by', '')}" if intent_info.get('order_by') else ""}
            {f"- Group By: {intent_info.get('group_by', '')}" if intent_info.get('group_by') else ""}
            {f"- Limit: {intent_info.get('limit', '')}" if intent_info.get('limit') else ""}
            
            Tables to use: {', '.join(tables_used) if tables_used else 'Any appropriate table from the schema'}
            """
            
            # Call the LLM
            llm_response = get_gemini_response(
                prompt=query_prompt,
                system_prompt=system_prompt,
                response_format="text",
                model=self.config.get("llm_model", "models/gemini-2.0-flash")
            )
            
            # Extract the SQL from the response
            if isinstance(llm_response, dict) and "error" in llm_response:
                logger.warning(f"LLM error: {llm_response['error']}")
                return self._generate_fallback_query(tables_used)
                
            sql_query = self._extract_sql_from_text(llm_response)
            
            # Validate the query
            is_valid, error = self._validate_sql(sql_query, schema_info)
            if not is_valid:
                logger.warning(f"LLM generated invalid SQL: {error}")
                return self._generate_fallback_query(tables_used)
                
            return sql_query
        
        except Exception as e:
            logger.exception(f"Error generating SQL with LLM: {str(e)}")
            return self._generate_fallback_query(input_data.get("tables_used", []))
    
    def _extract_sql_from_text(self, text: str) -> str:
        """
        Extract SQL query from text response.
        
        Args:
            text (str): Text containing SQL query
            
        Returns:
            str: Extracted SQL query
        """
        if not text:
            return ""
            
        # Try to extract SQL between code blocks
        code_block_pattern = r"```(?:sql)?\s*([\s\S]*?)\s*```"
        matches = re.findall(code_block_pattern, text)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks, assume the entire text is SQL
        # but clean up any markdown or explanations
        lines = text.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip common markdown and explanatory text markers
            if line and not line.startswith(('#', '-', '*', '>', '|')):
                sql_lines.append(line)
        
        return ' '.join(sql_lines).strip()
    
    def _create_schema_context(self, schema_info: Dict[str, Any], 
                              tables_used: List[str]) -> str:
        """
        Create a schema context for the LLM.
        
        Args:
            schema_info (Dict[str, Any]): Schema information
            tables_used (List[str]): List of tables used
            
        Returns:
            str: Schema context
        """
        context = "DATABASE SCHEMA:\n"
        
        if "tables" not in schema_info:
            return context
            
        # Include detailed information only for tables being used
        for table_name in tables_used:
            if table_name not in schema_info["tables"]:
                continue
                
            table_info = schema_info["tables"][table_name]
            context += f"Table: {table_name}\n"
            
            if "columns" in table_info:
                context += "Columns:\n"
                for col_name, col_info in table_info["columns"].items():
                    data_type = col_info.get("data_type", "unknown")
                    is_nullable = col_info.get("is_nullable", True)
                    context += f"  - {col_name} ({data_type})"
                    if not is_nullable:
                        context += " NOT NULL"
                        
                    # Add primary key information
                    if col_info.get("is_primary_key", False):
                        context += " PRIMARY KEY"
                        
                    context += "\n"
        
        # Add relationship information
        if "relationships" in schema_info:
            context += "\nRelationships:\n"
            for rel in schema_info["relationships"]:
                parent_table = rel.get("parent_table", "")
                child_table = rel.get("child_table", "")
                parent_column = rel.get("parent_column", "")
                child_column = rel.get("child_column", "")
                
                # Only include relationships relevant to the tables being used
                if parent_table in tables_used or child_table in tables_used:
                    context += f"  - {parent_table}.{parent_column} -> {child_table}.{child_column}\n"
        
        return context
    
    def _format_validated_columns(self, validated_columns: Dict[str, Dict[str, Any]]) -> str:
        """
        Format validated columns for the LLM.
        
        Args:
            validated_columns (Dict[str, Dict[str, Any]]): Validated columns
            
        Returns:
            str: Formatted column information
        """
        result = ""
        for col_name, col_info in validated_columns.items():
            table_name = col_info.get("table", "")
            column_name = col_info.get("column", "")
            data_type = col_info.get("data_type", "")
            match_type = col_info.get("match_type", "")
            
            result += f"  - {table_name}.{column_name} ({data_type})"
            if match_type != "exact":
                result += f" [matched from '{col_name}' using {match_type}]"
            result += "\n"
        
        return result 
"""
Schema Utilities for SQL validation.

This module provides utilities for validating SQL queries against
a database schema.
"""

import logging
import re
import sqlparse
from typing import Dict, Any, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ColumnValidator:
    """Validates SQL query columns against a database schema."""
    
    def __init__(self):
        """Initialize the ColumnValidator."""
        pass
        
    def validate(self, sql_query: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that columns in the SQL query exist in the schema.
        
        Args:
            sql_query: The SQL query to validate.
            schema_info: Database schema information.
            
        Returns:
            Dict with validation results, including:
                - valid (bool): Whether the query is valid.
                - issues (List[str]): List of validation issues.
        """
        try:
            # Parse the SQL query
            parsed = sqlparse.parse(sql_query)
            if not parsed:
                return {"valid": False, "issues": ["Failed to parse SQL query"]}
                
            # Extract column references
            column_refs = self._extract_column_references(sql_query)
            
            # Get available columns from schema
            available_columns = self._get_available_columns(schema_info)
            
            # Check if all column references exist in the schema
            issues = []
            for col_ref in column_refs:
                # Check if the column reference includes a table name
                if "." in col_ref:
                    table_name, col_name = col_ref.split(".", 1)
                    # Check if table exists
                    if table_name not in available_columns:
                        issues.append(f"Table '{table_name}' not found in schema")
                        continue
                    # Check if column exists in table
                    if col_name.lower() not in [c.lower() for c in available_columns[table_name]]:
                        issues.append(f"Column '{col_name}' not found in table '{table_name}'")
                else:
                    # For columns without table reference, check if they exist in any table
                    found = False
                    for table_name, columns in available_columns.items():
                        if col_ref.lower() in [c.lower() for c in columns]:
                            found = True
                            break
                    if not found:
                        issues.append(f"Column '{col_ref}' not found in any table")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Error validating SQL query: {str(e)}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"]
            }
    
    def _extract_column_references(self, sql_query: str) -> List[str]:
        """
        Extract column references from an SQL query.
        
        This is a simplified extraction that may not catch all cases.
        
        Args:
            sql_query: The SQL query to extract from.
            
        Returns:
            List of column references.
        """
        # Parse the SQL query
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return []
            
        # Extract column names from the SQL tokens
        column_refs = []
        
        # Look for identifiers that could be column references
        for token in parsed[0].flatten():
            if token.ttype is None and isinstance(token, sqlparse.sql.Identifier):
                # Add the identifier value as a possible column reference
                column_refs.append(token.value)
            
        # Also use regex to find column references that sqlparse might miss
        # Match patterns like "table.column" or standalone "column"
        regex_refs = re.findall(r'(?:^|\s)(\w+\.\w+|\w+)(?=\s|$|,|\)|\()', sql_query)
        for ref in regex_refs:
            if ref not in column_refs and ref.lower() not in [
                'select', 'from', 'where', 'join', 'inner', 'outer', 'left', 'right',
                'on', 'and', 'or', 'not', 'in', 'between', 'like', 'is', 'null',
                'group', 'by', 'having', 'order', 'limit', 'offset', 'as'
            ]:
                column_refs.append(ref)
        
        return column_refs
    
    def _get_available_columns(self, schema_info: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Get available columns from schema info.
        
        Args:
            schema_info: Database schema information.
            
        Returns:
            Dict mapping table names to lists of column names.
        """
        available_columns = {}
        
        # Extract tables and their columns from schema info
        for table in schema_info.get("tables", []):
            table_name = table.get("table_name", "")
            if table_name:
                columns = []
                for column in table.get("columns", []):
                    column_name = column.get("column_name", "")
                    if column_name:
                        columns.append(column_name)
                available_columns[table_name] = columns
        
        return available_columns 
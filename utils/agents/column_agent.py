"""
Column Agent module for validating and mapping column references.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.agents.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)

class ColumnAgent(BaseAgent):
    """
    Agent responsible for validating column references
    and mapping them to actual database columns.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Column Agent.
        
        Args:
            name (str): Name of the agent
            config (Dict[str, Any], optional): Configuration for the agent
        """
        super().__init__(name, config)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data to validate and map column references.
        
        Args:
            input_data (Dict[str, Any]): Input data including intent info and schema
            
        Returns:
            Dict[str, Any]: Results including validated columns
        """
        # Validate input
        if not self.validate_input(input_data, ["intent_info", "schema_info"]):
            return {
                "success": False,
                "error": "Missing required intent or schema information",
                "validated_columns": {}
            }
        
        intent_info = input_data["intent_info"]
        schema_info = input_data["schema_info"]
        
        try:
            # Get inferred tables and columns from intent
            inferred_tables = intent_info.get("tables", [])
            inferred_columns = intent_info.get("columns", [])
            
            # If no tables were inferred, try to infer from columns
            if not inferred_tables:
                inferred_tables = self._infer_tables_from_columns(inferred_columns, schema_info)
                
            # If still no tables, use all tables as fallback
            if not inferred_tables and "tables" in schema_info:
                inferred_tables = list(schema_info["tables"].keys())
                logger.info("No specific tables inferred, considering all tables")
            
            # Validate and map columns
            validated_columns, unmapped_columns = self._validate_columns(
                inferred_columns, inferred_tables, schema_info
            )
            
            # Apply fuzzy matching for unmapped columns
            fuzzy_matches = self._fuzzy_match_columns(unmapped_columns, inferred_tables, schema_info)
            validated_columns.update(fuzzy_matches)
            
            # Update remaining unmapped columns
            unmapped_columns = [col for col in unmapped_columns if col not in fuzzy_matches]
            
            # Determine if validation was successful
            success = len(unmapped_columns) == 0 or len(validated_columns) > 0
            
            # Store validated columns in state
            self.update_state({
                "validated_columns": validated_columns,
                "unmapped_columns": unmapped_columns
            })
            
            # Determine tables used in the validated columns
            tables_used = set()
            for col_key in validated_columns:
                table_name = validated_columns[col_key].get("table")
                if table_name:
                    tables_used.add(table_name)
            
            # Return success
            result = {
                "success": success,
                "validated_columns": validated_columns,
                "unmapped_columns": unmapped_columns,
                "tables_used": list(tables_used),
                "columns_used": list(validated_columns.keys()),
                "error": None if success else f"Could not map columns: {', '.join(unmapped_columns)}"
            }
            
            self.log_result(result)
            return result
            
        except Exception as e:
            logger.exception(f"Error in ColumnAgent: {str(e)}")
            return {
                "success": False,
                "error": f"Column validation error: {str(e)}",
                "validated_columns": {}
            }
    
    def _infer_tables_from_columns(self, columns: List[str], 
                                  schema_info: Dict[str, Any]) -> List[str]:
        """
        Infer tables based on column names.
        
        Args:
            columns (List[str]): List of column names
            schema_info (Dict[str, Any]): Database schema information
            
        Returns:
            List[str]: List of inferred table names
        """
        inferred_tables = set()
        
        if not columns or "tables" not in schema_info:
            return list(inferred_tables)
        
        # Check each table to see if it contains any of the mentioned columns
        for table_name, table_info in schema_info["tables"].items():
            if "columns" not in table_info:
                continue
                
            table_columns = set(table_info["columns"].keys())
            
            # Check for exact matches
            for col in columns:
                if col in table_columns:
                    inferred_tables.add(table_name)
                    break
            
            # If no exact matches, try fuzzy matching
            if table_name not in inferred_tables:
                for col in columns:
                    # Check for partial matches
                    for table_col in table_columns:
                        # Simple case: column is part of table column name
                        if col.lower() in table_col.lower():
                            inferred_tables.add(table_name)
                            break
                        
                        # Case with common prefixes/suffixes removed
                        clean_col = self._clean_column_name(col)
                        clean_table_col = self._clean_column_name(table_col)
                        
                        if clean_col.lower() in clean_table_col.lower():
                            inferred_tables.add(table_name)
                            break
        
        return list(inferred_tables)
    
    def _clean_column_name(self, column_name: str) -> str:
        """
        Clean a column name by removing common prefixes and suffixes.
        
        Args:
            column_name (str): Original column name
            
        Returns:
            str: Cleaned column name
        """
        # Convert to lowercase
        col = column_name.lower()
        
        # Remove common prefixes
        prefixes = ["col_", "column_", "fld_", "field_", "the_", "is_", "has_"]
        for prefix in prefixes:
            if col.startswith(prefix):
                col = col[len(prefix):]
                break
        
        # Remove common suffixes
        suffixes = ["_id", "_code", "_name", "_num", "_date", "_time", "_count", "_amount"]
        for suffix in suffixes:
            if col.endswith(suffix):
                col = col[:-len(suffix)]
                break
        
        return col
    
    def _validate_columns(self, columns: List[str], tables: List[str], 
                         schema_info: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        """
        Validate columns against the schema and map them to actual columns.
        
        Args:
            columns (List[str]): List of inferred column names
            tables (List[str]): List of inferred table names
            schema_info (Dict[str, Any]): Database schema information
            
        Returns:
            Tuple[Dict[str, Dict[str, Any]], List[str]]: 
                - Validated columns mapping
                - List of unmapped columns
        """
        validated_columns = {}
        unmapped_columns = []
        
        if not "tables" in schema_info:
            return validated_columns, columns
        
        # Check for exact column matches in the inferred tables
        for col in columns:
            found = False
            
            for table_name in tables:
                if table_name not in schema_info["tables"]:
                    continue
                    
                table_info = schema_info["tables"][table_name]
                
                if "columns" not in table_info:
                    continue
                
                # Direct match
                if col in table_info["columns"]:
                    validated_columns[col] = {
                        "table": table_name,
                        "column": col,
                        "match_type": "exact",
                        "data_type": table_info["columns"][col].get("data_type", "unknown")
                    }
                    found = True
                    break
                
                # Case-insensitive match
                for table_col in table_info["columns"]:
                    if col.lower() == table_col.lower():
                        validated_columns[col] = {
                            "table": table_name,
                            "column": table_col,  # Use the correct case from schema
                            "match_type": "case_insensitive",
                            "data_type": table_info["columns"][table_col].get("data_type", "unknown")
                        }
                        found = True
                        break
                
                if found:
                    break
            
            if not found:
                unmapped_columns.append(col)
        
        return validated_columns, unmapped_columns
    
    def _fuzzy_match_columns(self, unmapped_columns: List[str], tables: List[str],
                           schema_info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Apply fuzzy matching to unmapped columns.
        
        Args:
            unmapped_columns (List[str]): List of unmapped column names
            tables (List[str]): List of inferred table names
            schema_info (Dict[str, Any]): Database schema information
            
        Returns:
            Dict[str, Dict[str, Any]]: Fuzzy-matched columns
        """
        fuzzy_matches = {}
        
        if not "tables" in schema_info:
            return fuzzy_matches
        
        for col in unmapped_columns:
            best_match = None
            best_score = 0
            best_table = None
            best_column = None
            
            for table_name in tables:
                if table_name not in schema_info["tables"]:
                    continue
                    
                table_info = schema_info["tables"][table_name]
                
                if "columns" not in table_info:
                    continue
                
                for table_col in table_info["columns"]:
                    # Calculate match score
                    score = self._calculate_match_score(col, table_col)
                    
                    if score > best_score:
                        best_score = score
                        best_table = table_name
                        best_column = table_col
                        best_match = {
                            "table": table_name,
                            "column": table_col,
                            "match_type": "fuzzy",
                            "confidence": score,
                            "data_type": table_info["columns"][table_col].get("data_type", "unknown")
                        }
            
            # Only accept matches with a minimum confidence
            if best_match and best_score >= 0.7:  # 70% confidence threshold
                fuzzy_matches[col] = best_match
                logger.info(f"Fuzzy matched '{col}' to '{best_table}.{best_column}' with score {best_score}")
        
        return fuzzy_matches
    
    def _calculate_match_score(self, col1: str, col2: str) -> float:
        """
        Calculate a match score between two column names.
        
        Args:
            col1 (str): First column name
            col2 (str): Second column name
            
        Returns:
            float: Match score between 0 and 1
        """
        # Convert to lowercase for comparison
        a = col1.lower()
        b = col2.lower()
        
        # Clean column names
        clean_a = self._clean_column_name(a)
        clean_b = self._clean_column_name(b)
        
        # Direct match check
        if a == b:
            return 1.0
        
        # Check if one is contained in the other
        if a in b or b in a:
            return 0.9
        
        # Check if cleaned versions match
        if clean_a == clean_b:
            return 0.85
        
        # Check if cleaned versions are contained in each other
        if clean_a in clean_b or clean_b in clean_a:
            return 0.8
        
        # Check for common substrings
        common_len = len(self._longest_common_substring(a, b))
        max_len = max(len(a), len(b))
        
        if max_len > 0:
            return 0.7 * (common_len / max_len)
        
        # No significant match
        return 0.0
    
    def _longest_common_substring(self, s1: str, s2: str) -> str:
        """
        Find the longest common substring between two strings.
        
        Args:
            s1 (str): First string
            s2 (str): Second string
            
        Returns:
            str: Longest common substring
        """
        m = [[0] * (1 + len(s2)) for _ in range(1 + len(s1))]
        longest, x_longest = 0, 0
        
        for x in range(1, 1 + len(s1)):
            for y in range(1, 1 + len(s2)):
                if s1[x - 1] == s2[y - 1]:
                    m[x][y] = m[x - 1][y - 1] + 1
                    if m[x][y] > longest:
                        longest = m[x][y]
                        x_longest = x
                else:
                    m[x][y] = 0
        
        return s1[x_longest - longest: x_longest] 
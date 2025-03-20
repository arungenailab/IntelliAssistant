"""
Intent Agent module for analyzing natural language queries.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.agents.base_agent import BaseAgent
from utils.gemini_helper import get_gemini_response

# Configure logging
logger = logging.getLogger(__name__)

class IntentAgent(BaseAgent):
    """
    Agent responsible for analyzing the user's query to extract intent,
    tables, columns, operations, and constraints.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Intent Agent.
        
        Args:
            name (str): Name of the agent
            config (Dict[str, Any], optional): Configuration for the agent
        """
        super().__init__(name, config)
        
        # Common query patterns
        self.operation_keywords = {
            "select": ["show", "get", "find", "list", "display", "retrieve", "what", "which"],
            "insert": ["add", "create", "insert", "new", "register"],
            "update": ["update", "change", "modify", "edit", "set", "alter"],
            "delete": ["delete", "remove", "drop", "eliminate"]
        }
        
        # Common aggregation functions
        self.aggregation_keywords = [
            "count", "sum", "average", "avg", "min", "max", "mean", "total",
            "standard deviation", "std", "variance", "var"
        ]
        
        # Common filtering words
        self.filter_keywords = [
            "where", "if", "when", "with", "that has", "having", "containing", "equals", 
            "greater than", "less than", "between", "in", "not in", "like", "matches",
            "older than", "newer than", "recent", "latest", "earliest", "first", "last"
        ]
        
        # Group by indicators
        self.groupby_keywords = [
            "group by", "grouped by", "per", "for each", "by each", "based on", "categorize by",
            "summarize by", "aggregate by"
        ]
        
        # Order by indicators
        self.orderby_keywords = [
            "order by", "ordered by", "sort by", "sorted by", "arrange by", "arranged by",
            "ascending", "descending", "asc", "desc", "increasing", "decreasing"
        ]
        
        # Indicators for limiting results
        self.limit_keywords = [
            "limit", "top", "only", "just", "first", "last", "latest", "recent",
            "most recent", "newest", "oldest"
        ]
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data to extract query intent and components.
        
        Args:
            input_data (Dict[str, Any]): Input data including user query and schema
            
        Returns:
            Dict[str, Any]: Results including intent information
        """
        # Validate input
        if not self.validate_input(input_data, ["user_query", "schema_info"]):
            return {
                "success": False,
                "error": "Missing required query or schema information",
                "intent_info": {}
            }
        
        user_query = input_data["user_query"]
        schema_info = input_data["schema_info"]
        conversation_history = input_data.get("conversation_history", [])
        
        try:
            # Extract intent using pattern matching
            simple_intent = self._extract_simple_intent(user_query)
            
            # Extract intent using LLM
            llm_intent = self._extract_llm_intent(user_query, schema_info, conversation_history)
            
            # Merge results, preferring LLM results but falling back to pattern matching
            intent_info = self._merge_intent_results(simple_intent, llm_intent)
            
            # Store intent in state
            self.update_state({"intent_info": intent_info})
            
            # Return success
            result = {
                "success": True,
                "intent_info": intent_info,
                "operation": intent_info["operation"],
                "inferred_tables": intent_info["tables"],
                "inferred_columns": intent_info["columns"],
                "inferred_filters": intent_info["filters"],
                "requires_aggregation": intent_info["requires_aggregation"]
            }
            
            self.log_result(result)
            return result
            
        except Exception as e:
            logger.exception(f"Error in IntentAgent: {str(e)}")
            return {
                "success": False,
                "error": f"Intent extraction error: {str(e)}",
                "intent_info": {}
            }
    
    def _extract_simple_intent(self, query: str) -> Dict[str, Any]:
        """
        Extract basic intent using pattern matching.
        
        Args:
            query (str): Natural language query
            
        Returns:
            Dict[str, Any]: Basic intent information
        """
        query_lower = query.lower()
        
        # Determine operation type
        operation = "select"  # Default operation
        for op, keywords in self.operation_keywords.items():
            for keyword in keywords:
                if keyword in query_lower.split():
                    operation = op
                    break
        
        # Check for aggregation
        requires_aggregation = False
        for agg_word in self.aggregation_keywords:
            if agg_word in query_lower:
                requires_aggregation = True
                break
        
        # Check for filtering
        has_filters = False
        filters = []
        for filter_word in self.filter_keywords:
            if filter_word in query_lower:
                has_filters = True
                # Extract the filter condition (simplified)
                parts = query_lower.split(filter_word, 1)
                if len(parts) > 1:
                    filter_text = parts[1].strip().split(".")[0].strip()
                    filters.append(filter_text)
        
        # Check for grouping
        has_grouping = False
        for group_word in self.groupby_keywords:
            if group_word in query_lower:
                has_grouping = True
                break
        
        # Check for ordering
        has_ordering = False
        for order_word in self.orderby_keywords:
            if order_word in query_lower:
                has_ordering = True
                break
        
        # Check for limiting
        has_limit = False
        for limit_word in self.limit_keywords:
            if limit_word in query_lower.split():
                has_limit = True
                break
        
        return {
            "operation": operation,
            "requires_aggregation": requires_aggregation,
            "has_filters": has_filters,
            "filters": filters,
            "has_grouping": has_grouping,
            "has_ordering": has_ordering,
            "has_limit": has_limit,
            "tables": [],  # Will be inferred by LLM
            "columns": []  # Will be inferred by LLM
        }
    
    def _extract_llm_intent(self, query: str, schema_info: Dict[str, Any], 
                           conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract advanced intent using LLM.
        
        Args:
            query (str): Natural language query
            schema_info (Dict[str, Any]): Database schema information
            conversation_history (List[Dict[str, Any]]): Previous conversation
            
        Returns:
            Dict[str, Any]: Advanced intent information from LLM
        """
        # Prepare list of tables for context
        tables_context = ""
        if "tables" in schema_info:
            tables_list = list(schema_info["tables"].keys())
            tables_context = f"Available tables: {', '.join(tables_list)}\n\n"
            
            # Add a sample of columns for each table
            for table_name, table_info in schema_info["tables"].items():
                if "columns" in table_info:
                    col_names = list(table_info["columns"].keys())
                    if len(col_names) > 5:
                        sample_cols = col_names[:5]
                        tables_context += f"Table '{table_name}' columns include: {', '.join(sample_cols)} and others.\n"
                    else:
                        tables_context += f"Table '{table_name}' columns: {', '.join(col_names)}.\n"
        
        # Prepare the prompt for the LLM
        prompt = f"""
You are a database query analyzer. Analyze the following query and extract key components.
Respond with JSON only, no explanation.

{tables_context}

User query: "{query}"

Extract the following information:
1. The SQL operation type (SELECT, INSERT, UPDATE, DELETE)
2. The likely tables involved
3. The likely columns needed
4. Any filters or conditions
5. Whether aggregation is needed
6. Any grouping required
7. Any sorting required
8. Any limit on results

Response format:
{{
  "operation": "select|insert|update|delete",
  "tables": ["table1", "table2"],
  "columns": ["col1", "col2"],
  "filters": ["condition1", "condition2"],
  "requires_aggregation": true|false,
  "aggregation_type": "count|sum|avg|etc.",
  "group_by": ["col1"],
  "order_by": [{{"column": "col1", "direction": "asc|desc"}}],
  "limit": number|null
}}
"""
        
        try:
            # Get response from LLM
            response = get_gemini_response(prompt, response_format="json")
            
            # If response is not valid JSON, try to extract it
            if isinstance(response, str):
                try:
                    # Find JSON content if it's embedded in a larger response
                    import json
                    import re
                    
                    # Look for content between curly braces
                    match = re.search(r'({.*})', response, re.DOTALL)
                    if match:
                        response = json.loads(match.group(1))
                    else:
                        raise ValueError("Could not extract JSON from response")
                        
                except Exception as e:
                    logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                    # Fallback to simple intent extraction if LLM fails
                    return {
                        "operation": "select",
                        "tables": [],
                        "columns": [],
                        "filters": [],
                        "requires_aggregation": False,
                        "aggregation_type": None,
                        "group_by": [],
                        "order_by": [],
                        "limit": None
                    }
            
            # Ensure all required fields are present
            required_fields = [
                "operation", "tables", "columns", "filters", 
                "requires_aggregation", "group_by", "order_by"
            ]
            
            for field in required_fields:
                if field not in response:
                    response[field] = [] if field in ["tables", "columns", "filters", "group_by", "order_by"] else (
                        False if field == "requires_aggregation" else None
                    )
            
            return response
            
        except Exception as e:
            logger.exception(f"Error calling LLM for intent extraction: {str(e)}")
            # Return basic intent information as fallback
            return {
                "operation": "select",
                "tables": [],
                "columns": [],
                "filters": [],
                "requires_aggregation": False,
                "aggregation_type": None,
                "group_by": [],
                "order_by": [],
                "limit": None
            }
    
    def _merge_intent_results(self, simple_intent: Dict[str, Any], 
                             llm_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge results from simple pattern matching and LLM extraction.
        
        Args:
            simple_intent (Dict[str, Any]): Intent from pattern matching
            llm_intent (Dict[str, Any]): Intent from LLM
            
        Returns:
            Dict[str, Any]: Merged intent information
        """
        # Start with LLM results as they're likely more accurate
        merged = dict(llm_intent)
        
        # Fall back to simple results if LLM didn't provide certain fields
        if not merged.get("operation"):
            merged["operation"] = simple_intent["operation"]
        
        if not merged.get("requires_aggregation"):
            merged["requires_aggregation"] = simple_intent["requires_aggregation"]
        
        if not merged.get("filters") and simple_intent.get("filters"):
            merged["filters"] = simple_intent["filters"]
        
        # Normalize operation to lowercase
        if "operation" in merged:
            merged["operation"] = merged["operation"].lower()
        
        # Ensure all expected fields exist
        expected_fields = [
            "operation", "tables", "columns", "filters", 
            "requires_aggregation", "has_filters", "has_grouping", 
            "has_ordering", "has_limit"
        ]
        
        for field in expected_fields:
            if field not in merged:
                if field in ["tables", "columns", "filters"]:
                    merged[field] = []
                elif field.startswith("has_"):
                    merged[field] = False
                elif field == "requires_aggregation":
                    merged[field] = False
                else:
                    merged[field] = None
        
        # Derive has_* fields from more detailed LLM output
        merged["has_filters"] = len(merged["filters"]) > 0
        merged["has_grouping"] = len(merged.get("group_by", [])) > 0
        merged["has_ordering"] = len(merged.get("order_by", [])) > 0
        merged["has_limit"] = merged.get("limit") is not None
        
        return merged 
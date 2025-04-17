"""
Reflection adapter tool for the LangGraph SQL generation system.

This tool implements SQL query reflection and validation functionality,
which is a key new component in the LangGraph workflow system.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from langchain.chat_models import ChatOpenAI

from ..config import get_reflection_model

logger = logging.getLogger(__name__)


class ReflectionTool:
    """
    Tool for reflecting on and validating SQL queries.
    
    Analyzes SQL queries for correctness and potential issues,
    and provides feedback for improvement.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the reflection tool.
        
        Args:
            model_name: Name of the LLM to use for reflection
        """
        # Use the provided model or get from config
        self.model_name = model_name or get_reflection_model()
        self.llm = ChatOpenAI(model_name=self.model_name, temperature=0)
        self._timestamp = None
        
    async def reflect_on_sql(
        self, 
        sql_query: str,
        user_query: str,
        schema_info: Dict[str, Any],
        intent_info: Dict[str, Any],
        validated_columns: Dict[str, Dict[str, Any]] = None,
        previous_feedback: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Reflect on the generated SQL to identify issues and suggest improvements.
        
        Args:
            sql_query: The generated SQL query
            user_query: The original user query
            schema_info: Database schema information
            intent_info: User intent information
            validated_columns: Validated column information
            previous_feedback: Previous reflection feedback
            
        Returns:
            Reflection feedback including issues and suggestions
        """
        self._timestamp = time.time()
        
        try:
            # Check for empty SQL
            if not sql_query.strip():
                return {
                    "issues": ["SQL query is empty"],
                    "suggestions": ["Generate a valid SQL query"],
                    "needs_regeneration": True,
                    "revision_focus": "complete_rewrite"
                }
                
            # Construct the reflection prompt
            reflection_prompt = self._build_reflection_prompt(
                sql_query=sql_query,
                user_query=user_query,
                schema_info=schema_info,
                intent_info=intent_info,
                validated_columns=validated_columns or {},
                previous_feedback=previous_feedback or []
            )
            
            # Get reflection from LLM
            reflection_response = await self.llm.ainvoke(reflection_prompt)
            reflection_content = reflection_response.content
            
            # Parse reflection response
            reflection_result = self._parse_reflection_response(reflection_content)
            
            # Add metadata
            reflection_result["meta"] = {
                "timestamp": self._timestamp,
                "previous_feedback_count": len(previous_feedback or [])
            }
            
            return reflection_result
            
        except Exception as e:
            logger.error("Error in SQL reflection: %s", str(e), exc_info=True)
            return {
                "issues": [f"Error during reflection: {str(e)}"],
                "suggestions": ["Try regenerating the SQL query"],
                "needs_regeneration": True,
                "revision_focus": "error_recovery"
            }
            
    def _build_reflection_prompt(
        self,
        sql_query: str,
        user_query: str,
        schema_info: Dict[str, Any],
        intent_info: Dict[str, Any],
        validated_columns: Dict[str, Dict[str, Any]],
        previous_feedback: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Build the reflection prompt for the LLM.
        
        Args:
            sql_query: The generated SQL query
            user_query: The original user query
            schema_info: Database schema information
            intent_info: User intent information
            validated_columns: Validated column information
            previous_feedback: Previous reflection feedback
            
        Returns:
            Formatted prompt for the LLM
        """
        # Format schema information
        schema_str = "Tables:\n"
        for table_name, table_info in schema_info.get("table_schemas", {}).items():
            schema_str += f"- {table_name}\n  Columns: {', '.join(table_info.get('columns', []))}\n"
            
        # Format relationships
        relationships_str = "Relationships:\n"
        for rel in schema_info.get("relationships", []):
            relationships_str += f"- {rel.get('table1')}.{rel.get('column1')} -> {rel.get('table2')}.{rel.get('column2')}\n"
            
        # Format previous feedback
        previous_feedback_str = ""
        if previous_feedback:
            previous_feedback_str = "Previous feedback:\n"
            for i, feedback in enumerate(previous_feedback):
                previous_feedback_str += f"Iteration {i+1}:\n"
                previous_feedback_str += f"- Issues: {', '.join(feedback.get('issues', []))}\n"
                previous_feedback_str += f"- Suggestions: {', '.join(feedback.get('suggestions', []))}\n"
                
        # Build the system prompt
        system_prompt = """You are an expert SQL validator. Your task is to carefully analyze a SQL query and determine if it correctly addresses the user's question and follows best practices. You should check for:

1. Correctness: Does the SQL accurately translate the user's intent?
2. Schema compliance: Does it use valid tables and columns?
3. Joins: Are the necessary tables joined correctly?
4. Filters: Are the filter conditions appropriate?
5. SQL syntax: Are there any syntax errors?
6. Performance: Are there obvious performance issues?

Provide your analysis in a structured JSON format with the following fields:
- issues: List of identified issues (empty if none)
- suggestions: List of suggestions to improve the query
- needs_regeneration: Boolean indicating if the SQL needs to be regenerated
- revision_focus: String indicating what aspect needs most attention (schema, joins, filters, etc.)
"""

        # Create the messages for the chat prompt
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
User question: {user_query}

Generated SQL query:
```sql
{sql_query}
```

Database Schema Information:
{schema_str}

{relationships_str}

Intent Information:
- Query type: {intent_info.get('query_type', 'select')}
- Entities: {', '.join(intent_info.get('entities', []))}
- Filters: {', '.join(str(f) for f in intent_info.get('filters', []))}
- Aggregations: {', '.join(intent_info.get('aggregations', []))}

{previous_feedback_str}

Analyze this SQL query against the user's question and the schema.
Is it correct and optimal? What issues do you find? Does it need to be regenerated?
Return your analysis in the specified JSON format.
"""}
        ]
        
    def _parse_reflection_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse the reflection response from the LLM.
        
        Args:
            response_content: Raw response from the LLM
            
        Returns:
            Structured reflection data
        """
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON pattern in the response
            json_match = re.search(r'({[\s\S]*})', response_content)
            if json_match:
                json_str = json_match.group(1)
                reflection_data = json.loads(json_str)
                
                # Ensure required fields are present
                reflection_data.setdefault("issues", [])
                reflection_data.setdefault("suggestions", [])
                reflection_data.setdefault("needs_regeneration", False)
                reflection_data.setdefault("revision_focus", "")
                
                return reflection_data
            else:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse JSON from reflection response")
                return {
                    "issues": ["Failed to parse reflection response"],
                    "suggestions": ["Retry reflection"],
                    "needs_regeneration": False,
                    "revision_focus": "parsing_error"
                }
        except Exception as e:
            logger.error("Error parsing reflection response: %s", str(e), exc_info=True)
            return {
                "issues": ["Error parsing reflection response"],
                "suggestions": ["Retry reflection"],
                "needs_regeneration": False,
                "revision_focus": "parsing_error"
            }
            
    def get_timestamp(self) -> float:
        """
        Get the timestamp of the last reflection.
        
        Returns:
            Timestamp of last execution or current time if not executed
        """
        return self._timestamp or time.time() 
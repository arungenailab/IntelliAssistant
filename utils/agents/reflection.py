"""
ReflectionAgent: An agent that analyzes SQL queries for correctness and potential improvements.

This agent reviews a generated SQL query against the original natural language query,
schema information, and intent analysis to provide feedback and suggestions for improvement.
"""

import logging
from typing import Dict, Any, List, Optional
import json

from ..config import get_llm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReflectionAgent:
    """
    An agent that reflects on SQL queries to ensure they correctly address
    the original natural language query.
    """
    
    def __init__(self):
        """Initialize the reflection agent."""
        self.llm = get_llm()
        logger.info("ReflectionAgent initialized")
    
    async def reflect_on_query(
        self,
        natural_language_query: str,
        sql_query: str,
        schema_info: Dict[str, Any],
        intent_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reflect on a generated SQL query and provide feedback.
        
        Args:
            natural_language_query: The original natural language query
            sql_query: The generated SQL query to reflect on
            schema_info: Information about the database schema
            intent_analysis: Results from intent analysis
            
        Returns:
            A dictionary containing reflection feedback and improvement suggestions
        """
        try:
            logger.info(f"Reflecting on SQL query: {sql_query[:100]}...")
            
            # Create a concise schema representation
            schema_summary = self._summarize_schema(schema_info)
            
            # Create the prompt for reflection
            prompt = self._create_reflection_prompt(
                natural_language_query,
                sql_query,
                schema_summary,
                intent_analysis
            )
            
            # Get reflection from LLM
            reflection_response = await self._get_reflection(prompt)
            
            # Parse the reflection response
            reflection_feedback = self._parse_reflection(reflection_response)
            
            return reflection_feedback
            
        except Exception as e:
            logger.error(f"Error during SQL reflection: {str(e)}")
            return {
                "error": str(e),
                "needs_improvement": False,
                "feedback": "An error occurred during reflection."
            }
    
    def _summarize_schema(self, schema_info: Dict[str, Any]) -> str:
        """Create a concise summary of the schema for the reflection prompt."""
        tables = schema_info.get("tables", {})
        schema_summary = []
        
        for table_name, table_info in tables.items():
            columns = table_info.get("columns", {})
            primary_key = table_info.get("primary_key", [])
            foreign_keys = table_info.get("foreign_keys", {})
            
            column_details = []
            for column_name, column_info in columns.items():
                column_type = column_info.get("type", "unknown")
                nullable = "NULL" if column_info.get("nullable", True) else "NOT NULL"
                pk_marker = "PRIMARY KEY" if column_name in primary_key else ""
                column_details.append(f"{column_name} {column_type} {nullable} {pk_marker}".strip())
            
            fk_details = []
            for fk_column, fk_info in foreign_keys.items():
                ref_table = fk_info.get("referenced_table", "")
                ref_column = fk_info.get("referenced_column", "")
                fk_details.append(f"FOREIGN KEY ({fk_column}) REFERENCES {ref_table}({ref_column})")
            
            table_summary = f"Table: {table_name}\n"
            table_summary += "Columns:\n" + "\n".join([f"  - {col}" for col in column_details])
            
            if fk_details:
                table_summary += "\nForeign Keys:\n" + "\n".join([f"  - {fk}" for fk in fk_details])
            
            schema_summary.append(table_summary)
        
        return "\n\n".join(schema_summary)
    
    def _create_reflection_prompt(
        self,
        natural_language_query: str,
        sql_query: str,
        schema_summary: str,
        intent_analysis: Dict[str, Any]
    ) -> str:
        """Create a prompt for the reflection LLM."""
        # Extract intent analysis information
        tables_needed = intent_analysis.get("tables_needed", [])
        columns_needed = intent_analysis.get("columns_needed", [])
        filters_needed = intent_analysis.get("filters", [])
        operations = intent_analysis.get("operations", [])
        
        # Format intent information
        intent_info = f"""
        Tables needed: {', '.join(tables_needed)}
        Columns needed: {', '.join(columns_needed)}
        Filters: {', '.join(filters_needed) if filters_needed else 'None specified'}
        Operations: {', '.join(operations) if operations else 'None specified'}
        """
        
        # Create the full prompt
        prompt = f"""
        # SQL Query Reflection Task

        You are an expert SQL reviewer. Analyze the SQL query for correctness, efficiency, and completeness.
        
        ## Original Natural Language Query
        {natural_language_query}
        
        ## Generated SQL Query
        ```sql
        {sql_query}
        ```
        
        ## Database Schema Information
        {schema_summary}
        
        ## Intent Analysis
        {intent_info}
        
        ## Instructions
        Please review the SQL query and provide structured feedback covering the following aspects:
        
        1. **Correctness**: Does the SQL query correctly address the natural language question? Are there any syntax errors?
        2. **Tables and Joins**: Are all necessary tables included? Are the joins correctly implemented?
        3. **Columns**: Are all required columns selected? Are any columns missing or extraneous?
        4. **Filters**: Are the WHERE conditions appropriate for the question?
        5. **Aggregations**: If needed, are GROUP BY and aggregation functions used correctly?
        6. **Ordering**: Is the result ordered appropriately (if needed)?
        7. **Improvement Areas**: What specific changes would make the query more accurate or efficient?
        
        ## Response Format
        Your response should be a valid JSON object with the following structure:
        ```json
        {{
            "needs_improvement": true/false,
            "correctness_score": 1-10,
            "strengths": ["strength1", "strength2", ...],
            "issues": [
                {{
                    "issue_type": "correctness|tables|joins|columns|filters|aggregations|ordering",
                    "description": "Description of the issue",
                    "suggestion": "Suggested fix"
                }}
            ],
            "feedback": "Overall feedback on the query",
            "improved_query": "Improved SQL query if needed"
        }}
        ```
        
        The JSON must be valid and follow this exact format. Do not include any explanation outside of the JSON.
        """
        
        return prompt
    
    async def _get_reflection(self, prompt: str) -> str:
        """Get reflection from the LLM."""
        response = await self.llm.agenerate(
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content
    
    def _parse_reflection(self, reflection_text: str) -> Dict[str, Any]:
        """Parse the reflection response into a structured format."""
        try:
            # Extract JSON from the response (the LLM might add extra text)
            json_start = reflection_text.find("{")
            json_end = reflection_text.rfind("}")
            if json_start >= 0 and json_end >= 0:
                json_str = reflection_text[json_start:json_end+1]
                reflection_data = json.loads(json_str)
            else:
                # Fallback if JSON not found
                logger.warning("Could not extract JSON from reflection response")
                reflection_data = {
                    "needs_improvement": False,
                    "correctness_score": 7,
                    "strengths": ["Generated SQL looks generally reasonable"],
                    "issues": [],
                    "feedback": "Could not properly parse reflection response."
                }
            
            return reflection_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse reflection response: {str(e)}")
            return {
                "needs_improvement": False,
                "error": "Failed to parse reflection response",
                "raw_response": reflection_text
            }
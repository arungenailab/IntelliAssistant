"""
Reflection node for the LangGraph SQL generation system.

This module implements reflection on generated SQL queries to check for errors
and suggest improvements.
"""

import logging
import json
from typing import Dict, List, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import get_reflection_model

logger = logging.getLogger(__name__)

# Reflection prompt
REFLECTION_PROMPT = """You are a SQL expert tasked with verifying SQL queries for correctness and quality.

USER QUERY: {user_query}

DATABASE SCHEMA:
{schema_info}

GENERATED SQL QUERY:
```sql
{sql_query}
```

Please analyze this SQL query and provide feedback on its correctness and quality. Include:

1. OVERALL RATING (1-10): An overall score from 1-10
2. CORRECTNESS: Does the query correctly address the user's question? Will it run without syntax errors?
3. ISSUES: List any issues you identified (syntax, logic, schema mismatches, etc.)
4. SUGGESTIONS: Specific improvements to address each issue
5. IMPROVED_QUERY: Provide an improved version of the query if necessary

Your feedback should be thorough but concise, focusing on practical improvements.

Respond with a JSON object containing these sections.
"""


async def reflect_on_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reflect on the generated SQL query to identify potential issues and suggest improvements.
    
    This node:
    1. Takes the generated SQL query and schema information
    2. Uses an LLM to analyze the query for correctness and quality
    3. Updates the state with reflection feedback
    
    Args:
        state: The current graph state
        
    Returns:
        Updated state with reflection feedback
    """
    logger.info("Reflecting on SQL query")
    
    # Extract required information from state
    user_query = state.get("user_query", "")
    schema_info = state.get("schema_info", "No schema information available")
    sql_query = state.get("sql_query", "")
    
    # Skip reflection if no SQL query was generated
    if not sql_query:
        return {
            **state,
            "reflection_feedback": "No SQL query to reflect on.",
            "workflow_stage": "reflection_skipped"
        }
    
    try:
        # Initialize language model
        model = get_reflection_model()
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a SQL expert tasked with verifying SQL queries for correctness and quality."),
            HumanMessage(content=REFLECTION_PROMPT.format(
                user_query=user_query,
                schema_info=schema_info,
                sql_query=sql_query
            ))
        ])
        
        # Generate the reflection
        response = await model.ainvoke(prompt)
        reflection_text = response.content
        
        # Parse the JSON response
        try:
            reflection_data = json.loads(reflection_text)
        except json.JSONDecodeError:
            # Try to extract JSON if it's wrapped in text or code blocks
            import re
            json_match = re.search(r'{.*}', reflection_text, re.DOTALL)
            if json_match:
                try:
                    reflection_data = json.loads(json_match.group(0))
                except:
                    reflection_data = {
                        "OVERALL_RATING": 5,
                        "CORRECTNESS": "Undetermined",
                        "ISSUES": ["Failed to parse reflection output"],
                        "SUGGESTIONS": ["Review query manually"],
                        "IMPROVED_QUERY": sql_query
                    }
            else:
                reflection_data = {
                    "OVERALL_RATING": 5,
                    "CORRECTNESS": "Undetermined",
                    "ISSUES": ["Failed to parse reflection output"],
                    "SUGGESTIONS": ["Review query manually"],
                    "IMPROVED_QUERY": sql_query
                }
        
        logger.info(f"Reflection rating: {reflection_data.get('OVERALL_RATING', 'N/A')}")
        
        # Check if we need to regenerate the SQL
        rating = reflection_data.get("OVERALL_RATING", 5)
        needs_regeneration = rating < 7  # Consider regenerating if rating is below 7
        improved_query = reflection_data.get("IMPROVED_QUERY", "")
        
        # Use the improved query if provided and significantly different
        if improved_query and improved_query != sql_query:
            needs_regeneration = False  # No need to regenerate if we have an improved query
            sql_query = improved_query
            logger.info("Using improved query from reflection")
        
        # Update the state
        return {
            **state,
            "reflection_feedback": reflection_data,
            "sql_query": sql_query,
            "reflection_rating": rating,
            "needs_regeneration": needs_regeneration,
            "workflow_stage": "reflection_complete"
        }
        
    except Exception as e:
        error_msg = f"Failed to reflect on SQL query: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "reflection_feedback": {"error": error_msg},
            "workflow_stage": "reflection_error"
        } 
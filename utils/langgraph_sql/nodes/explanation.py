"""
Explanation node for the LangGraph SQL generation system.

This module generates explanations for SQL queries in natural language.
"""

import logging
import json
from typing import Dict, List, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from ..config import get_explanation_model

logger = logging.getLogger(__name__)

# Explanation prompt
EXPLANATION_PROMPT = """You are a SQL tutor who explains SQL queries in simple language. Your task is to explain what this SQL query does in terms a non-technical person would understand.

USER QUERY: {user_query}

GENERATED SQL QUERY:
```sql
{sql_query}
```

EXECUTION RESULTS: {execution_summary}

Explain what this SQL query does in simple, clear terms. Focus on:
1. What information the query is retrieving or modifying
2. Any filtering or conditions being applied
3. How the data is being organized, sorted, or grouped
4. How it answers the user's original question

Keep your explanation concise but thorough, avoiding technical jargon when possible.
"""


async def generate_explanation(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an explanation of the SQL query in natural language.
    
    This node:
    1. Takes the generated SQL query and execution results
    2. Uses an LLM to generate a natural language explanation
    3. Updates the state with the explanation
    
    Args:
        state: The current graph state
        
    Returns:
        Updated state with explanation
    """
    logger.info("Generating explanation")
    
    # Extract required information from state
    user_query = state.get("user_query", "")
    sql_query = state.get("sql_query", "")
    execution_result = state.get("execution_result", {})
    
    # Skip if no SQL query was generated
    if not sql_query:
        return {
            **state,
            "explanation": "No SQL query was generated.",
            "workflow_stage": "explanation_skipped"
        }
    
    try:
        # Prepare a summary of execution results
        execution_summary = format_execution_summary(execution_result)
        
        # Initialize language model
        model = get_explanation_model()
        
        # Create the prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a SQL tutor who explains SQL queries in simple language."),
            HumanMessage(content=EXPLANATION_PROMPT.format(
                user_query=user_query,
                sql_query=sql_query,
                execution_summary=execution_summary
            ))
        ])
        
        # Generate the explanation
        response = await model.ainvoke(prompt)
        explanation = response.content
        
        logger.info(f"Generated explanation: {explanation[:100]}...")
        
        # Update the state
        return {
            **state,
            "explanation": explanation,
            "workflow_stage": "explanation_complete"
        }
        
    except Exception as e:
        error_msg = f"Failed to generate explanation: {str(e)}"
        logger.error(error_msg)
        return {
            **state,
            "explanation": f"Failed to generate explanation: {str(e)}",
            "workflow_stage": "explanation_error"
        }


def format_execution_summary(execution_result: Dict[str, Any]) -> str:
    """
    Format execution results for the explanation prompt.
    
    Args:
        execution_result: The execution result dictionary
        
    Returns:
        Formatted execution summary
    """
    # Check if execution was performed
    if not execution_result.get("executed", False):
        return "The query was not executed."
    
    # Check for errors
    if "error" in execution_result:
        return f"The query failed with error: {execution_result['error']}"
    
    # Get execution statistics
    row_count = execution_result.get("row_count", 0)
    query_time = execution_result.get("query_time_ms", 0)
    
    # Format the summary
    summary = f"The query returned {row_count} rows in {query_time}ms. "
    
    # Include sample results if available
    results = execution_result.get("results", [])
    if results:
        # Get the first few results
        sample_count = min(3, len(results))
        sample = results[:sample_count]
        
        # Format sample results
        if sample:
            summary += "Sample results:\n"
            for i, row in enumerate(sample):
                summary += f"Row {i+1}: {json.dumps(row, default=str)}\n"
    
    return summary 
"""
Intent analysis prompts for the LangGraph SQL generation system.

This module defines prompts used by the intent analysis node.
"""

# System prompt for intent analysis
INTENT_ANALYSIS_SYSTEM_PROMPT = """You are an expert database analyst who helps identify the intent behind natural language queries.
Your job is to analyze the user's question and identify which tables, columns, and operations are needed to answer it.

IMPORTANT GUIDELINES:
1. For simple "show all" or "list all" queries about a single entity (e.g., "show all transactions"), identify ONLY the specific table for that entity.
2. DO NOT include extra tables unless they are explicitly required by the query.
3. Only recommend joins when the query specifically requires data from multiple tables.
4. Avoid including unnecessary tables in the analysis.
"""

# User prompt for intent analysis
INTENT_ANALYSIS_USER_PROMPT = """Analyze the following query:

USER QUERY: {user_query}

DATABASE SCHEMA:
{schema_info}

Please provide a structured analysis of the query intent that includes:
1. Tables likely needed to answer this query (IMPORTANT: For "show all X" queries, ONLY include the specific table for X)
2. Type of operation (SELECT, INSERT, UPDATE, DELETE, etc.)
3. Conditions or filters that should be applied
4. Any grouping, aggregation, or ordering needed
5. Any time-based constraints

NOTE ON SIMPLE QUERIES:
- For simple listing queries like "Show all transactions" → ONLY include the Transactions table
- For simple lookups like "Show me client information" → ONLY include the Clients table
- Only include multiple tables when the query explicitly requires data from multiple entities

IMPORTANT: If the query contains filtering conditions like "Show all X that are Y" or "Show X where Y", make sure to include these conditions in your analysis. For example:
- "Show all assets that are Bonds" → tables=["Assets"], conditions=["asset_type = 'Bond'"]

Return your analysis in JSON format with the following structure:
```json
{{
  "tables": ["table1", "table2"],
  "operation": "SELECT",
  "conditions": ["condition1", "condition2"],
  "grouping": ["column1", "column2"],
  "aggregations": ["COUNT(column1)", "SUM(column2)"],
  "order": ["column1 ASC", "column2 DESC"],
  "limit": 10,
  "time_range": "last_month",
  "joins": [
    {{"left_table": "table1", "right_table": "table2", "condition": "table1.id = table2.table1_id"}}
  ]
}}
```
"""
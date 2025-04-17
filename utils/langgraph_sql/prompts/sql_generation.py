"""
SQL generation prompts for the LangGraph SQL generation system.

This module defines prompts used by the SQL generation node.
"""

# SQL generation prompt
SQL_GENERATION_PROMPT = """You are an expert SQL query generator. Your task is to generate a SQL query that answers the user's question.

Database Schema:
{schema_info}

User Query: {user_query}

Intent Analysis:
{intent_analysis}

Generate a SQL query that exactly matches the user's intent. The SQL query should be:
1. Syntactically correct
2. Use the appropriate tables and columns from the schema
3. Include proper joins if multiple tables are involved
4. Follow best practices for SQL query writing

The query MUST be compatible with Microsoft SQL Server syntax.

Return ONLY the SQL query, without any explanations, wrapped in ```sql ```.""" 
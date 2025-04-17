"""
SQL Generation Utility

This module provides functionality to convert natural language queries to SQL
using large language models.
"""

import logging
import json
from typing import Dict, List, Any, Optional
import re

# Import AI helper
from utils.gemini_helper import get_gemini_client

logger = logging.getLogger(__name__)

def generate_sql_from_natural_language(
    user_query: str,
    schema_info: Dict[str, List[Dict[str, Any]]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Convert a natural language query to SQL using Gemini
    
    Args:
        user_query: The natural language query from the user
        schema_info: Dictionary mapping table names to their schema information
        conversation_history: Optional list of previous conversation messages
    
    Returns:
        Dict containing:
            - sql: The generated SQL query
            - explanation: A human-readable explanation of the SQL
            - confidence: Confidence score (0-1)
    """
    try:
        # Format schema information for the prompt
        schema_prompt = ""
        
        # Get list of available tables for the prompt
        available_tables = []
        
        # Handle both simple table list and full DDL structure
        if isinstance(schema_info, dict) and "tables" in schema_info:
            # This is the full DDL format with tables, relationships, indexes
            schema_prompt += "DATABASE TABLES AND COLUMNS:\n"
            available_tables = list(schema_info["tables"].keys())
            
            # First, display a clear list of all tables and their columns
            schema_prompt += "--- EXACT COLUMN NAMES FOR EACH TABLE ---\n"
            for table_name, columns in schema_info["tables"].items():
                column_names = [col.get('column_name', '') for col in columns]
                schema_prompt += f"Table '{table_name}' has ONLY these columns: {', '.join(column_names)}\n"
            schema_prompt += "\n"
            
            # Then provide detailed schema information
            schema_prompt += "--- DETAILED TABLE SCHEMAS ---\n"
            for table_name, columns in schema_info["tables"].items():
                schema_prompt += f"Table: {table_name}\n"
                schema_prompt += "Columns:\n"
                for col in columns:
                    # Handle both simple and detailed column information
                    col_name = col.get('column_name', '')
                    data_type = col.get('data_type', '')
                    is_pk = col.get('is_primary_key', 'NO')
                    is_nullable = col.get('is_nullable', '')
                    
                    pk_indicator = " (PRIMARY KEY)" if is_pk == 'YES' else ""
                    nullable_indicator = " NULL" if is_nullable == 'YES' else " NOT NULL"
                    
                    schema_prompt += f"  - {col_name} ({data_type}{pk_indicator}{nullable_indicator})\n"
                schema_prompt += "\n"
            
            # Add relationships if available
            if "relationships" in schema_info and schema_info["relationships"]:
                schema_prompt += "RELATIONSHIPS:\n"
                for rel in schema_info["relationships"]:
                    parent_table = rel.get('parent_table', '')
                    parent_col = rel.get('parent_column', '')
                    ref_table = rel.get('referenced_table', '')
                    ref_col = rel.get('referenced_column', '')
                    schema_prompt += f"  - {parent_table}.{parent_col} -> {ref_table}.{ref_col}\n"
                schema_prompt += "\n"
            
            # Add indexes if available
            if "indexes" in schema_info and schema_info["indexes"]:
                schema_prompt += "INDEXES:\n"
                for idx in schema_info["indexes"]:
                    table = idx.get('table_name', '')
                    index = idx.get('index_name', '')
                    column = idx.get('column_name', '')
                    is_unique = "UNIQUE " if idx.get('is_unique', 0) == 1 else ""
                    schema_prompt += f"  - {is_unique}INDEX {index} on {table}({column})\n"
                schema_prompt += "\n"
                
        else:
            # Simple table schema format
            schema_prompt += "DATABASE TABLES AND COLUMNS:\n"
            available_tables = list(schema_info.keys())
            
            # First, display a clear list of all tables and their columns
            schema_prompt += "--- EXACT COLUMN NAMES FOR EACH TABLE ---\n"
            for table_name, columns in schema_info.items():
                column_names = [col['column_name'] for col in columns]
                schema_prompt += f"Table '{table_name}' has ONLY these columns: {', '.join(column_names)}\n"
            schema_prompt += "\n"
            
            # Then provide detailed schema information
            schema_prompt += "--- DETAILED TABLE SCHEMAS ---\n"
            for table_name, columns in schema_info.items():
                schema_prompt += f"Table: {table_name}\n"
                schema_prompt += "Columns:\n"
                for col in columns:
                    schema_prompt += f"  - {col['column_name']} ({col['data_type']})\n"
                schema_prompt += "\n"
        
        # Include previous conversation for context if provided
        context_prompt = ""
        if conversation_history and len(conversation_history) > 0:
            context_prompt = "PREVIOUS CONVERSATION CONTEXT:\n"
            for i, msg in enumerate(conversation_history[-3:]):  # Use last 3 messages for context
                role = "User" if msg['role'] == 'user' else "Assistant"
                context_prompt += f"{role}: {msg['content']}\n"
            context_prompt += "\n"
        
        # Construct the prompt with clear emphasis on available tables
        prompt = f"""
You are an expert SQL query generator. Your task is to convert the following natural language query into a valid SQL query for SQL Server.

DATABASE SCHEMA:
{schema_prompt}

AVAILABLE TABLES AND THEIR COLUMNS:
{', '.join(available_tables)}

{context_prompt}USER QUERY:
"{user_query}"

CRITICAL INSTRUCTIONS (MUST FOLLOW EXACTLY):
1. You MUST ONLY use tables and columns that EXACTLY match what is listed in the schema above.
2. NEVER substitute column names with synonyms or similar terms - use the EXACT column names as shown.
3. COLUMN NAME VERIFICATION PROCESS (MANDATORY):
   a. For each column you plan to use, find it in the "EXACT COLUMN NAMES" section
   b. Copy-paste the exact column name - CHARACTER BY CHARACTER - from the schema
   c. Double-check spelling and casing of each column name against the schema
   d. If the user mentions a column that doesn't exist, do NOT use a similar name - use the closest ACTUAL column name
4. If you cannot find a real column that matches what the user is asking for, state this clearly in your explanation.
5. Every column in your SQL query MUST appear verbatim in the schema - no exceptions.

JOIN INSTRUCTIONS (CRUCIAL FOR MULTI-TABLE QUERIES):
1. SIMPLE QUERIES: For queries like "show all X" (e.g., "show all transactions"), start with ONLY that table. DO NOT include other tables unless specifically requested.
2. PROPER JOIN STRATEGY:
   a. Use the RELATIONSHIPS section to determine how tables are related
   b. Use appropriate joins (INNER JOIN, LEFT JOIN) based on these relationships
   c. AVOID CROSS JOINS except when no relationship exists and you need every combination
3. JOIN EXAMPLES:
   - GOOD: SELECT t.* FROM Transactions t INNER JOIN Portfolios p ON t.portfolio_id = p.id WHERE p.name = 'Growth'
   - BAD: SELECT * FROM Transactions CROSS JOIN Portfolios
4. FOR "SHOW ALL" PATTERNS:
   - "Show all transactions" → SELECT * FROM Transactions
   - NOT: SELECT * FROM Transactions CROSS JOIN Clients CROSS JOIN Portfolios

EXAMPLES:
✓ CORRECT: SELECT * FROM Transactions
✗ WRONG: SELECT * FROM Transactions CROSS JOIN Clients CROSS JOIN Portfolios (unnecessary joins)
✓ CORRECT: SELECT t.transaction_id, t.transaction_date, c.client_name FROM Transactions t INNER JOIN Clients c ON t.client_id = c.client_id
✗ WRONG: SELECT price FROM Transactions (using non-existent column names)

COMMON QUERY PATTERNS:
1. LISTING ENTITIES: 
   - "Show all transactions" → SELECT * FROM Transactions [LIMIT 100]
   - "List all clients" → SELECT * FROM Clients [LIMIT 100]
2. FILTERED QUERIES:
   - "Show transactions for client X" → Use appropriate JOINs with WHERE clauses
   - "Find assets with value > X" → Use proper column names and conditions
3. AGGREGATIONS:
   - "Total transaction amount by client" → Use GROUP BY with appropriate JOINs

VERIFICATION STEPS (REQUIRED):
1. After drafting your SQL, compare EVERY column name against the schema list
2. If any column is not an exact match to the schema, replace it with the correct name or remove it
3. If you can't find a suitable column, explain this in your response
4. VERIFY JOIN QUALITY:
   a. For "show all X" queries, check if you're using only the necessary tables
   b. Ensure you're using proper JOIN types based on relationships
   c. Only use CROSS JOIN when appropriate (rarely needed)
5. Check one final time that your query is efficient and matches the user's intent

Format your response as a JSON object with the following fields:
- sql: The SQL query (using ONLY columns that EXACTLY match the schema)
- explanation: A detailed explanation including your column verification steps
- confidence: A confidence score from 0.0 to 1.0 (use 0.0 if you're not confident the column names match)

JSON RESPONSE:
"""
        
        # Get Gemini client
        client = get_gemini_client()
        
        # Log the prompt for debugging
        logger.info(f"Sending prompt to Gemini: {prompt[:100]}...")
        
        # Generate the response
        response = client.generate_content(prompt)
        response_text = response.text
        
        # Parse the JSON response
        try:
            # Check if response is wrapped in a code block
            json_match = re.search(r'```(?:json)?\n([\s\S]*?)\n```', response_text)
            if json_match:
                # Extract the JSON content from inside the code block
                json_content = json_match.group(1).strip()
                result = json.loads(json_content)
            else:
                # Try parsing as raw JSON
                result = json.loads(response_text)
                
            # Ensure required fields are present
            if 'sql' not in result:
                result['sql'] = ""
            if 'explanation' not in result:
                result['explanation'] = "Could not generate explanation."
            if 'confidence' not in result:
                result['confidence'] = 0.5
                
            logger.info(f"Successfully generated SQL: {result['sql'][:100]}...")
            return result
        except json.JSONDecodeError:
            # If the response is not valid JSON, try to extract the SQL
            sql_match = re.search(r'```sql\n([\s\S]*?)\n```', response_text)
            if sql_match:
                sql = sql_match.group(1).strip()
                return {
                    'sql': sql,
                    'explanation': "Generated SQL from text response.",
                    'confidence': 0.6
                }
            else:
                logger.error(f"Failed to parse response as JSON: {response_text[:100]}...")
                return {
                    'sql': "",
                    'explanation': "Could not generate SQL from the natural language query.",
                    'confidence': 0.0
                }
                
    except Exception as e:
        logger.error(f"Error generating SQL: {str(e)}")
        return {
            'sql': "",
            'explanation': f"Error generating SQL: {str(e)}",
            'confidence': 0.0
        }

def enhance_sql_query(sql_query: str) -> Dict[str, Any]:
    """
    Analyze and enhance a SQL query for better performance and readability
    
    Args:
        sql_query: Original SQL query
        
    Returns:
        Dict containing:
            - enhanced_sql: Improved SQL query
            - explanation: Explanation of changes made
            - performance_tips: List of performance optimization tips
    """
    try:
        # Get Gemini client
        client = get_gemini_client()
        
        # Construct the prompt
        prompt = f"""
You are an expert SQL query optimizer. Analyze the following SQL query and suggest improvements for better performance and readability.

ORIGINAL SQL QUERY:
```sql
{sql_query}
```

INSTRUCTIONS:
1. Analyze the SQL query for performance issues and readability
2. Suggest an enhanced version of the query
3. Explain the changes you made
4. Provide performance optimization tips

Format your response as a JSON object with the following fields:
- enhanced_sql: The improved SQL query
- explanation: Explanation of changes made
- performance_tips: List of performance optimization tips

JSON RESPONSE:
"""
        
        # Generate the response
        response = client.generate_content(prompt)
        response_text = response.text
        
        # Parse the JSON response
        try:
            result = json.loads(response_text)
            # Ensure required fields are present
            if 'enhanced_sql' not in result:
                result['enhanced_sql'] = sql_query
            if 'explanation' not in result:
                result['explanation'] = "No enhancements suggested."
            if 'performance_tips' not in result:
                result['performance_tips'] = []
                
            return result
        except json.JSONDecodeError:
            return {
                'enhanced_sql': sql_query,
                'explanation': "Could not analyze query.",
                'performance_tips': []
            }
                
    except Exception as e:
        logger.error(f"Error enhancing SQL: {str(e)}")
        return {
            'enhanced_sql': sql_query,
            'explanation': "Error analyzing query.",
            'performance_tips': []
        }

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

INSTRUCTIONS:
1. ONLY use tables and columns that ACTUALLY EXIST in this database.
2. Refer to the "EXACT COLUMN NAMES FOR EACH TABLE" section at the beginning of the schema above.
3. Copy column names exactly as they appear in the schema, without any alteration.
4. REQUIRED VERIFICATION PROCESS - For each table you plan to use:
   a. Find the table in the "EXACT COLUMN NAMES" section
   b. Copy the exact column names from that section
   c. Verify each column name character-by-character
   d. Do not assume standard column names - use ONLY what's in the schema
5. If the user's query mentions a table or column that doesn't exist, use the closest matching alternative.
6. If you cannot map the query to existing columns, explain why rather than generating invalid SQL.
7. Provide a detailed explanation that explicitly lists all tables and columns you're using.

IMPORTANT NOTES ABOUT COLUMN NAMES:
- The 'Clients' table DOES NOT have an 'address' column
- The 'Clients' table has 'phone' (not 'phone_number')
- Always double-check schema above for EXACT column names

Column name verification example:
User query: "Show me all clients with their contact info"
Verification:
1. Tables: Clients
2. Available columns in Clients: client_id, last_name, first_name, email, created_date, phone
3. Creating SQL using only these exact column names: SELECT client_id, last_name, first_name, email, phone FROM Clients

Format your response as a JSON object with the following fields:
- sql: The SQL query (using ONLY tables and columns that exist in the schema)
- explanation: A detailed explanation including your column verification steps
- confidence: A confidence score from 0.0 to 1.0

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

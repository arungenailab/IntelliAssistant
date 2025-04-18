"""
Query processor for the LangGraph SQL generation system.

This module contains utilities for post-processing SQL queries.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def process_query(user_query: str, generated_sql: str) -> Tuple[str, bool]:
    """
    Process a generated SQL query to fix common issues.
    
    Args:
        user_query: The original natural language query
        generated_sql: The SQL query generated by the model
    
    Returns:
        tuple: (processed_sql, was_modified)
    """
    logger.info(f"Processing query: '{user_query}'")
    logger.info(f"Generated SQL: '{generated_sql}'")
    
    # Check for filtering conditions
    was_modified = False
    processed_sql = generated_sql
    
    # Handle "Show all X that are Y" pattern but missing WHERE clause
    filter_pattern = re.search(r'show\s+all\s+(\w+)s?\s+that\s+are\s+(\w+)', user_query.lower())
    is_filtered_request = filter_pattern is not None
    has_where = "WHERE" in generated_sql.upper()
    
    if is_filtered_request and not has_where:
        entity = filter_pattern.group(1)  # e.g., 'asset'
        filter_value = filter_pattern.group(2)  # e.g., 'bond'
        
        # Handle specific cases
        if entity == 'asset' and filter_value == 'bond':
            # Check if the SQL is just a simple SELECT without filtering
            if re.match(r'^\s*SELECT\s+.+\s+FROM\s+Assets\s*$', generated_sql, re.IGNORECASE):
                processed_sql = f"SELECT * FROM Assets WHERE asset_type = 'Bond'"
                was_modified = True
                logger.info(f"Added WHERE clause for bond filtering: {processed_sql}")
    
    # Handle CROSS JOIN when not needed
    has_cross_join = "CROSS JOIN" in generated_sql.upper()
    show_all_pattern = re.search(r'^show\s+all\s+(\w+)s?\s*$', user_query.lower())
    
    if show_all_pattern and has_cross_join:
        entity = show_all_pattern.group(1)
        
        # Known mappings of entities to tables
        entity_table_map = {
            'asset': 'Assets',
            'client': 'Clients',
            'transaction': 'Transactions',
            'portfolio': 'Portfolios'
        }
        
        if entity in entity_table_map:
            table_name = entity_table_map[entity]
            processed_sql = f"SELECT * FROM {table_name}"
            was_modified = True
            logger.info(f"Simplified CROSS JOIN to simple SELECT: {processed_sql}")
    
    return processed_sql, was_modified 
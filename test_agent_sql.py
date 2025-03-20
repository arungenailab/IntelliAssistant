#!/usr/bin/env python
"""
Test script for the agentic SQL generation system.
This script simulates a natural language query and tests the system's ability
to generate a valid SQL query.
"""

import os
import sys
import json
import logging
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the root directory to the path to allow importing modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the agent orchestrator
from utils.agents.orchestrator import AgentOrchestrator
from utils.sql_connector import SQLServerConnector

def run_test_query(query, connection_params, database_info=None):
    """
    Run a test query through the agentic system.
    
    Args:
        query (str): Natural language query
        connection_params (dict): Database connection parameters
        database_info (dict, optional): Database schema information
        
    Returns:
        dict: Result of the agentic process
    """
    logger.info(f"Testing query: '{query}'")
    
    # If database_info is not provided, fetch it from the database
    if not database_info and connection_params:
        connector = SQLServerConnector(connection_params)
        if connector.connect():
            try:
                logger.info("Fetching database schema...")
                database_info = connector.get_database_ddl()
                logger.info(f"Found {len(database_info.get('tables', {}))} tables")
            except Exception as e:
                logger.error(f"Error fetching schema: {str(e)}")
            finally:
                connector.disconnect()
    
    # Initialize the orchestrator
    orchestrator = AgentOrchestrator()
    
    # Process the query
    result = orchestrator.process_query(
        user_query=query,
        connection_params=connection_params,
        database_context=database_info
    )
    
    return result

def main():
    """Main function to run test cases"""
    # Define test cases
    test_cases = [
        {
            "name": "Simple SELECT query",
            "query": "Show me all customers from New York"
        },
        {
            "name": "Aggregation query",
            "query": "What is the total sales amount by product category?"
        },
        {
            "name": "JOIN query",
            "query": "List all orders with their customer names"
        },
        {
            "name": "Filter and sort",
            "query": "Show me the top 5 products by sales amount"
        },
        {
            "name": "Column name mismatch test",
            "query": "Show me the price and fees for all transactions"
        }
    ]
    
    # Load connection parameters from config or environment
    try:
        from config import SQL_SERVER_CONFIG
        connection_params = SQL_SERVER_CONFIG
    except ImportError:
        # If config not available, use example values
        connection_params = {
            "server": "AVDAILAB15-34\\SQLEXPRESS",
            "database": "fintest",
            "trusted_connection": "yes"
        }
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print(f"{'-'*80}")
        
        try:
            result = run_test_query(test_case["query"], connection_params)
            
            # Print results
            print(f"Success: {result['success']}")
            if result["error"]:
                print(f"Error: {result['error']}")
            
            print("\nGenerated SQL:")
            print(result["sql"] if result["sql"] else "No SQL generated")
            
            print("\nExplanation:")
            print(result["explanation"] if result["explanation"] else "No explanation provided")
            
            # Print any metadata
            if "metadata" in result and result["metadata"]:
                print("\nMetadata:")
                pprint(result["metadata"])
                
        except Exception as e:
            print(f"Error running test: {str(e)}")
    
    print(f"\n{'='*80}")
    print("Tests completed")

if __name__ == "__main__":
    main() 
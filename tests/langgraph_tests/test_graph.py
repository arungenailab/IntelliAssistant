"""
Test the LangGraph SQL generation system.

This module contains integration tests for the SQL generation graph.
"""

import unittest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

from utils.langgraph_sql.graph import SQLGenerationGraph, build_sql_gen_graph
from utils.langgraph_sql.state import SQLGenState, initialize_state


@patch('utils.langgraph_sql.nodes.schema_extraction.extract_schema')
@patch('utils.langgraph_sql.nodes.intent_analysis.analyze_intent')
@patch('utils.langgraph_sql.nodes.sql_generation.generate_sql')
@patch('utils.langgraph_sql.nodes.reflection.reflect_on_sql')
@patch('utils.langgraph_sql.nodes.execution.execute_sql')
@patch('utils.langgraph_sql.nodes.explanation.generate_explanation')
class TestGraphIntegration(unittest.TestCase):
    """Test case for the SQL generation graph."""
    
    def setUp(self):
        """Set up the test case."""
        self.test_query = "Get me customer information for customer 123"
        self.test_connection_params = {
            "server": "test_server",
            "database": "test_db",
            "username": "test_user",
            "password": "test_password"
        }
        self.test_schema_info = {
            "tables": {
                "customers": {
                    "columns": [
                        {"name": "customer_id", "type": "int"},
                        {"name": "first_name", "type": "varchar"},
                        {"name": "last_name", "type": "varchar"},
                        {"name": "email", "type": "varchar"}
                    ]
                }
            },
            "relationships": []
        }
        
    def test_graph_creation(self, mock_explain, mock_execute, mock_reflect, mock_generate, mock_analyze, mock_extract):
        """Test that the graph can be created."""
        # Act
        graph = build_sql_gen_graph()
        
        # Assert
        self.assertIsNotNone(graph)
        
    def test_initialize_state(self, mock_explain, mock_execute, mock_reflect, mock_generate, mock_analyze, mock_extract):
        """Test state initialization."""
        # Act
        state = initialize_state(
            user_query=self.test_query,
            connection_params=self.test_connection_params,
            schema_info=self.test_schema_info
        )
        
        # Assert
        self.assertIsNotNone(state)
        self.assertEqual(self.test_query, state["user_query"])
        self.assertEqual(self.test_connection_params, state["connection_params"])
        self.assertEqual(self.test_schema_info, state["schema_info"])
        
    @patch('langgraph.graph.StateGraph.compile')
    def test_graph_instance_creation(self, mock_compile, mock_explain, mock_execute, mock_reflect, mock_generate, mock_analyze, mock_extract):
        """Test that the graph instance can be created."""
        # Arrange
        mock_compiled_graph = MagicMock()
        mock_compile.return_value = mock_compiled_graph
        
        # Act
        graph_instance = SQLGenerationGraph(
            enable_reflection=True,
            enable_execution=False
        )
        
        # Assert
        self.assertIsNotNone(graph_instance)
        self.assertIsNotNone(graph_instance.graph)
        
    def test_graph_simple_flow(self, mock_explain, mock_execute, mock_reflect, mock_generate, mock_analyze, mock_extract):
        """Test a simplified flow through the graph."""
        # Arrange
        # Mock the extract_schema node
        mock_extract.return_value = {
            "user_query": self.test_query,
            "connection_params": self.test_connection_params,
            "schema_info": self.test_schema_info,
            "tables_used": ["customers"],
            "workflow_stage": "schema_extraction_complete"
        }
        
        # Mock the analyze_intent node
        mock_analyze.return_value = {
            "user_query": self.test_query,
            "connection_params": self.test_connection_params,
            "schema_info": self.test_schema_info,
            "tables_used": ["customers"],
            "intent_info": {"query_type": "select", "entities": ["customers"]},
            "workflow_stage": "intent_analysis_complete"
        }
        
        # Mock the generate_sql node
        mock_generate.return_value = {
            "user_query": self.test_query,
            "connection_params": self.test_connection_params,
            "schema_info": self.test_schema_info,
            "tables_used": ["customers"],
            "intent_info": {"query_type": "select", "entities": ["customers"]},
            "sql_query": "SELECT customer_id, first_name, last_name, email FROM customers WHERE customer_id = 123",
            "workflow_stage": "sql_generation_complete"
        }
        
        # Mock the reflect_on_sql node
        mock_reflect.return_value = {
            "user_query": self.test_query,
            "connection_params": self.test_connection_params,
            "schema_info": self.test_schema_info,
            "tables_used": ["customers"],
            "intent_info": {"query_type": "select", "entities": ["customers"]},
            "sql_query": "SELECT customer_id, first_name, last_name, email FROM customers WHERE customer_id = 123",
            "reflection_log": {"issues": [], "suggestions": []},
            "iteration_count": 1,
            "workflow_stage": "reflection_complete"
        }
        
        # Mock the execute_sql node
        mock_execute.return_value = {
            "user_query": self.test_query,
            "connection_params": self.test_connection_params,
            "schema_info": self.test_schema_info,
            "tables_used": ["customers"],
            "intent_info": {"query_type": "select", "entities": ["customers"]},
            "sql_query": "SELECT customer_id, first_name, last_name, email FROM customers WHERE customer_id = 123",
            "reflection_log": {"issues": [], "suggestions": []},
            "iteration_count": 1,
            "execution_result": {
                "executed": True,
                "success": True,
                "row_count": 1,
                "results": [{"customer_id": 123, "first_name": "John", "last_name": "Doe", "email": "john@example.com"}]
            },
            "workflow_stage": "execution_complete"
        }
        
        # Mock the generate_explanation node
        mock_explain.return_value = {
            "user_query": self.test_query,
            "connection_params": self.test_connection_params,
            "schema_info": self.test_schema_info,
            "tables_used": ["customers"],
            "intent_info": {"query_type": "select", "entities": ["customers"]},
            "sql_query": "SELECT customer_id, first_name, last_name, email FROM customers WHERE customer_id = 123",
            "reflection_log": {"issues": [], "suggestions": []},
            "iteration_count": 1,
            "execution_result": {
                "executed": True,
                "success": True,
                "row_count": 1,
                "results": [{"customer_id": 123, "first_name": "John", "last_name": "Doe", "email": "john@example.com"}]
            },
            "explanation": "This query retrieves customer information for customer ID 123.",
            "workflow_stage": "explanation_complete",
            "success": True
        }
        
        # Create a graph instance with mock graph
        graph_instance = SQLGenerationGraph(
            enable_reflection=True,
            enable_execution=True
        )
        
        # Override the compiled graph with a mock
        async_mock = AsyncMock()
        async_mock.ainvoke.return_value = {
            "user_query": self.test_query,
            "connection_params": self.test_connection_params,
            "schema_info": self.test_schema_info,
            "tables_used": ["customers"],
            "intent_info": {"query_type": "select", "entities": ["customers"]},
            "sql_query": "SELECT customer_id, first_name, last_name, email FROM customers WHERE customer_id = 123",
            "reflection_log": {"issues": [], "suggestions": []},
            "iteration_count": 1,
            "execution_result": {
                "executed": True,
                "success": True,
                "row_count": 1,
                "results": [{"customer_id": 123, "first_name": "John", "last_name": "Doe", "email": "john@example.com"}]
            },
            "explanation": "This query retrieves customer information for customer ID 123.",
            "workflow_stage": "explanation_complete",
            "success": True
        }
        graph_instance.graph = async_mock
        
        # Act
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(graph_instance.generate_sql(
            user_query=self.test_query,
            connection_params=self.test_connection_params,
            schema_info=self.test_schema_info
        ))
        loop.close()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result.get("success", False))
        self.assertEqual("SELECT customer_id, first_name, last_name, email FROM customers WHERE customer_id = 123", result.get("sql_query", ""))
        self.assertEqual("explanation_complete", result.get("workflow_stage", ""))
        self.assertIsNotNone(result.get("execution_result", None))
        self.assertEqual(1, result.get("execution_result", {}).get("row_count", 0))


if __name__ == '__main__':
    unittest.main() 
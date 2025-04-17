"""
Test the reflection node in the LangGraph SQL generation system.

This module contains tests for the SQL query reflection functionality.
"""

import unittest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

from utils.langgraph_sql.nodes.reflection import reflect_on_sql, format_schema_for_reflection


class TestReflection(unittest.TestCase):
    """Test case for the reflection functionality."""
    
    def setUp(self):
        """Set up the test case."""
        self.test_sql = "SELECT * FROM customers WHERE customer_id = 123"
        self.test_query = "Get me customer information for customer 123"
        self.test_schema = {
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
        self.test_intent = {
            "query_type": "select",
            "entities": ["customers"],
            "filters": ["customer_id = 123"]
        }
        
        self.test_state = {
            "user_query": self.test_query,
            "connection_params": {"server": "test", "database": "test"},
            "schema_info": self.test_schema,
            "tables_used": ["customers"],
            "intent_info": self.test_intent,
            "sql_query": self.test_sql,
            "iteration_count": 0
        }
        
    def test_format_schema_for_reflection(self):
        """Test schema formatting for reflection."""
        # Act
        formatted_schema = format_schema_for_reflection(self.test_schema, ["customers"])
        
        # Assert
        self.assertIsNotNone(formatted_schema)
        self.assertIn("customers", formatted_schema)
        self.assertIn("customer_id", formatted_schema)
        
    @patch('langchain_openai.ChatOpenAI')
    def test_reflection_empty_sql(self, mock_chat):
        """Test reflection with empty SQL."""
        # Arrange
        mock_chat.return_value = MagicMock()
        state = self.test_state.copy()
        state["sql_query"] = ""
        
        # Act
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(reflect_on_sql(state))
        loop.close()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("regenerate_sql", result)
        self.assertTrue(result.get("regenerate_sql", False))
        
    @patch('langchain_openai.ChatOpenAI')
    def test_reflection_with_valid_sql(self, mock_chat):
        """Test reflection with valid SQL."""
        # Arrange
        mock_invoke = AsyncMock()
        mock_invoke.return_value = MagicMock(content='{"issues": [], "suggestions": [], "regenerate_sql": false, "focus_area": ""}')
        mock_chat.return_value = MagicMock(ainvoke=mock_invoke)
        
        # Act
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(reflect_on_sql(self.test_state))
        loop.close()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("reflection_log", result)
        self.assertFalse(result.get("regenerate_sql", True))
        self.assertEqual(1, result.get("iteration_count", 0))
        
    @patch('langchain_openai.ChatOpenAI')
    def test_reflection_with_invalid_sql(self, mock_chat):
        """Test reflection with invalid SQL."""
        # Arrange
        mock_invoke = AsyncMock()
        mock_invoke.return_value = MagicMock(content='{"issues": ["Invalid table name"], "suggestions": ["Check table name"], "regenerate_sql": true, "focus_area": "schema"}')
        mock_chat.return_value = MagicMock(ainvoke=mock_invoke)
        
        # Act
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(reflect_on_sql(self.test_state))
        loop.close()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("reflection_log", result)
        self.assertIn("issues", result["reflection_log"])
        self.assertTrue(result.get("regenerate_sql", False))
        self.assertEqual("schema", result["reflection_log"].get("focus_area", ""))
        
    @patch('langchain_openai.ChatOpenAI')
    def test_max_iterations_reached(self, mock_chat):
        """Test reflection with max iterations reached."""
        # Arrange
        mock_invoke = AsyncMock()
        mock_invoke.return_value = MagicMock(content='{"issues": ["Issue"], "suggestions": ["Fix"], "regenerate_sql": true, "focus_area": "logic"}')
        mock_chat.return_value = MagicMock(ainvoke=mock_invoke)
        
        state = self.test_state.copy()
        state["iteration_count"] = 3  # Max iterations typically 3
        
        # Act
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(reflect_on_sql(state))
        loop.close()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("reflection_log", result)
        self.assertIn("Max iterations reached", str(result["reflection_log"]))
        self.assertFalse(result.get("regenerate_sql", True))  # Should not regenerate after max iterations


if __name__ == '__main__':
    unittest.main() 
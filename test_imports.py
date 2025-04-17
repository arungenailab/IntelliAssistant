"""
Test script to check if all required modules can be imported properly.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Testing imports...")

# Test core LangChain imports
try:
    import langchain
    import langchain_core
    from langchain_core.language_models import BaseChatModel
    logger.info(f"✓ LangChain imports successful")
except ImportError as e:
    logger.error(f"Failed to import LangChain: {e}")

# Test LangGraph imports
try:
    import langgraph
    from langgraph.graph import StateGraph, END
    logger.info(f"✓ LangGraph imports successful")
except ImportError as e:
    logger.error(f"Failed to import LangGraph: {e}")

# Test Google Gemini imports
try:
    import google.generativeai
    from langchain_google_genai import ChatGoogleGenerativeAI
    logger.info(f"✓ LangChain Google Genai imports successful")
except ImportError as e:
    logger.error(f"Failed to import Google Genai: {e}")

# Test our local imports
try:
    sys.path.insert(0, os.path.abspath('.'))
    from utils.langgraph_sql.config import is_langgraph_enabled
    enabled = is_langgraph_enabled()
    logger.info(f"✓ Local module imports successful")
    logger.info(f"LangGraph SQL enabled: {enabled}")
except ImportError as e:
    logger.error(f"Failed to import local modules: {e}")
    import traceback
    traceback.print_exc()

# Test StateGraph creation
try:
    from typing import Dict, Any
    graph = StateGraph(Dict[str, Any])
    logger.info(f"✓ StateGraph creation successful")
except Exception as e:
    logger.error(f"Failed to create StateGraph: {e}")
    import traceback
    traceback.print_exc()

logger.info("Import tests completed.")
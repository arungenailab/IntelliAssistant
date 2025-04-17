"""
Intent analysis adapter tool for the LangGraph SQL generation system.

This tool adapts the existing intent analysis functionality for use in the
LangGraph workflow system.
"""

import logging
import time
from typing import Dict, Any, List, Optional

# Import existing intent analysis functionality
from utils.agents.intent_agent import IntentAgent

logger = logging.getLogger(__name__)


class IntentAnalysisTool:
    """
    Tool for analyzing user query intent.
    
    Adapts the existing IntentAgent to work within the LangGraph workflow.
    """
    
    def __init__(self):
        """Initialize the intent analysis tool."""
        self.intent_agent = IntentAgent()
        self._timestamp = None
        
    async def analyze_intent(
        self, 
        query: str, 
        schema_info: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze the user query to extract intent and SQL requirements.
        
        Args:
            query: The natural language query from the user
            schema_info: Database schema information
            conversation_history: Previous conversation history
            
        Returns:
            Intent information extracted from the query
        """
        self._timestamp = time.time()
        
        try:
            # Call the existing intent agent
            intent_info = await self.intent_agent.analyze_intent(
                query=query,
                schema=schema_info,
                conversation_history=conversation_history or []
            )
            
            # Process and return in the expected format
            return {
                "query_type": intent_info.get("query_type", "select"),
                "entities": intent_info.get("entities", []),
                "filters": intent_info.get("filters", []),
                "aggregations": intent_info.get("aggregations", []),
                "joins": intent_info.get("joins", []),
                "sort": intent_info.get("sort", {}),
                "limit": intent_info.get("limit"),
                "meta": {
                    "confidence": intent_info.get("confidence", 0.0),
                    "analysis_method": "intent_agent",
                    "timestamp": self._timestamp
                }
            }
            
        except Exception as e:
            logger.error("Error in intent analysis: %s", str(e), exc_info=True)
            raise
            
    def get_timestamp(self) -> float:
        """
        Get the timestamp of the last analysis.
        
        Returns:
            Timestamp of last execution or current time if not executed
        """
        return self._timestamp or time.time() 
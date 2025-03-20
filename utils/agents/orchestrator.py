"""
Orchestrator module that coordinates the multi-agent system for SQL generation.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from utils.agents.base_agent import BaseAgent
from utils.agents.schema_agent import SchemaAgent
from utils.agents.intent_agent import IntentAgent
from utils.agents.column_agent import ColumnAgent
from utils.agents.sql_generator import SQLGeneratorAgent
from utils.agents.explanation_agent import ExplanationAgent

# Configure logging
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Orchestrator that coordinates the workflow between different agents
    to generate SQL from natural language queries.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the orchestrator with specialized agents.
        
        Args:
            config (Dict[str, Any], optional): Configuration for the orchestrator
        """
        self.config = config or {}
        
        # Initialize the specialized agents
        self.schema_agent = SchemaAgent("SchemaAgent", self.config)
        self.intent_agent = IntentAgent("IntentAgent", self.config)
        self.column_agent = ColumnAgent("ColumnAgent", self.config)
        self.sql_generator = SQLGeneratorAgent("SQLGeneratorAgent", self.config)
        self.explanation_agent = ExplanationAgent("ExplanationAgent", self.config)
        
        # Store conversation history
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Workflow stages
        self.workflow_stages = [
            ("schema_extraction", self.schema_agent),
            ("intent_analysis", self.intent_agent),
            ("column_validation", self.column_agent),
            ("sql_generation", self.sql_generator),
            ("explanation_generation", self.explanation_agent)
        ]
        
        logger.info("AgentOrchestrator initialized with all agents")
        
    def process_query(self, 
                     user_query: str, 
                     connection_params: Dict[str, Any],
                     database_context: Dict[str, Any] = None,
                     conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language query through the agent workflow.
        
        Args:
            user_query (str): Natural language query from the user
            connection_params (Dict[str, Any]): Database connection parameters
            database_context (Dict[str, Any], optional): Additional context about the database
            conversation_history (List[Dict[str, Any]], optional): Previous conversation history
            
        Returns:
            Dict[str, Any]: Result containing SQL query and other metadata
        """
        if not user_query:
            return {
                "success": False,
                "error": "Query cannot be empty",
                "sql": "",
                "explanation": "Please provide a valid query."
            }
        
        # Initialize the shared state for this query
        state = {
            "user_query": user_query,
            "connection_params": connection_params,
            "database_context": database_context or {},
            "conversation_history": conversation_history or [],
            "workflow_stage": "initialization",
            "success": True,
            "error": None,
            "sql": "",
            "explanation": "",
            "debug_info": {}
        }
        
        logger.info(f"Processing query: {user_query}")
        
        # Execute workflow stages
        try:
            for stage_name, agent in self.workflow_stages:
                if not state["success"]:
                    # Skip remaining stages if a previous stage failed
                    break
                
                logger.info(f"Executing workflow stage: {stage_name}")
                state["workflow_stage"] = stage_name
                
                # Process with the current agent
                result = agent.process(state)
                
                # Update the state with the agent's result
                state.update(result)
                
                # Add debug information
                state["debug_info"][stage_name] = {
                    "completed": state["success"],
                    "output": result
                }
                
                logger.info(f"Completed stage {stage_name} with success={state['success']}")
        
        except Exception as e:
            logger.exception(f"Error in workflow execution: {str(e)}")
            state.update({
                "success": False,
                "error": f"Internal processing error: {str(e)}",
                "workflow_stage": "error",
                "sql": "",
                "explanation": "An error occurred while processing your query. Please try again."
            })
        
        # Update conversation history
        self.update_conversation_history(user_query, state)
        
        # Return the final result
        return {
            "success": state["success"],
            "sql": state["sql"],
            "explanation": state["explanation"],
            "error": state["error"],
            "metadata": {
                "workflow_stage": state["workflow_stage"],
                "tables_used": state.get("tables_used", []),
                "columns_used": state.get("columns_used", [])
            }
        }
    
    def update_conversation_history(self, user_query: str, state: Dict[str, Any]) -> None:
        """
        Update the conversation history with the current query and result.
        
        Args:
            user_query (str): User's natural language query
            state (Dict[str, Any]): Current state after processing
        """
        history_entry = {
            "query": user_query,
            "sql": state["sql"],
            "success": state["success"],
            "timestamp": state.get("timestamp", None)
        }
        
        self.conversation_history.append(history_entry)
        
        # Limit history size
        max_history = self.config.get("max_conversation_history", 10)
        if len(self.conversation_history) > max_history:
            self.conversation_history = self.conversation_history[-max_history:]
    
    def get_debug_info(self) -> Dict[str, Any]:
        """
        Get debugging information about the agent workflow.
        Useful for troubleshooting.
        
        Returns:
            Dict[str, Any]: Debug information
        """
        return {
            "agents": [
                {
                    "name": self.schema_agent.name,
                    "state": self.schema_agent.get_state()
                },
                {
                    "name": self.intent_agent.name,
                    "state": self.intent_agent.get_state()
                },
                {
                    "name": self.column_agent.name,
                    "state": self.column_agent.get_state()
                },
                {
                    "name": self.sql_generator.name,
                    "state": self.sql_generator.get_state()
                },
                {
                    "name": self.explanation_agent.name,
                    "state": self.explanation_agent.get_state()
                }
            ],
            "conversation_history_length": len(self.conversation_history)
        }
    
    def reset(self) -> None:
        """
        Reset the orchestrator and all agents to their initial state.
        """
        for _, agent in self.workflow_stages:
            agent.clear_state()
        
        self.conversation_history = []
        logger.info("AgentOrchestrator and all agents have been reset") 
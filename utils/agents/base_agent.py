"""
Base Agent module that defines the interface for all agents in the system.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base abstract class for all agents in the system.
    All specialized agents should inherit from this class.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent with a name and optional configuration.
        
        Args:
            name (str): Name of the agent
            config (Dict[str, Any], optional): Configuration for the agent
        """
        self.name = name
        self.config = config or {}
        self.state: Dict[str, Any] = {}
        logger.info(f"Initialized {self.name} agent")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and return the result.
        
        Args:
            input_data (Dict[str, Any]): Input data for processing
            
        Returns:
            Dict[str, Any]: Results of the processing
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate that the input data contains all required fields.
        
        Args:
            input_data (Dict[str, Any]): Input data to validate
            required_fields (List[str]): List of required field names
            
        Returns:
            bool: True if all required fields are present, False otherwise
        """
        for field in required_fields:
            if field not in input_data:
                logger.error(f"{self.name}: Missing required field '{field}'")
                return False
        return True
    
    def log_result(self, result: Dict[str, Any]) -> None:
        """
        Log the result of the agent's processing.
        
        Args:
            result (Dict[str, Any]): The result to log
        """
        logger.debug(f"{self.name} result: {result}")
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """
        Update the agent's state with the provided updates.
        
        Args:
            updates (Dict[str, Any]): Updates to apply to the state
        """
        self.state.update(updates)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the agent.
        
        Returns:
            Dict[str, Any]: The agent's current state
        """
        return self.state.copy()
        
    def clear_state(self) -> None:
        """
        Clear the agent's state.
        """
        self.state = {} 
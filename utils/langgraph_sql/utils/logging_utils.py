"""
Logging utilities for the LangGraph SQL generation system.

This module provides logging utilities and helpers for the LangGraph SQL system.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any

# Configure logger
logger = logging.getLogger("langgraph_sql")


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging for the LangGraph SQL system.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, logs to console only)
        log_format: Custom log format string
        
    Returns:
        Configured logger
    """
    # Set default format if none provided
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
    # Configure formatter
    formatter = logging.Formatter(log_format)
    
    # Set level based on input
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure logger
    logger.setLevel(numeric_level)
    logger.handlers = []  # Clear existing handlers if any
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger


def log_state_transition(
    logger: logging.Logger,
    from_state: Dict[str, Any],
    to_state: Dict[str, Any],
    node_name: str
) -> None:
    """
    Log a state transition between graph nodes.
    
    Args:
        logger: Logger instance
        from_state: Original state
        to_state: New state
        node_name: Name of the node that performed the transition
    """
    # Extract workflow stage changes
    from_stage = from_state.get("workflow_stage", "unknown")
    to_stage = to_state.get("workflow_stage", "unknown")
    
    # Log basic transition
    logger.info(
        "State transition: %s -> %s (by node: %s)",
        from_stage,
        to_stage,
        node_name
    )
    
    # Log specific changes at debug level
    if logger.isEnabledFor(logging.DEBUG):
        # Find keys that changed
        changed_keys = []
        for key in to_state:
            if key in from_state:
                if to_state[key] != from_state[key]:
                    changed_keys.append(key)
            else:
                changed_keys.append(key)
                
        logger.debug("Changed keys: %s", changed_keys)
        
    # Log errors at warning level
    if not to_state.get("success", True):
        error_msg = to_state.get("error_message", "Unknown error")
        logger.warning("Error in state transition: %s", error_msg) 
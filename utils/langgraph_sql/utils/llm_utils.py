"""
LLM utility functions for the LangGraph SQL generation system.

This module provides utility functions for working with language models.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from ..config import get_generation_model, get_reflection_model

logger = logging.getLogger(__name__)


def get_llm_for_generation() -> BaseChatModel:
    """
    Get a language model for text generation tasks.
    
    Returns:
        Language model instance configured for generation
    """
    return get_generation_model()


def get_llm_for_reflection() -> BaseChatModel:
    """
    Get a language model for reflection tasks.
    
    Reflection models typically use lower temperature for more deterministic output.
    
    Returns:
        Language model instance configured for reflection
    """
    return get_reflection_model()


def format_conversation_history(
    conversation_history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Format conversation history for inclusion in prompts.
    
    Args:
        conversation_history: List of conversation messages
        
    Returns:
        Formatted conversation history string
    """
    if not conversation_history:
        return ""
    
    formatted = "CONVERSATION HISTORY:\n"
    
    for message in conversation_history:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        
        if role.lower() == "user":
            formatted += f"User: {content}\n"
        elif role.lower() in ["assistant", "ai"]:
            formatted += f"Assistant: {content}\n"
        else:
            formatted += f"{role.capitalize()}: {content}\n"
    
    return formatted


def format_messages_for_llm(
    messages: List[Union[BaseMessage, Dict[str, str]]]
) -> List[BaseMessage]:
    """
    Format messages for LLM input, converting dictionaries to BaseMessage objects if needed.
    
    Args:
        messages: List of messages (either BaseMessage objects or dictionaries)
        
    Returns:
        List of BaseMessage objects
    """
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    formatted_messages = []
    
    for message in messages:
        if isinstance(message, BaseMessage):
            formatted_messages.append(message)
        elif isinstance(message, dict):
            role = message.get("role", "").lower()
            content = message.get("content", "")
            
            if role == "user":
                formatted_messages.append(HumanMessage(content=content))
            elif role in ["assistant", "ai"]:
                formatted_messages.append(AIMessage(content=content))
            elif role == "system":
                formatted_messages.append(SystemMessage(content=content))
    
    return formatted_messages
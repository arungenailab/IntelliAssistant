"""
LangChain utility functions for the LangGraph SQL generation system.

This module provides utilities for working with LangChain components.
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any, Union, List, Callable
from langchain.chat_models import ChatOpenAI
from langchain.chat_models import ChatVertexAI, ChatGoogleGenerativeAI
from langchain.schema import BaseMessage

logger = logging.getLogger(__name__)


def get_chat_model(
    model_name: str,
    temperature: float = 0,
    model_kwargs: Optional[Dict[str, Any]] = None
) -> Union[ChatOpenAI, ChatVertexAI, ChatGoogleGenerativeAI]:
    """
    Get a chat model based on the specified model name and provider.
    
    Supports OpenAI, Google Vertex AI, and Google Gemini models.
    
    Args:
        model_name: Name of the model to use
        temperature: Sampling temperature
        model_kwargs: Additional keyword arguments for the model
        
    Returns:
        Configured chat model
    """
    model_kwargs = model_kwargs or {}
    
    # OpenAI models
    if model_name.startswith("gpt-"):
        return ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            **model_kwargs
        )
    
    # Google Vertex AI models
    elif model_name.startswith("vertex-"):
        # Extract the actual model name after the prefix
        vertex_model = model_name.replace("vertex-", "")
        return ChatVertexAI(
            model_name=vertex_model,
            temperature=temperature,
            **model_kwargs
        )
    
    # Google Gemini models
    elif model_name.startswith("gemini-"):
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            **model_kwargs
        )
    
    # Default to OpenAI if no prefix is specified
    else:
        logger.warning(
            "Model provider not specified in model name. Defaulting to OpenAI: %s",
            model_name
        )
        return ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            **model_kwargs
        )


def create_structured_chat_prompt(
    system_message: str,
    user_message: str,
    format_instructions: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Create a structured chat prompt with system and user messages.
    
    Args:
        system_message: System message content
        user_message: User message content
        format_instructions: Optional format instructions to append to system message
        
    Returns:
        List of message dictionaries for LangChain chat models
    """
    # Add format instructions if provided
    if format_instructions:
        system_message = f"{system_message}\n\n{format_instructions}"
    
    # Create the message list
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]


def create_retry_decorator(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0
) -> Callable:
    """
    Create a retry decorator for LLM calls.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay between retries (exponential backoff)
        max_delay: Maximum delay between retries
        
    Returns:
        Retry decorator function
    """
    import time
    import random
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(
                            "Max retries (%d) exceeded: %s", 
                            max_retries, str(e)
                        )
                        raise
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                    jitter = random.uniform(0.8, 1.2)
                    delay = delay * jitter
                    
                    logger.warning(
                        "Retry %d/%d after error: %s. Waiting %.2f seconds...",
                        retries, max_retries, str(e), delay
                    )
                    
                    await asyncio.sleep(delay)
                    
        return wrapper
    
    return decorator
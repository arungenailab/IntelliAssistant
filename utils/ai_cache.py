import json
import time
import hashlib
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_cache")

class AiCache:
    """
    Cache for AI responses to minimize redundant API calls,
    reduce costs, and improve response times.
    """
    
    def __init__(self, ttl_seconds=3600):  # Default TTL: 1 hour
        """
        Initialize the cache with a specified time-to-live for entries.
        
        Args:
            ttl_seconds: Time-to-live in seconds for cache entries
        """
        self.cache = {}
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, query: str, system_prompt: Optional[str] = None, 
                      model: Optional[str] = None, conversation_context: Optional[str] = None) -> str:
        """
        Generate a unique cache key based on the query and context.
        
        Args:
            query: The user query
            system_prompt: The system prompt provided to the model
            model: The model identifier
            conversation_context: A string representation of relevant conversation context
            
        Returns:
            A string hash representing the unique key
        """
        # Combine all relevant inputs
        key_content = {
            "query": query.strip().lower(),  # Normalize query
            "system_prompt": system_prompt,
            "model": model,
            "context": conversation_context
        }
        
        # Convert to string and hash
        key_str = json.dumps(key_content, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, query: str, system_prompt: Optional[str] = None, 
            model: Optional[str] = None, conversation_context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get data from cache if it exists and is not expired.
        
        Args:
            query: The user query
            system_prompt: The system prompt provided to the model
            model: The model identifier 
            conversation_context: A string representation of relevant conversation context
            
        Returns:
            Cached response or None if not found/expired
        """
        cache_key = self._generate_key(query, system_prompt, model, conversation_context)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check if entry is still valid
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                logger.info(f"AI cache hit for key: {cache_key[:8]}...")
                return entry["data"]
            else:
                logger.info(f"AI cache expired for key: {cache_key[:8]}...")
                del self.cache[cache_key]
        
        return None
    
    def set(self, query: str, response_data: Dict[str, Any], system_prompt: Optional[str] = None,
            model: Optional[str] = None, conversation_context: Optional[str] = None) -> None:
        """
        Store response in cache with current timestamp.
        
        Args:
            query: The user query
            response_data: The response data to cache
            system_prompt: The system prompt provided to the model
            model: The model identifier
            conversation_context: A string representation of relevant conversation context
        """
        cache_key = self._generate_key(query, system_prompt, model, conversation_context)
        
        self.cache[cache_key] = {
            "timestamp": time.time(),
            "data": response_data
        }
        
        logger.info(f"Cached AI response for key: {cache_key[:8]}...")
    
    def clear(self) -> None:
        """Clear all cached data."""
        self.cache = {}
        logger.info("AI cache cleared")
        
    def clear_expired(self) -> int:
        """
        Clear expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items() 
            if current_time - entry["timestamp"] >= self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired entries from AI cache")
            
        return len(expired_keys)

# Initialize global cache instance
ai_cache = AiCache() 
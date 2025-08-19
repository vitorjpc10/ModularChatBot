"""
Redis cache service for the Modular Chatbot application.
Handles caching for conversation history and simplified logging.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError

from .config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache service for conversation history and logging."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish Redis connection."""
        try:
            self.redis_client = redis.Redis.from_url(
                settings.REDIS_URL,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False
    
    def _reconnect_if_needed(self) -> None:
        """Reconnect to Redis if connection is lost."""
        if not self._is_connected():
            logger.warning("Redis connection lost, attempting to reconnect...")
            self._connect()
    
    # Conversation History Caching Methods
    
    def cache_conversation_history(
        self, 
        conversation_id: str, 
        messages: List[Dict[str, Any]], 
        ttl: int = 3600
    ) -> bool:
        """
        Cache conversation history.
        
        Args:
            conversation_id: Conversation identifier
            messages: List of message dictionaries
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            self._reconnect_if_needed()
            if not self._is_connected():
                return False
            
            key = f"conversation:{conversation_id}:history"
            data = {
                "messages": messages,
                "cached_at": datetime.utcnow().isoformat(),
                "message_count": len(messages)
            }
            
            self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(data, default=str)
            )
            
            logger.info(f"Cached conversation history for {conversation_id} with {len(messages)} messages")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to cache conversation history for {conversation_id}: {e}")
            return False
    
    def get_cached_conversation_history(
        self, 
        conversation_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached conversation history.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            List of message dictionaries or None if not found
        """
        try:
            self._reconnect_if_needed()
            if not self._is_connected():
                return None
            
            key = f"conversation:{conversation_id}:history"
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"Retrieved cached conversation history for {conversation_id}")
                return data.get("messages", [])
            
            return None
            
        except RedisError as e:
            logger.error(f"Failed to get cached conversation history for {conversation_id}: {e}")
            return None
    
    def invalidate_conversation_cache(self, conversation_id: str) -> bool:
        """
        Invalidate cached conversation history.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        try:
            self._reconnect_if_needed()
            if not self._is_connected():
                return False
            
            key = f"conversation:{conversation_id}:history"
            result = self.redis_client.delete(key)
            
            if result > 0:
                logger.info(f"Invalidated conversation cache for {conversation_id}")
                return True
            
            return False
            
        except RedisError as e:
            logger.error(f"Failed to invalidate conversation cache for {conversation_id}: {e}")
            return False
    
    def cache_conversation_metadata(
        self, 
        conversation_id: str, 
        metadata: Dict[str, Any], 
        ttl: int = 7200
    ) -> bool:
        """
        Cache conversation metadata (title, stats, etc.).
        
        Args:
            conversation_id: Conversation identifier
            metadata: Conversation metadata
            ttl: Time to live in seconds (default: 2 hours)
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            self._reconnect_if_needed()
            if not self._is_connected():
                return False
            
            key = f"conversation:{conversation_id}:metadata"
            data = {
                **metadata,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(data, default=str)
            )
            
            logger.info(f"Cached conversation metadata for {conversation_id}")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to cache conversation metadata for {conversation_id}: {e}")
            return False
    
    def get_cached_conversation_metadata(
        self, 
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached conversation metadata.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation metadata or None if not found
        """
        try:
            self._reconnect_if_needed()
            if not self._is_connected():
                return None
            
            key = f"conversation:{conversation_id}:metadata"
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"Retrieved cached conversation metadata for {conversation_id}")
                return data
            
            return None
            
        except RedisError as e:
            logger.error(f"Failed to get cached conversation metadata for {conversation_id}: {e}")
            return None
    
    # Simplified Logging Methods
    
    def cache_log_entry(
        self, 
        log_key: str, 
        log_data: Dict[str, Any], 
        ttl: int = 86400
    ) -> bool:
        """
        Cache a log entry for simplified logging.
        
        Args:
            log_key: Unique key for the log entry
            log_data: Log data dictionary
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            self._reconnect_if_needed()
            if not self._is_connected():
                return False
            
            key = f"log:{log_key}"
            data = {
                **log_data,
                "logged_at": datetime.utcnow().isoformat()
            }
            
            self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(data, default=str)
            )
            
            return True
            
        except RedisError as e:
            logger.error(f"Failed to cache log entry {log_key}: {e}")
            return False
    
    def get_cached_logs(
        self, 
        pattern: str = "log:*", 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get cached log entries by pattern.
        
        Args:
            pattern: Redis key pattern to search for
            limit: Maximum number of logs to return
            
        Returns:
            List of log entries
        """
        try:
            self._reconnect_if_needed()
            if not self._is_connected():
                return []
            
            keys = self.redis_client.keys(pattern)
            logs = []
            
            for key in keys[:limit]:
                try:
                    log_data = self.redis_client.get(key)
                    if log_data:
                        logs.append(json.loads(log_data))
                except (RedisError, json.JSONDecodeError):
                    continue
            
            return logs
            
        except RedisError as e:
            logger.error(f"Failed to get cached logs with pattern {pattern}: {e}")
            return []
    
    def cache_error_log(
        self, 
        error_type: str, 
        error_message: str, 
        context: Dict[str, Any] = None
    ) -> bool:
        """
        Cache an error log entry.
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context data
            
        Returns:
            True if cached successfully, False otherwise
        """
        log_data = {
            "type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        log_key = f"error:{error_type}:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        return self.cache_log_entry(log_key, log_data, ttl=604800)  # 7 days
    
    def cache_performance_log(
        self, 
        operation: str, 
        execution_time: float, 
        context: Dict[str, Any] = None
    ) -> bool:
        """
        Cache a performance log entry.
        
        Args:
            operation: Operation name
            execution_time: Execution time in seconds
            context: Additional context data
            
        Returns:
            True if cached successfully, False otherwise
        """
        log_data = {
            "type": "performance",
            "operation": operation,
            "execution_time": execution_time,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        log_key = f"perf:{operation}:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        return self.cache_log_entry(log_key, log_data, ttl=86400)  # 24 hours
    
    # Cache Management Methods
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get Redis cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            self._reconnect_if_needed()
            if not self._is_connected():
                return {"error": "Redis not connected"}
            
            info = self.redis_client.info()
            
            # Count keys by pattern
            conversation_keys = len(self.redis_client.keys("conversation:*"))
            log_keys = len(self.redis_client.keys("log:*"))
            error_keys = len(self.redis_client.keys("log:error:*"))
            perf_keys = len(self.redis_client.keys("log:perf:*"))
            
            stats = {
                "redis_info": {
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "total_commands_processed": info.get("total_commands_processed"),
                },
                "cache_counts": {
                    "conversation_keys": conversation_keys,
                    "log_keys": log_keys,
                    "error_keys": error_keys,
                    "performance_keys": perf_keys,
                    "total_keys": conversation_keys + log_keys
                }
            }
            
            return stats
            
        except RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
    
    def clear_expired_keys(self) -> int:
        """
        Clear expired keys from cache.
        
        Returns:
            Number of keys cleared
        """
        try:
            self._reconnect_if_needed()
            if not self._is_connected():
                return 0
            
            # This is a simplified approach - Redis automatically expires keys
            # but we can check for keys that might be stale
            cleared = 0
            
            # Check conversation keys older than 24 hours
            conversation_keys = self.redis_client.keys("conversation:*")
            for key in conversation_keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        parsed_data = json.loads(data)
                        cached_at = datetime.fromisoformat(parsed_data.get("cached_at", "1970-01-01T00:00:00"))
                        if datetime.utcnow() - cached_at > timedelta(hours=24):
                            self.redis_client.delete(key)
                            cleared += 1
                except (RedisError, json.JSONDecodeError, ValueError):
                    continue
            
            return cleared
            
        except RedisError as e:
            logger.error(f"Failed to clear expired keys: {e}")
            return 0


# Global cache instance
cache = RedisCache()

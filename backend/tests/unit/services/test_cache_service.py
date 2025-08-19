"""
Unit tests for Redis cache service.
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from app.cache import RedisCache


class TestRedisCache:
    """Test cases for Redis cache service."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.setex.return_value = True
        mock_client.get.return_value = None
        mock_client.delete.return_value = 1
        mock_client.keys.return_value = []
        mock_client.info.return_value = {
            "redis_version": "7.0.0",
            "connected_clients": 1,
            "used_memory_human": "1.0M",
            "total_commands_processed": 100
        }
        return mock_client
    
    @pytest.fixture
    def cache_service(self, mock_redis_client):
        """Create cache service with mocked Redis."""
        with patch('app.cache.redis.Redis.from_url', return_value=mock_redis_client):
            cache = RedisCache()
            return cache
    
    def test_cache_conversation_history(self, cache_service, mock_redis_client):
        """Test caching conversation history."""
        conversation_id = "test-conv-123"
        messages = [
            {"id": 1, "content": "Hello", "response": "Hi there!"},
            {"id": 2, "content": "How are you?", "response": "I'm doing well!"}
        ]
        
        result = cache_service.cache_conversation_history(conversation_id, messages)
        
        assert result is True
        mock_redis_client.setex.assert_called_once()
        
        # Verify the key and data structure
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == f"conversation:{conversation_id}:history"
        assert call_args[0][1] == 3600  # TTL
        
        # Verify data structure
        cached_data = json.loads(call_args[0][2])
        assert "messages" in cached_data
        assert "cached_at" in cached_data
        assert "message_count" in cached_data
        assert len(cached_data["messages"]) == 2
    
    def test_get_cached_conversation_history(self, cache_service, mock_redis_client):
        """Test retrieving cached conversation history."""
        conversation_id = "test-conv-123"
        cached_data = {
            "messages": [
                {"id": 1, "content": "Hello", "response": "Hi there!"}
            ],
            "cached_at": datetime.utcnow().isoformat(),
            "message_count": 1
        }
        
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        result = cache_service.get_cached_conversation_history(conversation_id)
        
        assert result is not None
        assert len(result) == 1
        assert result[0]["content"] == "Hello"
        
        mock_redis_client.get.assert_called_once_with(f"conversation:{conversation_id}:history")
    
    def test_cache_log_entry(self, cache_service, mock_redis_client):
        """Test caching log entry."""
        log_key = "test-log"
        log_data = {"type": "info", "message": "Test log message"}
        
        result = cache_service.cache_log_entry(log_key, log_data)
        
        assert result is True
        mock_redis_client.setex.assert_called_once()
        
        # Verify the key and data structure
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == f"log:{log_key}"
        assert call_args[0][1] == 86400  # TTL
        
        # Verify data structure
        cached_data = json.loads(call_args[0][2])
        assert cached_data["type"] == "info"
        assert cached_data["message"] == "Test log message"
        assert "logged_at" in cached_data
    
    def test_cache_error_log(self, cache_service, mock_redis_client):
        """Test caching error log."""
        error_type = "database_error"
        error_message = "Connection failed"
        context = {"user_id": "123", "operation": "create"}
        
        result = cache_service.cache_error_log(error_type, error_message, context)
        
        assert result is True
        mock_redis_client.setex.assert_called_once()
        
        # Verify the key pattern
        call_args = mock_redis_client.setex.call_args
        key = call_args[0][0]
        assert key.startswith("log:error:database_error:")
        
        # Verify data structure
        cached_data = json.loads(call_args[0][2])
        assert cached_data["type"] == "error"
        assert cached_data["error_type"] == error_type
        assert cached_data["error_message"] == error_message
        assert cached_data["context"] == context
    
    def test_cache_performance_log(self, cache_service, mock_redis_client):
        """Test caching performance log."""
        operation = "get_conversation"
        execution_time = 0.5
        context = {"conversation_id": "123"}
        
        result = cache_service.cache_performance_log(operation, execution_time, context)
        
        assert result is True
        mock_redis_client.setex.assert_called_once()
        
        # Verify the key pattern
        call_args = mock_redis_client.setex.call_args
        key = call_args[0][0]
        assert key.startswith("log:perf:get_conversation:")
        
        # Verify data structure
        cached_data = json.loads(call_args[0][2])
        assert cached_data["type"] == "performance"
        assert cached_data["operation"] == operation
        assert cached_data["execution_time"] == execution_time
        assert cached_data["context"] == context
    
    def test_get_cache_stats(self, cache_service, mock_redis_client):
        """Test getting cache statistics."""
        mock_redis_client.keys.side_effect = [
            ["conversation:1:history", "conversation:2:history"],  # conversation keys
            ["log:error:1", "log:perf:1"],  # log keys
            ["log:error:1"],  # error keys
            ["log:perf:1"]   # perf keys
        ]
        
        stats = cache_service.get_cache_stats()
        
        assert "redis_info" in stats
        assert "cache_counts" in stats
        assert stats["cache_counts"]["conversation_keys"] == 2
        assert stats["cache_counts"]["log_keys"] == 2
        assert stats["cache_counts"]["error_keys"] == 1
        assert stats["cache_counts"]["performance_keys"] == 1
        assert stats["cache_counts"]["total_keys"] == 4
    
    def test_invalidate_conversation_cache(self, cache_service, mock_redis_client):
        """Test invalidating conversation cache."""
        conversation_id = "test-conv-123"
        
        result = cache_service.invalidate_conversation_cache(conversation_id)
        
        assert result is True
        mock_redis_client.delete.assert_called_once_with(f"conversation:{conversation_id}:history")
    
    def test_redis_connection_failure(self):
        """Test behavior when Redis connection fails."""
        with patch('app.cache.redis.Redis.from_url', side_effect=Exception("Connection failed")):
            cache = RedisCache()
            
            # Should handle gracefully
            result = cache.cache_conversation_history("test", [])
            assert result is False
            
            result = cache.get_cached_conversation_history("test")
            assert result is None

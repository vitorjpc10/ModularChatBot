#!/usr/bin/env python3
"""
Simple script to test Redis connection and basic operations.
Run this to verify Redis is working correctly.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.cache import cache
from app.config import settings


def test_redis_connection():
    """Test Redis connection and basic operations."""
    print("🔍 Testing Redis connection...")
    print(f"Redis URL: {settings.REDIS_URL}")
    print(f"Redis DB: {settings.REDIS_DB}")
    
    try:
        # Test basic connection
        stats = cache.get_cache_stats()
        
        if "error" in stats:
            print(f"❌ Redis connection failed: {stats['error']}")
            return False
        
        print("✅ Redis connection successful!")
        print(f"Redis version: {stats.get('redis_info', {}).get('version', 'Unknown')}")
        print(f"Connected clients: {stats.get('redis_info', {}).get('connected_clients', 0)}")
        print(f"Used memory: {stats.get('redis_info', {}).get('used_memory_human', 'Unknown')}")
        
        # Test basic operations
        print("\n🧪 Testing basic operations...")
        
        # Test caching a simple value
        test_key = "test:connection:check"
        test_data = {"message": "Hello Redis!", "timestamp": "2024-01-01T00:00:00Z"}
        
        success = cache.cache_log_entry(test_key, test_data, ttl=60)
        if success:
            print("✅ Cache write successful")
        else:
            print("❌ Cache write failed")
            return False
        
        # Test reading the cached value
        logs = cache.get_cached_logs(f"log:{test_key}", limit=1)
        if logs and len(logs) > 0:
            print("✅ Cache read successful")
            print(f"Retrieved data: {logs[0]}")
        else:
            print("❌ Cache read failed")
            return False
        
        # Test performance logging
        success = cache.cache_performance_log("test_operation", 0.123, {"test": True})
        if success:
            print("✅ Performance logging successful")
        else:
            print("❌ Performance logging failed")
        
        # Test error logging
        success = cache.cache_error_log("test_error", "This is a test error", {"test": True})
        if success:
            print("✅ Error logging successful")
        else:
            print("❌ Error logging failed")
        
        # Get final stats
        final_stats = cache.get_cache_stats()
        print(f"\n📊 Final cache stats:")
        print(f"Total keys: {final_stats.get('cache_counts', {}).get('total_keys', 0)}")
        print(f"Conversation keys: {final_stats.get('cache_counts', {}).get('conversation_keys', 0)}")
        print(f"Log keys: {final_stats.get('cache_counts', {}).get('log_keys', 0)}")
        
        print("\n🎉 All Redis tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Redis test failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)

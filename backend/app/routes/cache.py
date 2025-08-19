"""
Cache management routes for Redis operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from ..database import get_db
from ..cache import cache
from ..config import settings

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get Redis cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        stats = cache.get_cache_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.get("/logs")
async def get_cached_logs(
    pattern: str = "log:*",
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get cached log entries.
    
    Args:
        pattern: Redis key pattern to search for
        limit: Maximum number of logs to return
        
    Returns:
        Dictionary with cached logs
    """
    try:
        logs = cache.get_cached_logs(pattern, limit)
        return {
            "status": "success",
            "data": {
                "logs": logs,
                "count": len(logs),
                "pattern": pattern
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cached logs: {str(e)}")


@router.get("/logs/errors")
async def get_error_logs(limit: int = 50) -> Dict[str, Any]:
    """
    Get cached error logs.
    
    Args:
        limit: Maximum number of error logs to return
        
    Returns:
        Dictionary with error logs
    """
    try:
        error_logs = cache.get_cached_logs("log:error:*", limit)
        return {
            "status": "success",
            "data": {
                "error_logs": error_logs,
                "count": len(error_logs)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get error logs: {str(e)}")


@router.get("/logs/performance")
async def get_performance_logs(limit: int = 50) -> Dict[str, Any]:
    """
    Get cached performance logs.
    
    Args:
        limit: Maximum number of performance logs to return
        
    Returns:
        Dictionary with performance logs
    """
    try:
        perf_logs = cache.get_cached_logs("log:perf:*", limit)
        return {
            "status": "success",
            "data": {
                "performance_logs": perf_logs,
                "count": len(perf_logs)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance logs: {str(e)}")


@router.delete("/conversation/{conversation_id}")
async def invalidate_conversation_cache(conversation_id: str) -> Dict[str, Any]:
    """
    Invalidate cached conversation data.
    
    Args:
        conversation_id: Conversation identifier
        
    Returns:
        Dictionary with operation result
    """
    try:
        success = cache.invalidate_conversation_cache(conversation_id)
        return {
            "status": "success" if success else "not_found",
            "data": {
                "conversation_id": conversation_id,
                "invalidated": success
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


@router.post("/clear-expired")
async def clear_expired_keys() -> Dict[str, Any]:
    """
    Clear expired keys from cache.
    
    Returns:
        Dictionary with operation result
    """
    try:
        cleared_count = cache.clear_expired_keys()
        return {
            "status": "success",
            "data": {
                "cleared_keys": cleared_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear expired keys: {str(e)}")


@router.get("/health")
async def cache_health_check() -> Dict[str, Any]:
    """
    Check Redis cache health.
    
    Returns:
        Dictionary with health status
    """
    try:
        stats = cache.get_cache_stats()
        if "error" in stats:
            return {
                "status": "unhealthy",
                "data": {
                    "error": stats["error"]
                }
            }
        
        return {
            "status": "healthy",
            "data": {
                "redis_connected": True,
                "redis_version": stats.get("redis_info", {}).get("version"),
                "total_keys": stats.get("cache_counts", {}).get("total_keys", 0)
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "data": {
                "error": str(e)
            }
        }

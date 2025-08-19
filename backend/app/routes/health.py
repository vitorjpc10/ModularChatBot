"""
Health check routes for monitoring system status.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db, check_database_health
from ..services import AIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Dictionary with system status information
    """
    try:
        # Check basic system health
        health_status = {
            "status": "healthy",
            "service": "ModularChatBot",
            "version": "1.0.0"
        }
        
        logger.info("Health check completed successfully")
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unhealthy"
        )


@router.get("/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Detailed health check endpoint that checks all system components.
    
    Returns:
        Dictionary with detailed system status information
    """
    try:
        health_status = {
            "status": "healthy",
            "service": "ModularChatBot",
            "version": "1.0.0",
            "components": {}
        }
        
        # Check database health
        try:
            db_healthy = check_database_health()
            health_status["components"]["database"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "details": "Database connection is working" if db_healthy else "Database connection failed"
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "details": f"Database check failed: {str(e)}"
            }
        
        # Check AI service health
        try:
            ai_service = AIService()
            ai_healthy = ai_service.health_check()
            health_status["components"]["ai_service"] = {
                "status": "healthy" if ai_healthy else "unhealthy",
                "details": "AI service is working" if ai_healthy else "AI service configuration issue"
            }
        except Exception as e:
            health_status["components"]["ai_service"] = {
                "status": "unhealthy",
                "details": f"AI service check failed: {str(e)}"
            }
        
        # Determine overall status
        all_healthy = all(
            component["status"] == "healthy" 
            for component in health_status["components"].values()
        )
        
        if not all_healthy:
            health_status["status"] = "degraded"
        
        logger.info(f"Detailed health check completed - Status: {health_status['status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes liveness probes.
    
    Returns:
        Dictionary with readiness status
    """
    try:
        # Check if the service is ready to handle requests
        ready_status = {
            "ready": True,
            "service": "ModularChatBot",
            "checks": {}
        }
        
        # Check database readiness
        try:
            db_healthy = check_database_health()
            ready_status["checks"]["database"] = {
                "ready": db_healthy,
                "details": "Database connection is working" if db_healthy else "Database connection failed"
            }
        except Exception as e:
            ready_status["checks"]["database"] = {
                "ready": False,
                "details": f"Database check failed: {str(e)}"
            }
        
        # Check AI service readiness
        try:
            ai_service = AIService()
            ai_healthy = ai_service.health_check()
            ready_status["checks"]["ai_service"] = {
                "ready": ai_healthy,
                "details": "AI service is configured" if ai_healthy else "AI service configuration issue"
            }
        except Exception as e:
            ready_status["checks"]["ai_service"] = {
                "ready": False,
                "details": f"AI service check failed: {str(e)}"
            }
        
        # Determine overall readiness
        all_ready = all(
            check["ready"] 
            for check in ready_status["checks"].values()
        )
        
        ready_status["ready"] = all_ready
        
        if not all_ready:
            logger.warning("Service is not ready to handle requests")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is not ready"
            )
        
        logger.info("Readiness check completed - Service is ready")
        return ready_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        )

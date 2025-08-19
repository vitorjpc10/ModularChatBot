"""
Main FastAPI application entry point for the Modular Chatbot.
"""

import logging
import logging.config
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import settings
from .database import create_tables
from .cache import cache
from .routes import chat_router, conversations_router, messages_router, health_router, cache_router

# Configure logging
logging.config.dictConfig(settings.get_logging_config())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting ModularChatBot application...")
    
    try:
        # Create database tables
        create_tables()
        logger.info("Database tables created successfully")
        
        # Test Redis connection
        cache_stats = cache.get_cache_stats()
        if "error" in cache_stats:
            logger.warning(f"Redis connection failed: {cache_stats['error']}")
            logger.warning("Application will continue without Redis caching")
        else:
            logger.info("Redis connection established successfully")
            logger.info(f"Redis version: {cache_stats.get('redis_info', {}).get('version', 'Unknown')}")
        
        # Additional startup tasks can be added here
        logger.info("ModularChatBot application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ModularChatBot application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A modular chatbot system with agent routing, knowledge retrieval, and mathematical computation capabilities.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent raw exceptions from being returned to clients."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


# Include routers
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(health_router)
app.include_router(cache_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with basic application information."""
    return {
        "message": "Welcome to ModularChatBot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/info", tags=["info"])
async def info():
    """Application information endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "description": "A modular chatbot system with agent routing capabilities"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

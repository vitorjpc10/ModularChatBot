"""
API routes for the Modular Chatbot application.
"""

from .chat import router as chat_router
from .conversations import router as conversations_router
from .messages import router as messages_router
from .health import router as health_router
from .cache import router as cache_router

__all__ = [
    "chat_router",
    "conversations_router", 
    "messages_router",
    "health_router",
    "cache_router"
]

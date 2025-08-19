"""
Message service for managing message data.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.message import Message
from ..schemas.message import MessageCreate, MessageResponse
from ..cache import cache

logger = logging.getLogger(__name__)


class MessageService:
    """Service for managing message data."""
    
    def __init__(self):
        """Initialize the message service."""
        logger.info("Message Service initialized")
    
    async def create_message(
        self, 
        db: Session, 
        message_data: MessageCreate
    ) -> MessageResponse:
        """
        Create a new message with cache invalidation.
        
        Args:
            db: Database session
            message_data: Message creation data
            
        Returns:
            Created message response
        """
        try:
            db_message = Message(
                conversation_id=message_data.conversation_id,
                content=message_data.content,
                response=message_data.response,
                source_agent=message_data.source_agent,
                source_agent_response=message_data.source_agent_response,
                agent_workflow=message_data.agent_workflow,
                execution_time=message_data.execution_time
            )
            
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            # Invalidate conversation cache since we added a new message
            cache.invalidate_conversation_cache(message_data.conversation_id)
            
            logger.info(f"Message {db_message.id} created for conversation {message_data.conversation_id}")
            
            return MessageResponse.from_orm(db_message)
            
        except Exception as e:
            db.rollback()
            # Cache error log
            cache.cache_error_log(
                "create_message_error",
                str(e),
                {"conversation_id": message_data.conversation_id, "content": message_data.content[:100]}
            )
            logger.error(f"Failed to create message: {e}")
            raise
    
    async def get_message(
        self, 
        db: Session, 
        message_id: int
    ) -> Optional[MessageResponse]:
        """
        Get a message by ID.
        
        Args:
            db: Database session
            message_id: Message identifier
            
        Returns:
            Message response or None if not found
        """
        try:
            message = db.query(Message).filter(Message.id == message_id).first()
            
            if message:
                return MessageResponse.from_orm(message)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get message {message_id}: {e}")
            raise
    
    async def get_conversation_messages(
        self, 
        db: Session, 
        conversation_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[MessageResponse]:
        """
        Get all messages for a conversation with Redis caching.
        
        Args:
            db: Database session
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of message responses
        """
        start_time = time.time()
        
        try:
            # Try to get from cache first (only for full conversation history)
            if offset == 0:
                cached_messages = cache.get_cached_conversation_history(conversation_id)
                if cached_messages and len(cached_messages) >= limit:
                    logger.info(f"Retrieved {len(cached_messages[:limit])} messages for conversation {conversation_id} from cache")
                    # Cache performance log
                    execution_time = time.time() - start_time
                    cache.cache_performance_log(
                        "get_conversation_messages_cache_hit",
                        execution_time,
                        {"conversation_id": conversation_id, "limit": limit}
                    )
                    return [MessageResponse(**msg) for msg in cached_messages[:limit]]
            
            # If not in cache or partial request, get from database
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).offset(offset).limit(limit).all()
            
            responses = [MessageResponse.from_orm(message) for message in messages]
            
            # Cache full conversation history if this is a complete request
            if offset == 0 and len(responses) > 0:
                message_dicts = [msg.dict() for msg in responses]
                cache.cache_conversation_history(conversation_id, message_dicts)
            
            # Cache performance log
            execution_time = time.time() - start_time
            cache.cache_performance_log(
                "get_conversation_messages_db_hit",
                execution_time,
                {"conversation_id": conversation_id, "limit": limit, "offset": offset}
            )
            
            logger.info(f"Retrieved {len(responses)} messages for conversation {conversation_id}")
            return responses
            
        except Exception as e:
            # Cache error log
            cache.cache_error_log(
                "get_conversation_messages_error",
                str(e),
                {"conversation_id": conversation_id, "limit": limit, "offset": offset}
            )
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            raise
    
    async def get_user_messages(
        self, 
        db: Session, 
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[MessageResponse]:
        """
        Get all messages for a user across all conversations.
        
        Args:
            db: Database session
            user_id: User identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of message responses
        """
        try:
            # Join with conversation to filter by user_id
            messages = db.query(Message).join(
                Message.conversation
            ).filter(
                Message.conversation.has(user_id=user_id)
            ).order_by(desc(Message.created_at)).offset(offset).limit(limit).all()
            
            responses = [MessageResponse.from_orm(message) for message in messages]
            
            logger.info(f"Retrieved {len(responses)} messages for user {user_id}")
            return responses
            
        except Exception as e:
            logger.error(f"Failed to get messages for user {user_id}: {e}")
            raise
    
    async def update_message(
        self, 
        db: Session, 
        message_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[MessageResponse]:
        """
        Update a message.
        
        Args:
            db: Database session
            message_id: Message identifier
            update_data: Data to update
            
        Returns:
            Updated message response or None if not found
        """
        try:
            message = db.query(Message).filter(Message.id == message_id).first()
            
            if not message:
                return None
            
            # Update allowed fields
            allowed_fields = ['response', 'source_agent_response', 'agent_workflow', 'execution_time']
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(message, field):
                    setattr(message, field, value)
            
            db.commit()
            db.refresh(message)
            
            logger.info(f"Message {message_id} updated successfully")
            
            return MessageResponse.from_orm(message)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update message {message_id}: {e}")
            raise
    
    async def delete_message(
        self, 
        db: Session, 
        message_id: int
    ) -> bool:
        """
        Delete a message.
        
        Args:
            db: Database session
            message_id: Message identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            message = db.query(Message).filter(Message.id == message_id).first()
            
            if not message:
                return False
            
            db.delete(message)
            db.commit()
            
            logger.info(f"Message {message_id} deleted successfully")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete message {message_id}: {e}")
            raise
    
    async def get_message_stats(
        self, 
        db: Session, 
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get message statistics.
        
        Args:
            db: Database session
            conversation_id: Optional conversation identifier to filter by
            user_id: Optional user identifier to filter by
            
        Returns:
            Dictionary with message statistics
        """
        try:
            query = db.query(Message)
            
            if conversation_id:
                query = query.filter(Message.conversation_id == conversation_id)
            
            if user_id:
                query = query.join(Message.conversation).filter(
                    Message.conversation.has(user_id=user_id)
                )
            
            messages = query.all()
            
            # Calculate statistics
            total_messages = len(messages)
            messages_with_responses = len([m for m in messages if m.response])
            messages_with_agents = len([m for m in messages if m.source_agent])
            
            # Agent breakdown
            agent_breakdown = {}
            for message in messages:
                if message.source_agent:
                    agent_breakdown[message.source_agent] = agent_breakdown.get(message.source_agent, 0) + 1
            
            # Execution time statistics
            execution_times = [m.execution_time for m in messages if m.execution_time]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            min_execution_time = min(execution_times) if execution_times else 0
            max_execution_time = max(execution_times) if execution_times else 0
            
            stats = {
                "total_messages": total_messages,
                "messages_with_responses": messages_with_responses,
                "messages_with_agents": messages_with_agents,
                "agent_breakdown": agent_breakdown,
                "execution_time_stats": {
                    "average": avg_execution_time,
                    "minimum": min_execution_time,
                    "maximum": max_execution_time,
                    "total_measured": len(execution_times)
                }
            }
            
            if conversation_id:
                stats["conversation_id"] = conversation_id
            
            if user_id:
                stats["user_id"] = user_id
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get message stats: {e}")
            raise

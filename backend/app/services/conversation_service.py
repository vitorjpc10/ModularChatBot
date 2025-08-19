"""
Conversation service for managing conversation data.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.conversation import Conversation
from ..schemas.conversation import ConversationCreate, ConversationResponse
from ..cache import cache

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversation data."""
    
    def __init__(self):
        """Initialize the conversation service."""
        logger.info("Conversation Service initialized")
    
    async def create_conversation(
        self, 
        db: Session, 
        conversation_data: ConversationCreate
    ) -> ConversationResponse:
        """
        Create a new conversation.
        
        Args:
            db: Database session
            conversation_data: Conversation creation data
            
        Returns:
            Created conversation response
        """
        try:
            # Check if conversation already exists
            existing = db.query(Conversation).filter(
                Conversation.conversation_id == conversation_data.conversation_id
            ).first()
            
            if existing:
                logger.info(f"Conversation {conversation_data.conversation_id} already exists")
                return ConversationResponse.from_orm(existing)
            
            # Create new conversation
            db_conversation = Conversation(
                conversation_id=conversation_data.conversation_id,
                user_id=conversation_data.user_id,
                title=conversation_data.title
            )
            
            db.add(db_conversation)
            db.commit()
            db.refresh(db_conversation)
            
            logger.info(f"Conversation {conversation_data.conversation_id} created successfully")
            
            return ConversationResponse.from_orm(db_conversation)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    async def get_conversation(
        self, 
        db: Session, 
        conversation_id: str
    ) -> Optional[ConversationResponse]:
        """
        Get a conversation by ID with Redis caching.
        
        Args:
            db: Database session
            conversation_id: Conversation identifier
            
        Returns:
            Conversation response or None if not found
        """
        start_time = time.time()
        
        try:
            # Try to get from cache first
            cached_metadata = cache.get_cached_conversation_metadata(conversation_id)
            if cached_metadata:
                logger.info(f"Retrieved conversation {conversation_id} from cache")
                # Cache performance log
                execution_time = time.time() - start_time
                cache.cache_performance_log(
                    "get_conversation_cache_hit",
                    execution_time,
                    {"conversation_id": conversation_id}
                )
                return ConversationResponse(**cached_metadata)
            
            # If not in cache, get from database
            conversation = db.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            
            if conversation:
                # Get message count
                message_count = len(conversation.messages)
                response = ConversationResponse.from_orm(conversation)
                response.message_count = message_count
                
                # Cache the conversation metadata
                metadata = response.dict()
                cache.cache_conversation_metadata(conversation_id, metadata)
                
                # Cache performance log
                execution_time = time.time() - start_time
                cache.cache_performance_log(
                    "get_conversation_db_hit",
                    execution_time,
                    {"conversation_id": conversation_id}
                )
                
                return response
            
            return None
            
        except Exception as e:
            # Cache error log
            cache.cache_error_log(
                "get_conversation_error",
                str(e),
                {"conversation_id": conversation_id}
            )
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            raise
    
    async def get_user_conversations(
        self, 
        db: Session, 
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ConversationResponse]:
        """
        Get all conversations for a user.
        
        Args:
            db: Database session
            user_id: User identifier
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            
        Returns:
            List of conversation responses
        """
        try:
            conversations = db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(desc(Conversation.updated_at)).offset(offset).limit(limit).all()
            
            responses = []
            for conversation in conversations:
                message_count = len(conversation.messages)
                response = ConversationResponse.from_orm(conversation)
                response.message_count = message_count
                responses.append(response)
            
            logger.info(f"Retrieved {len(responses)} conversations for user {user_id}")
            return responses
            
        except Exception as e:
            logger.error(f"Failed to get conversations for user {user_id}: {e}")
            raise
    
    async def update_conversation_title(
        self, 
        db: Session, 
        conversation_id: str, 
        title: str
    ) -> Optional[ConversationResponse]:
        """
        Update conversation title with cache invalidation.
        
        Args:
            db: Database session
            conversation_id: Conversation identifier
            title: New title
            
        Returns:
            Updated conversation response or None if not found
        """
        try:
            conversation = db.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            
            if not conversation:
                return None
            
            conversation.title = title
            db.commit()
            db.refresh(conversation)
            
            # Invalidate cache for this conversation
            cache.invalidate_conversation_cache(conversation_id)
            
            logger.info(f"Conversation {conversation_id} title updated to: {title}")
            
            response = ConversationResponse.from_orm(conversation)
            response.message_count = len(conversation.messages)
            return response
            
        except Exception as e:
            db.rollback()
            # Cache error log
            cache.cache_error_log(
                "update_conversation_title_error",
                str(e),
                {"conversation_id": conversation_id, "title": title}
            )
            logger.error(f"Failed to update conversation {conversation_id}: {e}")
            raise
    
    async def delete_conversation(
        self, 
        db: Session, 
        conversation_id: str
    ) -> bool:
        """
        Delete a conversation and all its messages with cache cleanup.
        
        Args:
            db: Database session
            conversation_id: Conversation identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            conversation = db.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            
            if not conversation:
                return False
            
            db.delete(conversation)
            db.commit()
            
            # Invalidate cache for this conversation
            cache.invalidate_conversation_cache(conversation_id)
            
            logger.info(f"Conversation {conversation_id} deleted successfully")
            return True
            
        except Exception as e:
            db.rollback()
            # Cache error log
            cache.cache_error_log(
                "delete_conversation_error",
                str(e),
                {"conversation_id": conversation_id}
            )
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            raise
    
    async def get_conversation_stats(
        self, 
        db: Session, 
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get conversation statistics.
        
        Args:
            db: Database session
            conversation_id: Conversation identifier
            
        Returns:
            Dictionary with conversation statistics
        """
        try:
            conversation = db.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            
            if not conversation:
                return {}
            
            messages = conversation.messages
            
            # Calculate statistics
            total_messages = len(messages)
            user_messages = len([m for m in messages if m.response is not None])
            agent_responses = len([m for m in messages if m.source_agent])
            
            # Agent breakdown
            agent_breakdown = {}
            for message in messages:
                if message.source_agent:
                    agent_breakdown[message.source_agent] = agent_breakdown.get(message.source_agent, 0) + 1
            
            # Average execution time
            execution_times = [m.execution_time for m in messages if m.execution_time]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            stats = {
                "conversation_id": conversation_id,
                "total_messages": total_messages,
                "user_messages": user_messages,
                "agent_responses": agent_responses,
                "agent_breakdown": agent_breakdown,
                "average_execution_time": avg_execution_time,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get conversation stats for {conversation_id}: {e}")
            raise

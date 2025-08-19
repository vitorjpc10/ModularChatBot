"""
Message management routes.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.message import MessageCreate, MessageResponse
from ..services import MessageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])

# Initialize service
message_service = MessageService()


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Create a new message.
    
    Args:
        message_data: Message creation data
        db: Database session
        
    Returns:
        Created message response
    """
    try:
        return await message_service.create_message(db, message_data)
    except Exception as e:
        logger.error(f"Failed to create message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message"
        )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Get a message by ID.
    
    Args:
        message_id: Message identifier
        db: Database session
        
    Returns:
        Message response
    """
    try:
        message = await message_service.get_message(db, message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve message"
        )


@router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    db: Session = Depends(get_db)
) -> List[MessageResponse]:
    """
    Get all messages for a conversation.
    
    Args:
        conversation_id: Conversation identifier
        limit: Maximum number of messages to return
        offset: Number of messages to skip
        db: Database session
        
    Returns:
        List of message responses
    """
    try:
        return await message_service.get_conversation_messages(db, conversation_id, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )


@router.get("/user/{user_id}", response_model=List[MessageResponse])
async def get_user_messages(
    user_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    db: Session = Depends(get_db)
) -> List[MessageResponse]:
    """
    Get all messages for a user across all conversations.
    
    Args:
        user_id: User identifier
        limit: Maximum number of messages to return
        offset: Number of messages to skip
        db: Database session
        
    Returns:
        List of message responses
    """
    try:
        return await message_service.get_user_messages(db, user_id, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get messages for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Update a message.
    
    Args:
        message_id: Message identifier
        update_data: Data to update
        db: Database session
        
    Returns:
        Updated message response
    """
    try:
        message = await message_service.update_message(db, message_id, update_data)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        return message
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message"
        )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a message.
    
    Args:
        message_id: Message identifier
        db: Database session
    """
    try:
        deleted = await message_service.delete_message(db, message_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )


@router.get("/stats/conversation/{conversation_id}")
async def get_conversation_message_stats(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get message statistics for a conversation.
    
    Args:
        conversation_id: Conversation identifier
        db: Database session
        
    Returns:
        Message statistics
    """
    try:
        stats = await message_service.get_message_stats(db, conversation_id=conversation_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get message stats for conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve message statistics"
        )


@router.get("/stats/user/{user_id}")
async def get_user_message_stats(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get message statistics for a user.
    
    Args:
        user_id: User identifier
        db: Database session
        
    Returns:
        Message statistics
    """
    try:
        stats = await message_service.get_message_stats(db, user_id=user_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get message stats for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve message statistics"
        )

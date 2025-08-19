"""
Conversation management routes.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.conversation import ConversationCreate, ConversationResponse
from ..services import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])

# Initialize service
conversation_service = ConversationService()


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """
    Create a new conversation.
    
    Args:
        conversation_data: Conversation creation data
        db: Database session
        
    Returns:
        Created conversation response
    """
    try:
        return await conversation_service.create_conversation(db, conversation_data)
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """
    Get a conversation by ID.
    
    Args:
        conversation_id: Conversation identifier
        db: Database session
        
    Returns:
        Conversation response
    """
    try:
        conversation = await conversation_service.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )


@router.get("/user/{user_id}", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    db: Session = Depends(get_db)
) -> List[ConversationResponse]:
    """
    Get all conversations for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip
        db: Database session
        
    Returns:
        List of conversation responses
    """
    try:
        return await conversation_service.get_user_conversations(db, user_id, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get conversations for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )


@router.put("/{conversation_id}/title", response_model=ConversationResponse)
async def update_conversation_title(
    conversation_id: str,
    title: str,
    db: Session = Depends(get_db)
) -> ConversationResponse:
    """
    Update conversation title.
    
    Args:
        conversation_id: Conversation identifier
        title: New title
        db: Database session
        
    Returns:
        Updated conversation response
    """
    try:
        conversation = await conversation_service.update_conversation_title(db, conversation_id, title)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    
    Args:
        conversation_id: Conversation identifier
        db: Database session
    """
    try:
        deleted = await conversation_service.delete_conversation(db, conversation_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.get("/{conversation_id}/stats")
async def get_conversation_stats(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get conversation statistics.
    
    Args:
        conversation_id: Conversation identifier
        db: Database session
        
    Returns:
        Conversation statistics
    """
    try:
        stats = await conversation_service.get_conversation_stats(db, conversation_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation stats for {conversation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation statistics"
        )

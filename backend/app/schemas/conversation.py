"""
Conversation schemas for conversation management.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    
    conversation_id: str = Field(..., min_length=1, max_length=255, description="Conversation identifier")
    user_id: str = Field(..., min_length=1, max_length=255, description="User identifier")
    title: Optional[str] = Field(None, max_length=500, description="Conversation title")
    
    class Config:
        schema_extra = {
            "example": {
                "conversation_id": "conv-1234",
                "user_id": "client789",
                "title": "Card Machine Inquiry"
            }
        }


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    title: Optional[str] = Field(None, description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    message_count: int = Field(0, description="Number of messages in conversation")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "conversation_id": "conv-1234",
                "user_id": "client789",
                "title": "Card Machine Inquiry",
                "created_at": "2025-08-07T14:30:00Z",
                "updated_at": "2025-08-07T14:35:00Z",
                "message_count": 5
            }
        }

"""
Conversation model for storing conversation metadata.
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database import Base


class Conversation(Base):
    """Model for storing conversation metadata."""
    
    __tablename__ = "conversations"
    
    # Primary key
    conversation_id = Column(String(255), primary_key=True, index=True)
    
    # User information
    user_id = Column(String(255), nullable=False, index=True)
    
    # Conversation metadata
    title = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Conversation(conversation_id='{self.conversation_id}', user_id='{self.user_id}')>"
    
    def __str__(self) -> str:
        return f"Conversation {self.conversation_id} by {self.user_id}"

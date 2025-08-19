"""
Message model for storing individual chat messages.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database import Base


class Message(Base):
    """Model for storing individual chat messages."""
    
    __tablename__ = "messages"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to conversation
    conversation_id = Column(String(255), ForeignKey("conversations.conversation_id"), nullable=False, index=True)
    
    # Message content
    content = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    
    # Agent information
    source_agent = Column(String(100), nullable=True)  # RouterAgent, KnowledgeAgent, MathAgent
    source_agent_response = Column(Text, nullable=True)
    
    # Agent workflow tracking
    agent_workflow = Column(JSON, nullable=True)  # Store the workflow steps
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    execution_time = Column(Integer, nullable=True)  # Execution time in milliseconds
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id='{self.conversation_id}', source_agent='{self.source_agent}')>"
    
    def __str__(self) -> str:
        return f"Message {self.id} in conversation {self.conversation_id}"

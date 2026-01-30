"""
Message model - individual chat message with metadata
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Message(Base):
    """Represents an individual message within a chat session"""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    sender = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)  # Can be null for deleted messages
    timestamp = Column(DateTime, nullable=False)
    
    # Sequence for gap detection
    sequence_number = Column(Integer, nullable=False)
    
    # Message type and status
    message_type = Column(String(50), default="text")  # text, media, system, deleted
    is_deleted = Column(Boolean, default=False)
    
    # Metadata for analysis
    word_count = Column(Integer, default=0)
    has_media = Column(Boolean, default=False)
    reply_to_sequence = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

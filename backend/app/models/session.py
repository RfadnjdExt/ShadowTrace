"""
ChatSession model - represents an imported chat conversation
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ChatSession(Base):
    """Represents an imported chat conversation session"""
    
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    source_format = Column(String(50), nullable=False)  # whatsapp, telegram, csv
    source_filename = Column(String(255), nullable=True)
    
    # Metadata extracted from chat
    participants = Column(Text, nullable=True)  # JSON array of participant names
    start_timestamp = Column(DateTime, nullable=True)
    end_timestamp = Column(DateTime, nullable=True)
    total_messages = Column(Integer, default=0)
    detected_gaps = Column(Integer, default=0)
    
    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, analyzed, error
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    gaps = relationship("Gap", back_populates="session", cascade="all, delete-orphan")

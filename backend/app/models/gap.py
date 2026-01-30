"""
Gap model - detected deletion or suspicious break in conversation
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Gap(Base):
    """Represents a detected gap/deletion in the chat conversation"""
    
    __tablename__ = "gaps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    
    # Position in conversation
    before_message_seq = Column(Integer, nullable=False)
    after_message_seq = Column(Integer, nullable=False)
    
    # Time analysis
    time_gap_seconds = Column(Integer, nullable=False)
    expected_messages = Column(Integer, nullable=True)  # Estimated missing messages
    
    # Detection reason
    detection_type = Column(String(50), nullable=False)
    # Types: time_anomaly, sequence_break, context_mismatch, pattern_break
    
    # Suspicion scoring
    suspicion_score = Column(Float, default=0.0)  # 0.0 to 1.0
    suspicion_reasons = Column(Text, nullable=True)  # JSON array of reasons
    
    # Context for AI analysis
    context_before = Column(Text, nullable=True)  # Messages before gap
    context_after = Column(Text, nullable=True)   # Messages after gap
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="gaps")
    inferences = relationship("Inference", back_populates="gap", cascade="all, delete-orphan")

"""
Inference model - AI-generated predictions for detected gaps
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Inference(Base):
    """AI-generated inference/prediction for a detected gap"""
    
    __tablename__ = "inferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gap_id = Column(UUID(as_uuid=True), ForeignKey("gaps.id"), nullable=False)
    
    # Inference content
    predicted_intent = Column(Text, nullable=False)  # What was likely discussed
    predicted_content = Column(Text, nullable=True)  # Possible message content
    predicted_sender = Column(String(255), nullable=True)
    
    # Confidence and anchoring
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    context_anchors = Column(Text, nullable=True)  # JSON: references to supporting messages
    
    # Model information
    model_used = Column(String(100), nullable=False)
    reasoning = Column(Text, nullable=True)  # AI's explanation
    
    # Hallucination prevention
    hallucination_flags = Column(Text, nullable=True)  # JSON: potential issues
    verified = Column(String(20), default="pending")  # pending, accepted, rejected
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    gap = relationship("Gap", back_populates="inferences")

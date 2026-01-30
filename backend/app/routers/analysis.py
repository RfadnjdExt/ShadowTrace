"""
Analysis Router - API endpoints for gap detection and AI inference
"""
import json
from uuid import UUID
from typing import List, Optional
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import ChatSession, Message, Gap, Inference
from app.services.parser import ParsedMessage
from app.services.gap_detector import GapDetector
from app.services.metadata_engine import MetadataEngine
from app.services.ai_inferencer import AIInferencer


router = APIRouter()


# Pydantic Schemas
class GapResponse(BaseModel):
    id: UUID
    before_message_seq: int
    after_message_seq: int
    time_gap_seconds: int
    detection_type: str
    suspicion_score: float
    suspicion_reasons: Optional[str]
    expected_messages: Optional[int]
    
    class Config:
        from_attributes = True


class InferenceResponse(BaseModel):
    id: UUID
    gap_id: UUID
    predicted_intent: str
    predicted_content: Optional[str]
    predicted_sender: Optional[str]
    confidence_score: float
    reasoning: Optional[str]
    model_used: str
    verified: str
    
    class Config:
        from_attributes = True


class AnalysisResultResponse(BaseModel):
    session_id: UUID
    gaps_detected: int
    inferences_generated: int
    high_priority_gaps: int
    gaps: List[GapResponse]
    

# Endpoints
@router.post("/sessions/{session_id}/analyze", response_model=AnalysisResultResponse)
async def analyze_session(
    session_id: UUID,
    min_suspicion: float = 0.0,
    generate_inferences: bool = True,
    db: Session = Depends(get_db)
):
    """
    Analyze a chat session for gaps and generate AI inferences
    
    Args:
        session_id: The session to analyze
        min_suspicion: Minimum suspicion score to record (0.0-1.0)
        generate_inferences: Whether to generate AI predictions for gaps
    """
    # Get session
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update status
    session.status = "processing"
    db.commit()
    
    try:
        # Get all messages
        messages = db.query(Message)\
            .filter(Message.session_id == session_id)\
            .order_by(Message.sequence_number)\
            .all()
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages in session")
        
        # Convert to ParsedMessage for analysis
        parsed_messages = [
            ParsedMessage(
                timestamp=m.timestamp,
                sender=m.sender,
                content=m.content or "",
                sequence_number=m.sequence_number,
                message_type=m.message_type,
                is_deleted=m.is_deleted,
                has_media=m.has_media,
            )
            for m in messages
        ]
        
        # Run gap detection
        detector = GapDetector(parsed_messages)
        detected_gaps = detector.detect_all()
        
        # Filter by suspicion score
        filtered_gaps = [g for g in detected_gaps if g.suspicion_score >= min_suspicion]
        
        # Clear existing gaps and inferences
        db.query(Gap).filter(Gap.session_id == session_id).delete()
        db.commit()
        
        # Store gaps in database
        gap_records = []
        for dg in filtered_gaps:
            gap = Gap(
                session_id=session_id,
                before_message_seq=dg.before_seq,
                after_message_seq=dg.after_seq,
                time_gap_seconds=dg.time_gap_seconds,
                detection_type=dg.detection_type,
                suspicion_score=dg.suspicion_score,
                suspicion_reasons=json.dumps(dg.suspicion_reasons),
                expected_messages=dg.estimated_missing,
                context_before=json.dumps(dg.context_before),
                context_after=json.dumps(dg.context_after),
            )
            db.add(gap)
            db.flush()
            gap_records.append(gap)
        
        # Generate AI inferences if requested
        inference_count = 0
        if generate_inferences and filtered_gaps:
            inferencer = AIInferencer()
            
            for gap_record, detected_gap in zip(gap_records, filtered_gaps):
                result = inferencer.analyze_gap(detected_gap)
                
                inference = Inference(
                    gap_id=gap_record.id,
                    predicted_intent=result.predicted_intent,
                    predicted_content=result.predicted_content,
                    predicted_sender=result.predicted_sender,
                    confidence_score=result.confidence_score,
                    context_anchors=json.dumps(result.context_anchors),
                    model_used=result.model_used,
                    reasoning=result.reasoning,
                    hallucination_flags=json.dumps(result.hallucination_flags),
                )
                db.add(inference)
                inference_count += 1
        
        # Update session status
        session.status = "analyzed"
        session.detected_gaps = len(gap_records)
        db.commit()
        
        # Build response
        high_priority = sum(1 for g in filtered_gaps if g.suspicion_score >= 0.5)
        
        return AnalysisResultResponse(
            session_id=session_id,
            gaps_detected=len(gap_records),
            inferences_generated=inference_count,
            high_priority_gaps=high_priority,
            gaps=[GapResponse.model_validate(g) for g in gap_records],
        )
        
    except Exception as e:
        session.status = "error"
        session.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/sessions/{session_id}/gaps", response_model=List[GapResponse])
async def get_gaps(
    session_id: UUID,
    min_suspicion: float = 0.0,
    detection_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get detected gaps for a session"""
    query = db.query(Gap).filter(Gap.session_id == session_id)
    
    if min_suspicion > 0:
        query = query.filter(Gap.suspicion_score >= min_suspicion)
    
    if detection_type:
        query = query.filter(Gap.detection_type == detection_type)
    
    gaps = query.order_by(Gap.before_message_seq).all()
    return gaps


@router.get("/sessions/{session_id}/gaps/{gap_id}", response_model=GapResponse)
async def get_gap_detail(
    session_id: UUID,
    gap_id: UUID,
    db: Session = Depends(get_db)
):
    """Get details for a specific gap"""
    gap = db.query(Gap)\
        .filter(Gap.session_id == session_id, Gap.id == gap_id)\
        .first()
    
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")
    
    return gap


@router.get("/sessions/{session_id}/inferences", response_model=List[InferenceResponse])
async def get_inferences(
    session_id: UUID,
    min_confidence: float = 0.0,
    db: Session = Depends(get_db)
):
    """Get AI inferences for a session's gaps"""
    # Get gap IDs for this session
    gap_ids = db.query(Gap.id).filter(Gap.session_id == session_id).all()
    gap_ids = [g[0] for g in gap_ids]
    
    if not gap_ids:
        return []
    
    query = db.query(Inference).filter(Inference.gap_id.in_(gap_ids))
    
    if min_confidence > 0:
        query = query.filter(Inference.confidence_score >= min_confidence)
    
    inferences = query.all()
    return inferences


@router.get("/sessions/{session_id}/gaps/{gap_id}/inference", response_model=InferenceResponse)
async def get_gap_inference(
    session_id: UUID,
    gap_id: UUID,
    db: Session = Depends(get_db)
):
    """Get AI inference for a specific gap"""
    inference = db.query(Inference).filter(Inference.gap_id == gap_id).first()
    
    if not inference:
        raise HTTPException(status_code=404, detail="Inference not found")
    
    return inference


@router.post("/sessions/{session_id}/gaps/{gap_id}/regenerate", response_model=InferenceResponse)
async def regenerate_inference(
    session_id: UUID,
    gap_id: UUID,
    db: Session = Depends(get_db)
):
    """Regenerate AI inference for a specific gap"""
    gap = db.query(Gap)\
        .filter(Gap.session_id == session_id, Gap.id == gap_id)\
        .first()
    
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")
    
    # Delete existing inference
    db.query(Inference).filter(Inference.gap_id == gap_id).delete()
    
    # Convert to DetectedGap
    from app.services.gap_detector import DetectedGap
    detected_gap = DetectedGap(
        before_seq=gap.before_message_seq,
        after_seq=gap.after_message_seq,
        before_timestamp=None,  # Not needed for inference
        after_timestamp=None,
        time_gap_seconds=gap.time_gap_seconds,
        detection_type=gap.detection_type,
        suspicion_score=gap.suspicion_score,
        suspicion_reasons=json.loads(gap.suspicion_reasons) if gap.suspicion_reasons else [],
        context_before=json.loads(gap.context_before) if gap.context_before else [],
        context_after=json.loads(gap.context_after) if gap.context_after else [],
        estimated_missing=gap.expected_messages,
    )
    
    # Generate new inference
    inferencer = AIInferencer()
    result = inferencer.analyze_gap(detected_gap)
    
    inference = Inference(
        gap_id=gap_id,
        predicted_intent=result.predicted_intent,
        predicted_content=result.predicted_content,
        predicted_sender=result.predicted_sender,
        confidence_score=result.confidence_score,
        context_anchors=json.dumps(result.context_anchors),
        model_used=result.model_used,
        reasoning=result.reasoning,
        hallucination_flags=json.dumps(result.hallucination_flags),
    )
    db.add(inference)
    db.commit()
    db.refresh(inference)
    
    return inference


@router.get("/sessions/{session_id}/metadata")
async def get_metadata_analysis(session_id: UUID, db: Session = Depends(get_db)):
    """Get metadata analysis for a session"""
    messages = db.query(Message)\
        .filter(Message.session_id == session_id)\
        .order_by(Message.sequence_number)\
        .all()
    
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")
    
    # Convert to ParsedMessage
    parsed = [
        ParsedMessage(
            timestamp=m.timestamp,
            sender=m.sender,
            content=m.content or "",
            sequence_number=m.sequence_number,
            message_type=m.message_type,
            is_deleted=m.is_deleted,
            has_media=m.has_media,
        )
        for m in messages
    ]
    
    # Run metadata analysis
    engine = MetadataEngine(parsed)
    
    return {
        "summary": engine.get_summary(),
        "sender_stats": [asdict(s) for s in engine.analyze_all_senders() if s],
        "patterns": [asdict(p) for p in engine.detect_activity_patterns()],
        "anomalies": engine.find_anomalies(),
    }


@router.get("/model/info")
async def get_model_info():
    """Get information about the currently configured AI model"""
    inferencer = AIInferencer()
    return inferencer.get_model_info()

"""
Chat Router - API endpoints for chat session management
"""
import json
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import ChatSession, Message
from app.services.parser import WhatsAppParser


router = APIRouter()


# Pydantic Schemas
class SessionCreate(BaseModel):
    name: str
    source_format: str = "whatsapp"


class MessageResponse(BaseModel):
    id: UUID
    sender: str
    content: Optional[str]
    timestamp: datetime
    sequence_number: int
    message_type: str
    is_deleted: bool
    
    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: UUID
    name: str
    source_format: str
    status: str
    total_messages: int
    detected_gaps: int
    participants: Optional[str]
    start_timestamp: Optional[datetime]
    end_timestamp: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse] = []


# Endpoints
@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List all chat sessions"""
    sessions = db.query(ChatSession)\
        .order_by(ChatSession.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return sessions


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: UUID, db: Session = Depends(get_db)):
    """Get a specific session with all messages"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(Message)\
        .filter(Message.session_id == session_id)\
        .order_by(Message.sequence_number)\
        .all()
    
    return SessionDetailResponse(
        **{c.name: getattr(session, c.name) for c in session.__table__.columns},
        messages=[MessageResponse.model_validate(m) for m in messages]
    )


@router.post("/sessions/upload", response_model=SessionResponse)
async def upload_chat(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload a WhatsApp chat export file for analysis
    
    Supported formats:
    - WhatsApp .txt export
    """
    # Validate file type
    if not file.filename.endswith('.txt'):
        raise HTTPException(
            status_code=400, 
            detail="Only .txt files are supported. Export your chat from WhatsApp."
        )
    
    # Read file content
    content = await file.read()
    try:
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text_content = content.decode('utf-16')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Unable to decode file")
    
    # Parse the chat
    parser = WhatsAppParser()
    parsed_messages = parser.parse(text_content)
    
    if not parsed_messages:
        raise HTTPException(
            status_code=400, 
            detail="No messages could be parsed from the file"
        )
    
    # Get metadata
    participants = parser.get_participants()
    start_ts, end_ts = parser.get_time_range()
    stats = parser.get_stats()
    
    # Create session
    session = ChatSession(
        name=name or file.filename,
        source_format="whatsapp",
        source_filename=file.filename,
        participants=json.dumps(participants),
        start_timestamp=start_ts,
        end_timestamp=end_ts,
        total_messages=stats["total_messages"],
        status="imported",
    )
    db.add(session)
    db.flush()  # Get the session ID
    
    # Create messages
    for pm in parsed_messages:
        message = Message(
            session_id=session.id,
            sender=pm.sender,
            content=pm.content,
            timestamp=pm.timestamp,
            sequence_number=pm.sequence_number,
            message_type=pm.message_type,
            is_deleted=pm.is_deleted,
            has_media=pm.has_media,
            word_count=len(pm.content.split()) if pm.content else 0,
        )
        db.add(message)
    
    db.commit()
    db.refresh(session)
    
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: UUID, db: Session = Depends(get_db)):
    """Delete a chat session and all related data"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: UUID,
    skip: int = 0,
    limit: int = 100,
    sender: Optional[str] = None,
    include_deleted: bool = True,
    db: Session = Depends(get_db)
):
    """Get messages from a session with optional filtering"""
    query = db.query(Message).filter(Message.session_id == session_id)
    
    if sender:
        query = query.filter(Message.sender == sender)
    
    if not include_deleted:
        query = query.filter(Message.is_deleted == False)
    
    messages = query\
        .order_by(Message.sequence_number)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return messages


@router.get("/sessions/{session_id}/stats")
async def get_session_stats(session_id: UUID, db: Session = Depends(get_db)):
    """Get statistics for a chat session"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(Message).filter(Message.session_id == session_id).all()
    
    # Calculate stats
    senders = {}
    for msg in messages:
        if msg.sender not in senders:
            senders[msg.sender] = {"count": 0, "deleted": 0}
        senders[msg.sender]["count"] += 1
        if msg.is_deleted:
            senders[msg.sender]["deleted"] += 1
    
    return {
        "session_id": str(session_id),
        "total_messages": len(messages),
        "deleted_messages": sum(1 for m in messages if m.is_deleted),
        "media_messages": sum(1 for m in messages if m.has_media),
        "participants": senders,
        "date_range": {
            "start": session.start_timestamp.isoformat() if session.start_timestamp else None,
            "end": session.end_timestamp.isoformat() if session.end_timestamp else None,
        },
    }

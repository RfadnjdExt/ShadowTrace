"""
ShadowTrace Backend - FastAPI Application
Forensic chat reconstruction system with AI-powered analysis
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, analysis
from app.database import engine, Base
from app.models import ChatSession, Message, Gap, Inference  # noqa: F401

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ShadowTrace API",
    description="Forensic chat reconstruction system with AI-powered gap inference",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "shadowtrace-api"}


app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

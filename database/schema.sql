-- ShadowTrace Database Schema
-- PostgreSQL 15+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Chat Sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source_format VARCHAR(50) NOT NULL,
    source_filename VARCHAR(255),
    participants TEXT, -- JSON array
    start_timestamp TIMESTAMP,
    end_timestamp TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    detected_gaps INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sender VARCHAR(255) NOT NULL,
    content TEXT,
    timestamp TIMESTAMP NOT NULL,
    sequence_number INTEGER NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    is_deleted BOOLEAN DEFAULT FALSE,
    word_count INTEGER DEFAULT 0,
    has_media BOOLEAN DEFAULT FALSE,
    reply_to_sequence INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster message queries
CREATE INDEX IF NOT EXISTS idx_messages_session_seq ON messages(session_id, sequence_number);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(session_id, sender);

-- Gaps table
CREATE TABLE IF NOT EXISTS gaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    before_message_seq INTEGER NOT NULL,
    after_message_seq INTEGER NOT NULL,
    time_gap_seconds INTEGER NOT NULL,
    expected_messages INTEGER,
    detection_type VARCHAR(50) NOT NULL,
    suspicion_score FLOAT DEFAULT 0.0,
    suspicion_reasons TEXT, -- JSON array
    context_before TEXT, -- JSON array
    context_after TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for gaps
CREATE INDEX IF NOT EXISTS idx_gaps_session ON gaps(session_id);
CREATE INDEX IF NOT EXISTS idx_gaps_suspicion ON gaps(session_id, suspicion_score);

-- Inferences table
CREATE TABLE IF NOT EXISTS inferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gap_id UUID NOT NULL REFERENCES gaps(id) ON DELETE CASCADE,
    predicted_intent TEXT NOT NULL,
    predicted_content TEXT,
    predicted_sender VARCHAR(255),
    confidence_score FLOAT NOT NULL,
    context_anchors TEXT, -- JSON array
    model_used VARCHAR(100) NOT NULL,
    reasoning TEXT,
    hallucination_flags TEXT, -- JSON array
    verified VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for inferences
CREATE INDEX IF NOT EXISTS idx_inferences_gap ON inferences(gap_id);
CREATE INDEX IF NOT EXISTS idx_inferences_confidence ON inferences(confidence_score);

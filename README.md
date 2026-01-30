# ShadowTrace

> **Forensic Chat Reconstruction System** - AI-powered tool for detecting and analyzing deleted messages in chat conversations.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

ShadowTrace adalah alat forensik digital yang mampu:
- **Mengimpor** ekspor chat WhatsApp
- **Mendeteksi** celah (gap) mencurigakan dalam percakapan
- **Menganalisis** pola metadata untuk menemukan anomali
- **Memprediksi** konten pesan yang dihapus menggunakan AI

Dibangun untuk **Hackathon Gemini 3.0** dalam kategori Cybersecurity & ML/AI.

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ (atau gunakan Docker)

### Setup dengan Docker

```bash
# Clone repository
git clone https://github.com/your-repo/ShadowTrace.git
cd ShadowTrace

# Copy environment file
cp .env.example .env

# Jalankan semua services
docker-compose up -d

# API tersedia di http://localhost:8000
# Docs di http://localhost:8000/docs
```

### Setup Manual (Development)

```bash
# Setup virtual environment
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Jalankan database PostgreSQL terlebih dahulu
# Kemudian jalankan API
uvicorn main:app --reload
```

## API Endpoints

### Chat Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | GET | List semua session |
| `/api/sessions/upload` | POST | Upload file chat |
| `/api/sessions/{id}` | GET | Detail session |

### Analysis
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions/{id}/analyze` | POST | Jalankan analisis |
| `/api/sessions/{id}/gaps` | GET | List gap terdeteksi |
| `/api/sessions/{id}/inferences` | GET | AI predictions |
| `/api/sessions/{id}/metadata` | GET | Metadata analysis |

## Features

### 1. Gap Detection
- **Time Anomaly**: Deteksi celah waktu tidak wajar
- **Context Mismatch**: Perubahan topik mendadak
- **Pattern Break**: Perubahan pola respons
- **Explicit Deletion**: Marker "Pesan ini telah dihapus"

### 2. Suspicion Scoring
Setiap gap diberi skor kecurigaan (0.0-1.0) berdasarkan:
- Durasi gap
- Konteks sekitar
- Pola perilaku pengirim

### 3. AI Inference
Menggunakan Gemini 3.0 API (atau mock service) untuk:
- Memprediksi konten yang dihapus
- Memberikan confidence score
- Context anchoring untuk minimisasi halusinasi

## Tech Stack

- **Backend**: Python, FastAPI
- **Database**: PostgreSQL, SQLAlchemy
- **AI**: Gemini 3.0 API / VertexAI
- **Container**: Docker

## Project Structure

```
ShadowTrace/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routers/         # API endpoints
│   │   └── services/        # Business logic
│   ├── tests/               # Unit tests
│   └── main.py              # FastAPI app
├── database/
│   └── schema.sql           # PostgreSQL schema
├── docker-compose.yml
└── README.md
```

## Testing

```bash
cd backend

# Run unit tests
pytest tests/ -v

# Generate test data
python -m tests.test_data_generator
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read our contributing guidelines.

---

**Built for Hackathon Gemini 3.0**

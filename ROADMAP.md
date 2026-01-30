# ShadowTrace - Hackathon Roadmap

**Deadline**: 9 Februari 2026 (10 hari)

---

## Hari 1-2 (30-31 Jan): Setup & Testing
- [ ] Setup PostgreSQL lokal atau Docker
- [ ] Test backend API dengan Postman/curl
- [ ] Generate sample data dan test parser
- [ ] Fix bugs dari testing awal

## Hari 3-4 (1-2 Feb): Integrasi Gemini API
- [ ] Dapatkan API key Gemini 3.0
- [ ] Implementasi `GeminiInferencer` penuh (bukan mock)
- [ ] Tuning prompt untuk minimisasi halusinasi
- [ ] Test inference dengan berbagai skenario gap

## Hari 5-6 (3-4 Feb): UI Polish
- [ ] Perbaiki responsive design
- [ ] Tambah loading states dan error handling
- [ ] Implementasi filter dan search messages
- [ ] Tambah export hasil analisis (PDF/JSON)

## Hari 7 (5 Feb): Testing Intensif
- [ ] End-to-end testing dengan data real
- [ ] Performance testing (chat besar 1000+ pesan)
- [ ] Fix critical bugs
- [ ] Code review dan refactoring

## Hari 8 (6 Feb): Demo & Dokumentasi
- [ ] Rekam video demo
- [ ] Update README dengan screenshots
- [ ] Tulis dokumentasi API lengkap
- [ ] Siapkan slide presentasi

## Hari 9 (7 Feb): Deployment
- [ ] Deploy ke cloud (Railway/Render/Vercel)
- [ ] Setup domain jika perlu
- [ ] Test production environment
- [ ] Backup dan versioning

## Hari 10 (8-9 Feb): Final Polish
- [ ] Final bug fixes
- [ ] Review submission requirements
- [ ] Submit ke hackathon
- [ ] Persiapan presentasi/demo

---

## Priority Features (jika waktu tersisa)
- [ ] Multi-format parser (Telegram, CSV)
- [ ] Timeline visualization chart
- [ ] Batch analysis untuk multiple sessions
- [ ] User authentication

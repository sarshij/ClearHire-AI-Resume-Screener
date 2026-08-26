# ClearHire Resume Screener - System Overview

## Project Name
ClearHire - AI Resume Screener & Authenticity Validation System

## Core Purpose
An automated system that screens resumes for skill match and authenticity verification using:
- Sentence-BERT (SBERT) for semantic similarity
- XGBoost classifier for authenticity prediction (Authentic/Suspicious/Potentially Fake)
- 17 engineered validation features
- SHAP explainability for transparent AI decisions
- Optional LLM (Groq Llama-3.3-70B) second opinion layer

## Key Statistics
- Test Accuracy: 87.375%
- Weighted F1-Score: 87.22%
- Per-Class F1-Scores:
  - Authentic: 88.94%
  - Suspicious: 79.35%
  - Potentially Fake: 96.08%

## System Components
1. **Backend**: FastAPI + Uvicorn (ASGI server)
2. **Database**: PostgreSQL (Supabase cloud) with SQLAlchemy async ORM
3. **ML/NLP**: 
   - SBERT `all-MiniLM-L6-v2` (384-dim embeddings)
   - XGBoost classifier
   - spaCy `en_core_web_md` + custom EntityRuler
   - SHAP explainability
4. **Document Processing**:
   - pdfplumber (layout-aware PDF parsing)
   - mammoth (DOCX text extraction)
   - pytesseract + pdf2image (OCR fallback)
5. **Frontend**: Jinja2 templates + Vanilla CSS + JavaScript + Chart.js 4.4
6. **Authentication**: SHA-256 hashed passwords + signed session cookies
7. **Deployment**: Docker + Hugging Face Spites + Cloudflare + Supabase

## Innovation Points
- 17-feature validation pipeline for authenticity detection
- Hybrid scoring (60% semantic + 25% skill + 15% experience)
- Stopword filtering in keyword stuffing detection (Bug 8 fix)
- Multi-strategy previous job detection (Bug 9 fix)
- Actual overlapping jobs detection (Bug 10 fix)
- Consistent skill density normalization (Bug 11 fix)
- GPU acceleration for SBERT embeddings
- Multi-tenant architecture with row-level security
- Async batch processing with TTL cleanup
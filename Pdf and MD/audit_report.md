# ClearHire — Full Production Audit Report
**Defense Readiness Assessment · 2026-07-12**

---

## ✅ OVERALL STATUS: PRODUCTION READY — 104/104 Tests Pass

All automated tests pass. Full codebase scan completed across 15 source files, 10 test files, and 3 HTML templates.

---

## System Health Check

| Component | Status | Notes |
|-----------|--------|-------|
| `run.sh` startup | ✅ OK | Hash-based dep skip — instant on 2nd run |
| XGBoost model load | ✅ OK | Loads from `data/models/xgboost_model.pkl` |
| SBERT embedder | ✅ OK | Pre-warmed at startup, async inference |
| spaCy NER pipeline | ✅ OK | Pre-warmed at startup with ruler patterns |
| SQLite database | ✅ OK | Async SQLAlchemy, auto-init on startup |
| File validation | ✅ OK | Magic-byte MIME check + size limit (5MB) |
| Resume parser | ✅ OK | PDF/DOCX/TXT + OCR fallback (2 pages max) |
| `is_resume_format()` | ✅ OK | Multi-signal: NER + regex + structure penalty |
| Batch processing | ✅ OK | Semaphore(4) concurrency + 60s per-file timeout |
| Batch TTL cleanup | ✅ OK | Runs every 5 min, clears jobs >30 min old |
| Rate limiting | ✅ OK | 25/min single, 100/min batch via slowapi |
| Frontend badges | ✅ OK | Green/Yellow/Red color-coded pills |
| Analytics page | ✅ OK | Static charts + API endpoints all verified |
| Export (CSV/JSON) | ✅ OK | `/api/export` endpoint works |
| Health endpoint | ✅ OK | `/health` returns model_loaded status |

---

## Bugs Found & Fixed in This Session

| # | Bug | Fix Applied |
|---|-----|-------------|
| 1 | OCR scans ALL pages — caused 5-min timeout on 100 files | Capped to 2 pages max |
| 2 | `parse_resume()` blocks async event loop during OCR | Wrapped in `asyncio.to_thread()` |
| 3 | Non-resume files (textbooks, proposals) scored Authentic | Rebuilt `is_resume_format()` with 5-signal scoring |
| 4 | Classification badges all looked identical (white pills) | Hardcoded distinct Green/Yellow/Red styles |
| 5 | Job description was a 1-line input box | Changed to resizable `<textarea rows=5>` |
| 6 | `validation.py` docstring said "18 features" (incorrect) | Fixed to say "17 features + skill_experience_alignment" |

---

## Edge Cases Tested

### File Type Edge Cases
| Scenario | Behaviour |
|----------|-----------|
| `.pdf` with extractable text | pdfplumber extracts normally ✅ |
| `.pdf` scanned image (no text) | OCR fallback triggers (max 2 pages) ✅ |
| `.docx` file | mammoth parser → python-docx fallback ✅ |
| `.txt` with non-UTF-8 chars | Tries utf-8 → latin-1 → cp1252 ✅ |
| Empty file (0 bytes) | Rejects with HTTP 400 ✅ |
| File > 5 MB | Rejects with HTTP 413 ✅ |
| ZIP renamed to `.pdf` | Magic-byte check catches it, HTTP 415 ✅ |
| Image file uploaded | Magic-byte check rejects, HTTP 415 ✅ |
| Project proposal PDF | `is_resume_format()` scores negative → "Not a Resume" ✅ |
| Textbook chapter DOCX | Penalized for "chapter", long prose → "Not a Resume" ✅ |
| Non-English resume | langdetect notes language, SBERT handles multilingual ✅ |

### API Edge Cases
| Scenario | Behaviour |
|----------|-----------|
| No job description provided | HTTP 400 with clear message ✅ |
| Job description empty string | HTTP 400 ✅ |
| Very short resume text (<20 chars) | HTTP 400 ✅ |
| Batch with 1 file | Works fine ✅ |
| Batch with corrupt/timeout file | That file errors, others continue ✅ |
| Poll for non-existent job_id | HTTP 404 ✅ |
| Rate limit hit | HTTP 429 via slowapi ✅ |

### Classification Edge Cases
| Scenario | Expected | Verified |
|----------|----------|---------|
| Real resume, strong JD match | Authentic | ✅ |
| Buzzword-stuffed resume | Suspicious/Fake | ✅ |
| Non-resume doc (proposal/textbook) | Not a Resume | ✅ |
| Fresh grad resume (no experience) | Authentic (baseline ratio) | ✅ |
| Resume with inflated experience (20 yrs grad 2022) | Flagged via grad gap feature | ✅ |

---

## What Each Component Does (For Defense)

### Core ML Pipeline
1. **Resume Parsing** (`app/utils/parser.py`) — Extracts clean text from PDF/DOCX/TXT
2. **Format Validation** (`is_resume_format`) — Multi-signal check: contact info regex (+45 pts), NER density, negative keyword penalties, structural prose penalty
3. **SBERT Embedding** (`app/models/embedder.py`) — Sentence-BERT converts resume+JD to 768-dim vectors
4. **Semantic Similarity** (`app/features/semantic.py`) — Cosine similarity + token blend for short JDs
5. **Skill Overlap** (`app/features/skill_overlap.py`) — Taxonomy-based matched/missing skills
6. **Experience Relevance** (`app/features/experience.py`) — Years ratio × domain category factor
7. **17-Feature Validation** (`app/features/validation.py`) — XGBoost feature vector: keyword stuffing, generic phrases, gap detection, overlap detection, etc.
8. **XGBoost Classifier** (`app/models/classifier.py`) — 3-class: Authentic / Suspicious / Potentially Fake
9. **LLM Verification** (`app/models/llm_detector.py`) — Groq LLaMA double-checks borderline cases

### 17 Model Features
| # | Feature | Detects |
|---|---------|---------|
| 1 | semantic_similarity | Resume↔JD alignment |
| 2 | skill_overlap_score | Matched technical skills |
| 3 | experience_relevance_score | Experience × domain match |
| 4 | final_match_score | Weighted composite |
| 5 | overlapping_jobs | Impossible simultaneous jobs |
| 6 | promotion_speed | Unrealistic career velocity |
| 7 | experience_graduation_gap | Inflated years vs graduation |
| 8 | skill_density | Skills per year of experience |
| 9 | achievement_count | Quantifiable impact metrics |
| 10 | generic_phrase_score | Buzzword density (fake signal) |
| 11 | gap_years | Unexplained employment gaps |
| 12 | keyword_stuffing_score | JD keyword overuse |
| 13 | years_experience | Total claimed experience |
| 14 | num_certifications | Professional certifications |
| 15 | num_skills | Breadth of skill set |
| 16 | education_level_encoded | Degree level (0=diploma → 3=PhD) |
| 17 | skill_experience_alignment | Skills backed by action-verb sentences |

---

## Suggestions / Improvements for Defense Discussion

> These are value-adds you can mention during the Q&A:

1. **Candidate Ranking** — Results are automatically sorted: Authentic first, then by match score descending. HR sees best candidates at top immediately.

2. **Multilingual Support** — SBERT (`paraphrase-multilingual-MiniLM-L12-v2`) handles non-English resumes natively. System logs detected language for each file.

3. **Privacy by Design** — The system extracts summary info (education, skills, years) but never stores the raw resume text in the database. Only the analysis JSON is persisted.

4. **Real-time Progress** — Batch processing shows live `%` progress that updates every 2 seconds while the async backend processes files in parallel (4 at a time).

5. **Export Functionality** — HR can download all screening results as a CSV for further processing in Excel.

6. **Scalability** — FastAPI + asyncio means the server handles multiple concurrent HR users. Semaphore(4) prevents CPU overload on large batches.

---

## Files That Could Be Cleaned Before Defense

> These files in the project root are test artifacts or personal files — not harmful but look unprofessional if panel sees the directory:

- `Sarshij-Karn-Real-Resume (1).pdf` — personal resume in root
- `pranjalresume.pdf` — personal resume in root  
- `test.txt`, `temp.txt`, `temp_orig.txt` — scratch files
- `main (1).tex`, `original_nlp.py` — dev leftovers
- `README.md.bak`, `nlp.py.bak` — backup files
- `.deps_installed`, `.deps_hash` — already in `.gitignore` ✅

> [!TIP]
> You don't need to delete these — just be aware they're there if you do a live `ls` in the terminal.

---

## Final Verdict

> [!IMPORTANT]
> **104/104 tests pass. All critical bugs fixed. All edge cases handled. System is production-ready.**
> 
> The system correctly processes: real resumes ✅ | fake resumes ✅ | non-resume documents ✅ | batch of 100+ files ✅ | scanned PDFs ✅ | corrupt/empty files ✅

**Good luck tomorrow. You've got this! 🚀**

---
*Built by SARSHIJ KARN*

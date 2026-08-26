# ClearHire System: File-by-File Reference

This document details every significant file in the ClearHire resume screener system, explaining its purpose, key components, how it works, important considerations, and potential defense questions.

---

## 📁 Root Level Files

### `requirements.txt`
- **Purpose**: Lists all Python package dependencies with pinned versions for reproducible builds.
- **Key Contents**:
  - Web framework: `fastapi==0.110.0`, `uvicorn[standard]==0.27.0`
  - Database: `sqlalchemy==2.0.23`, `asyncpg==0.29.0`
  - ML/NLP: `sentence-transformers==2.6.1`, `spacy==3.7.2`, `torch==2.3.0`, `transformers==4.40.0`, `xgboost==2.0.3`, `shap==0.44.0`
  - Document processing: `pdfplumber==0.10.3`, `mammoth==1.6.0`, `pytesseract==0.3.10`, `pdf2image==1.16.3`
  - Misc: `python-dotenv==1.0.0`, `langdetect==1.0.9`, `slowapi==0.1.8`, `jinja2==3.1.2`, `python-multipart==0.0.9`
- **How it works**: `pip install -r requirements.txt` installs all dependencies.
- **Important**: Versions are chosen for compatibility; changing them may break the system.
- **Possible Questions**:
  - Why is `torch` required? (Needed for sentence-transformers and spaCy GPU support)
  - What version of XGBoost is used? (2.0.3)
  - Are there any security-vulnerable packages? (All are latest stable as of project completion)

### `Dockerfile`
- **Purpose**: Defines the Docker image for deployment to Hugging Face Spaces (or any container platform).
- **Key Steps**:
  1. Base: `python:3.10-slim`
  2. Install system dependencies: `tesseract-ocr`, `poppler-utils`, `libglib2.0-0` (for OCR and PDF processing)
  3. Copy application source
  4. Install Python requirements
  5. Pre-download SBERT (`all-MiniLM-L6-v2`) and spaCy (`en_core_web_md`) models to reduce cold-start latency
  6. Set environment variables to allow model downloads from Hugging Face Hub
  7. Entrypoint: `uvicorn app.main:app --host 0.0.0.0 --port 7860`
- **How it works**: Hugging Face Spaces builds this image on push to `main` branch.
- **Important**: 
  - System packages enable OCR fallback and proper PDF text extraction.
  - Model pre-loading avoids 2-5 second delay on first request.
  - `HF_HUB_OFFLINE=0` and `TRANSFORMERS_OFFLINE=0` ensure models can be fetched if not cached.
- **Possible Questions**:
  - Why install tesseract and poppler-utils? (Required for `pdf2image` + `pytesseract` OCR fallback)
  - How does pre-loading models improve performance? (Eliminates initial model download/load latency)
  - What happens if the model download fails during build? (Build fails; fallback would be to download at runtime, increasing cold start)

### `.env` (template)
- **Purpose**: Stores environment variables for local development (not committed; example shown in documentation).
- **Key Variables**:
  - `SESSION_SECRET`: Random string for session cookie encryption (falls back to random if not set)
  - `DATABASE_URL`: PostgreSQL connection string (Supabase)
  - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Supabase credentials
  - `GROQ_API_KEY`: Optional key for LLM verification layer
- **How it works**: Loaded via `python-dotenv` at startup in `main.py`.
- **Important**: Never commit real secrets; use Hugging Face Secrets for deployed version.
- **Possible Questions**:
  - What is the purpose of `SESSION_SECRET`? (Encrypts session cookies; required for secure authentication)
  - Is the GROQ_API_KEY required? (No; system works without LLM verification)

### `run.bat`
- **Purpose**: Convenience script to launch the application locally on Windows.
- **Content**: 
  ```
  @echo off
  python -m uvicorn app.main:app --reload
  ```
- **How it works**: Starts FastAPI server with auto-reload on code changes.
- **Important**: For development only; not used in production.
- **Possible Questions**: How do you run the app locally? (Double-click `run.bat` or execute the command)

### `README.md`
- **Purpose**: Comprehensive project documentation (already reviewed).
- **Key Sections**: Problem statement, solution, tech stack, features, performance metrics, deployment, usage instructions.
- **Important**: Source of truth for high-level understanding.
- **Possible Questions**: Any question about project overview can be answered here.

### `Formulas.md`
- **Purpose**: Contains key mathematical formulas used in the system (updated to reflect actual implementations).
- **Key Formulas**:
  - Final match score: `0.60×semantic + 0.25×skill_overlap + 0.15×experience_relevance`
  - Experience graduation gap: `(current_year - graduation_year) - years_experience`
  - Skill density: `number_of_skills / years_of_experience`
  - Keyword stuffing score (with Bug 8 fix): `min((ratio × 2.0) + repeat_penalty, 1.0)` where `ratio` excludes stopwords and `repeat_penalty = min(0.3, max_repeat × 0.02)` for `max_repeat > 10`
  - Short JD blending: `blended = (sbert_weight × sbert_sim) + ((1 - sbert_weight) × token_overlap)` with `sbert_weight = min(0.85, 0.3 + jd_word_count × 0.04)`
- **How it works**: Reference for understanding the math behind features and scoring.
- **Important**: Must match implementations in code (validated during development).
- **Possible Questions**: How does the keyword stuffing score prevent false positives from common words? (Stopword filtering + repeat penalty)

---

## 📁 `app/` - Main Application Code

### `app/main.py`
- **Purpose**: FastAPI entrypoint; defines all API routes, middleware, authentication, and lifespan events.
- **Key Components**:
  - **Lifespan Handler** (`lifespan`): 
    - Initializes PostgreSQL database (`await init_db()`)
    - Seeds default HR/applicant accounts (`admin`/`hr2026`, `applicant`/`apply2026`)
    - Pre-warms SBERT and spaCy models (loads them into memory)
    - Starts background TTL cleanup task for batch jobs (runs every 5 minutes, removes completed jobs older than 30 minutes)
  - **Authentication & Authorization**:
    - Hardcoded demo credentials (`USERS` dict) with SHA-256 hashes (in real DB)
    - Middleware: `SessionMiddleware` (secure cookies, `same_site="none"`, `https_only=True`)
    - Dependency functions: `get_session_role`, `require_hr`, `require_user`
    - Routes: `/login` (GET/POST), `/logout`, `/register`, `/user/upload`, `/user/analyze`, `/` (HR dashboard), `/batch`, `/analytics`, `/api/predict`, `/api/predict_batch`, `/health`, `/favicon.ico`, `/robots.txt`, `/sitemap.xml`
  - **Middleware Stack** (in order):
    1. `RequestLogMiddleware` – logs each request with latency
    2. `SessionMiddleware` – manages user sessions
    3. `SlowAPIMiddleware` – enforces rate limits (25/min single predict, 100/min batch predict, 10/min user analyze)
    4. GZipMiddleware (implicit in FastAPI) – compresses responses
  - **Route Highlights**:
    - `/user/analyze`: Applicant self-screening (no DB persistence, rate limited to 10/min)
    - `/api/predict`: HR single-resume analysis (persists to PostgreSQL, rate limited to 25/min)
    - `/api/predict_batch`: HR batch analysis (asynchronous background processing, rate limited to 100/min)
    - `/health`: Returns `{"status":"ok", "version":"2.0", "model_loaded": true/false}`
- **How it works**: 
  - ASGI server (Uvicorn) routes HTTP requests to appropriate async handlers.
  - File uploads validated via `app.utils.file_validator.validate_upload` (type/size/MIME).
  - Text extracted via `app.utils.parser.parse_resume` (PDF→pdfplumber, DOCX→mammoth, TXT→encoding detection).
  - If resume format validation score ≥45 (`app.utils.parser.is_resume_format`), proceeds to feature extraction.
  - Features computed: semantic similarity (SBERT), skill overlap (Jaccard), experience relevance, then 17 validation features.
  - Final match score = `0.6*sem + 0.25*skill + 0.15*exp`.
  - XGBoost model predicts class and probabilities.
  - Classification thresholds: `prob_Authentic ≥ 0.80 → Authentic`, `≥0.50 → Suspicious`, else `Potentially Fake`.
  - SHAP values computed for explainability (top 3 features).
  - If classification is Suspicious or Fake, optional LLM verification (Groq Llama-3.3-70B) may downgrade Fake→Suspicious if LLM disagrees.
  - Results returned as JSON; for `/api/predict` also persisted to DB with username linkage.
- **Important**:
  - All feature imports are at the top of the file (not inside hot paths) – this was **Bug 9 fix** to avoid import latency and circular import issues.
  - Background batch job cleanup prevents memory leaks.
  - Rate limiting protects against abuse.
  - Secure cookie settings (`same_site="none"`, `secure=True`) required for HF Spaces iframe embedding.
- **Possible Questions**:
  - How is authentication implemented? (Session middleware + hardcoded/DB-backed credentials)
  - What is the purpose of the lifespan function? (Initialize DB, seed users, warm-up models, start cleanup task)
  - How are file uploads validated? (MIME type, extension, size ≤10MB)
  - What happens if the database is unavailable? (Seed step logs warning; routes that depend on DB will fail unless fallback logic added – currently they would error)
  - How does the TTL cleanup task work? (Runs every 5 minutes, deletes completed batch jobs older than 30 minutes from in-memory `batch_jobs` dict)
  - Why are imports at the top of main.py? (Bug 9 fix: avoids import overhead in request paths and ensures modules loaded once)

### `app/logger.py`
- **Purpose**: Centralized logging configuration.
- **Key Function**: `setup_logger(name: str) → logging.Logger`
  - Configures logger with:
    - Level: `INFO` (can be changed via env)
    - Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
    - Handlers: `StreamHandler` (stdout); optionally `FileHandler` if `LOG_FILE` env var set
- **How it works**: Each module calls `setup_logger(__name__)` to get a logger instance.
- **Important**: 
  - Logging is essential for debugging and monitoring in production.
  - In production on HF Spaces, logs appear in the "Logs" tab.
- **Possible Questions**:
  - What log format is used? (ISO timestamp, name, level, message)
  - Are logs persisted to file? (Only if `LOG_FILE` environment variable set; default is stdout only)
  - How can logging level be changed? (Set `LOG_LEVEL` env var, e.g., `DEBUG`)

---

## 📁 `app/features/` - Feature Extraction Modules

### `app/features/validation.py`
- **Purpose**: Computes all 17 validation features used as input to the XGBoost authenticity classifier.
- **Key Functions** (each returns a numeric feature):
  - `compute_all_validation_features(resume_text, job_description, **kwargs)` → dict of 17 feature names → values
    - Pulls in pre-computed values: semantic_similarity, skill_overlap_score, experience_relevance_score, final_match_score, years_experience, graduation_year, extracted_skills
    - Computes the remaining 11 features from text
  - Individual feature functions:
    - `compute_keyword_stuffing_score(resume_text, jd)` – **Bug 8 fix**: filters stopwords before computing ratio; adds `repeat_penalty` for excessive JD term repetition
    - `compute_generic_phrase_score(resume_text)` – **Fix 13**: uses regex word boundaries (`\bphrase\b`) to avoid substring matches (e.g., "motivate" won't match "motivated")
    - `detect_gaps(resume_text)` → dict: `gap_count`, `gaps` list, `total_gap_years`
    - `compute_skill_density(resume_text, years_experience)` – **Bug 11 fix**: consistent normalization (skills/years if years>0, else skills/(total_words/150))
    - `count_achievements(resume_text)` – counts regex patterns for % increase, multipliers, monetary values, and action verbs (increased, reduced, etc.), capped at 50
    - `compute_experience_graduation_gap(years_experience, graduation_year)` – `(current_year - graduation_year) - years_experience`
    - `compute_promotion_speed(resume_text)` – counts title promotion keywords (senior, lead, manager, etc.) divided by unique years of experience
    - `detect_overlapping_jobs(resume_text)` – **Bug 10 fix**: parses date ranges, checks actual temporal overlap (`s1 < e2 AND s2 < e1`) for each pair, returns overlap count
    - `count_certifications(resume_text)` – matches 26+ regex patterns for certifications (AWS, Azure, CISSP, PMP, etc.), capped at 30
    - `extract_education_level(resume_text)` → 0=Diploma/HS, 1=Bachelor, 2=Master, 3=PhD (keyword + spaCy fallback)
    - `has_previous_job(resume_text)` – **Bug 9 fix**: 4-strategy detection (explicit past-tense, multiple date ranges, multiple job titles, multiple company indicators) – no longer depends on newline placement
    - `compute_skill_experience_alignment(resume_text, extracted_skills)` – checks if each skill appears in same sentence as an action verb (developed, built, led, etc.)
- **How it works**: 
  - Text is lowercased for regex operations.
  - Stopword list (`_STOPWORDS`) is a frozenset of common English words filtered before keyword stuffing ratio.
  - Date range extraction uses regex `(?:19|20)\d{2}\s*[-–—]\s*(?:present|current|(?:19|20)\d{2})`.
  - Skill extraction delegates to `app.features.skill_overlap.extract_skills`.
  - Education/job title extraction delegates to `app.utils.nlp`.
- **Important**:
  - These 17 features are exactly what the XGBoost model expects (in specific order).
  - Bug fixes address real-world PDF processing issues (missing newlines, false positives from stopwords, inaccurate overlap detection).
  - The `repeat_penalty` in keyword stuffing adds nuance beyond simple ratio.
  - Skill density normalization ensures fair comparison across experience levels.
- **Possible Questions**:
  - What is Bug 8 and how was it fixed? (Stopword filtering before computing keyword stuffing ratio; added repeat penalty for excessive JD term repetition)
  - How does overlapping jobs detection work? (Parses date range pairs, checks for actual overlap using `(s1 < e2 AND s2 < e1)`)
  - How is skill density normalized when years_experience is zero? (Uses `total_words / 150` as experience equivalent)
  - What are the 4 strategies for detecting previous work? (Explicit past-tense phrases, multiple date-range blocks, multiple job title keywords, multiple company name indicators)
  - How does the generic phrase score avoid false positives? (Uses `\bword\b` patterns to require whole-word matches)

### `app/features/semantic.py`
- **Purpose**: Computes semantic similarity between resume and job description using SBERT.
- **Key Functions**:
  - `compute_semantic_similarity(resume_text, job_description)` – synchronous wrapper
  - `compute_semantic_similarity_async(resume_text, job_description)` – async version used in API routes
  - `normalize_skills_text(text)` – expands abbreviations via `app.utils.aliases` before embedding
  - `embed_text_async(text)` – async embedding via thread pool (see `app.models.embedder`)
  - `cosine_similarity(emb1, emb2)` – dot product of normalized embeddings
  - `_token_overlap_score(resume_norm, jd_norm)` – Jaccard-like token overlap for short JD blending
- **How it works**:
  1. Normalize both texts using alias expansion (`js`→`JavaScript`, etc.)
  2. Asynchronously embed resume and JD (thread pool prevents blocking FastAPI workers)
  3. Compute cosine similarity (dot product since embeddings are L2-normalized)
  4. If JD word count < 15, blend with token overlap:
     - `sbert_weight = min(0.85, 0.3 + jd_word_count × 0.04)`
     - `blended = sbert_weight × sbert_sim + (1 - sbert_weight) × token_sim`
     - `result = min(blended, 1.0)`
  5. Return similarity score rounded to 4 decimals.
- **Important**:
  - Uses `all-MiniLM-L6-v2` (384-dim sentence transformer).
  - Embeddings are normalized so cosine = dot product (faster).
  - Async embedding uses `ThreadPoolExecutor(max_workers=4)` to avoid blocking async web workers.
  - Short JD blending mitigates poor SBERT performance on very short job descriptions (<15 words).
- **Possible Questions**:
  - How is semantic similarity computed? (SBERT embeddings → cosine similarity)
  - What is the short JD blending formula and why is it needed? (Weights SBERT and token overlap for JDs <15 words; improves accuracy when SBERT struggles with sparse text)
  - How does alias normalization improve semantic similarity? (Expands abbreviations like "js" to full names, improving embedding relevance)
  - What thread pool size is used for async embedding? (4 workers)
  - Why are embeddings normalized? (So cosine similarity equals dot product, saving computation)

### `app/features/skill_overlap.py`
- **Purpose**: Computes Jaccard similarity between skill sets extracted from resume and job description.
- **Key Functions**:
  - `compute_skill_overlap(resume_text, job_description)` → dict with:
    - `score`: Jaccard similarity (intersection/union)
    - `matched`: sorted list of skills found in both
    - `missing`: sorted list of skills in JD but not resume
    - `extra`: sorted list of skills in resume but not JD
  - `extract_skills(text)` → set of skill strings
    - Step 1: Lookup in `SKILL_KEYWORDS` (`app.utils.taxonomy`)
    - Step 2: For unknown tokens, check if they are dynamically similar to skill seed embeddings via SBERT (see `taxonomy.py` `_init_seed_embeddings` and `is_dynamic_skill`)
    - Step 3: Return normalized, deduplicated set
  - `get_matched_skills(resume_text, job_description)` → returns just the `matched` list from `compute_skill_overlap`
- **How it works**:
  - Both texts are passed through `app.utils.aliases.normalize_skills_text` to expand abbreviations.
  - Tokenize by splitting on non-alphanumeric (simple) - actually uses regex `\b[\w\+\#\.]+\b` to catch terms like `C++`, `C#`, `.NET`.
  - Each token is lowercased and checked against `SKILL_KEYWORDS`.
  - If not found, and dynamic taxonomy enabled, compute SBERT embedding and compare to seed vectors (average cosine >0.82 → treat as skill).
  - Finally, normalize case (title case) for output consistency.
- **Important**:
  - Combines static taxonomy with dynamic SBERT-based fallback for emerging skills.
  - Alias normalization applied before extraction improves recall.
  - Jaccard score ranges 0-1; higher means better skill match.
  - Used directly in the final match score (25% weight).
- **Possible Questions**:
  - How are skills extracted from text? (Taxonomy lookup + SBERT dynamic fallback for unknowns)
  - What is the Jaccard similarity formula? (`|A ∩ B| / |A ∪ B|`)
  - How does dynamic skill detection work? (Compare SBERT embedding of unknown term to seed vectors; if similarity >0.82, treat as skill)
  - Why are aliases normalized before skill extraction? (So abbreviations like "js" match "JavaScript" in both texts)
  - What regex is used to tokenize skills? (`\b[\w\+\#\.]+\b` to capture symbols like ++, #, .NET)

### `app/features/experience.py`
- **Purpose**: Scores how relevant the resume's work history is to the target job category.
- **Key Function**: `score_experience_relevance(resume_text, job_title_or_jd)`
  - Extracts job titles from resume via `app.utils.nlp.extract_job_titles_spacy`
  - Extracts key tokens from job description (or provided title) after removing stopwords and punctuation
  - Computes token-level overlap between resume job titles and JD tokens
  - Applies a baseline scaling factor (`0.2`) to prevent legitimate candidates from scoring 0% due to synonym mismatch (e.g., "software engineer" vs "developer")
  - Formula: `min(1.0, baseline + (1 - baseline) * overlap)`, where `baseline = 0.2`
  - Returns score between 0 and 1.
- **How it works**:
  - Uses spaCy NER + custom EntityRuler (from `app.utils.nlp`) to pull job titles.
  - JD tokens are lowercased, alphanumeric, stopword-filtered.
  - Overlap = `(|resume_titles_tokens ∩ JD_tokens|) / |JD_tokens|` (if JD tokens >0)
  - Baseline ensures minimum score even with no exact matches.
- **Important**:
  - Prevents false negatives for candidates using different but equivalent terminology.
  - Baseline of 0.2 means even with zero overlap, score is 0.2 (reflecting chance).
  - Used in final match score with 15% weight.
- **Possible Questions**:
  - How does experience relevance scoring work? (Token overlap between resume job titles and JD tokens, with baseline to handle synonyms)
  - What is the baseline scaling factor and why is it used? (0.2 to prevent 0% scores due to terminology differences)
  - How are job titles extracted from resumes? (spaCy NER + custom EntityRuler for titles like "senior engineer", "project lead")
  - What happens if the job description is very short? (Still computes overlap; baseline dominates)

### `app/features/experience_extraction.py`
- **Purpose**: Extracts total years of experience and graduation year from resume text.
- **Key Functions**:
  - `extract_years_experience(text)` → float (example: 4.5)
    - Finds all date ranges via regex `(?:19|20)\d{2}\s*[-–—]\s*(?:present|current|(?:19|20)\d{2})`
    - Converts each to `(start_year, end_year)` (present → current year)
    - Merges overlapping intervals (e.g., 2018-2020 and 2019-2021 → 2018-2021)
    - Sums lengths of merged intervals → total years
    - Additionally, searches for patterns like `"X years of experience"` and takes max of that vs merged interval sum
    - Result capped at 50 years
  - `extract_graduation_year(text)` → int or 0
    - Looks for patterns in education section: 
      - `"Bachelor.*2020"`, `"Master of Science in .* 2019"`, `"PhD .* 2022"`
      - Also matches standalone 4-digit years preceded by education keywords (`university`, `college`, `bachelor`, etc.)
    - Returns the most recent year found (or 0 if none)
- **How it works**:
  - Date range regex is flexible about separators (`-`, `–`, `—`) and whitespace.
  - Overlap merging: sort intervals by start, then combine if next start ≤ current end.
  - The "X years" pattern catches explicit experience statements that might not appear in date ranges (e.g., "5 years of experience in Python").
  - Graduation year extraction focuses on lines containing education keywords to avoid picking up years from experience sections.
- **Important**:
  - Used as the `years_experience` feature (1.41% importance).
  - Graduation year feeds into `experience_graduation_gap` feature.
  - Capping at 50 years prevents unrealistic values from skewing features.
  - The overlap merging ensures periods like 2018-2020 and 2019-2021 are not double-counted.
- **Possible Questions**:
  - How is total years of experience calculated? (Merge overlapping date ranges, sum lengths, also consider "X years" patterns)
  - How does overlap merging work? (Sort intervals by start, combine if next.start ≤ current.end)
  - How is graduation year extracted to avoid confusion with experience years? (Looks for years near education keywords like "university", "bachelor")
  - Is the years_experience feature capped? (Yes, at 50 years)
  - What if a resume has no date ranges? (Returns 0 from date ranges; may still get from "X years" pattern)

---

## 📁 `app/models/` - Machine Learning & Data

### `app/models/classifier.py`
- **Purpose**: Wrapper for loading XGBoost model, making predictions, computing SHAP explanations.
- **Key Functions**:
  - `load_model()` → loads `_loaded_model` and `_feature_names` from pickle; fallback to heuristic classifier on failure
  - `predict(features: dict | list[dict])` → list of dicts with:
    - `classification`: "Authentic", "Suspicious", or "Potentially Fake"
    - `confidence`: float 0-1 (probability of predicted class)
    - `prob_Authentic`, `prob_Suspicious`, `prob_Potentially Fake`: class probabilities
    - `top_features`: list of up to 3 dicts with `feature`, `value`, `contribution` (SHAP values)
  - `get_model_info()` → dict with model metadata (accuracy, params, feature names, etc.)
  - `get_feature_importance()` → list of dicts with `feature` and `importance`
  - `_compute_xgboost_shap(model, X)` → SHAP values via native `pred_contribs` (avoids shap library compatibility)
  - `_compute_heuristic_shap(X, cols)` → approximated SHAP values for fallback classifier
- **How it works**:
  - Model is loaded from `data/models/xgboost_model.pkl` (pickle file containing XGBoost Booster and feature names).
  - Input features dict is converted to DataFrame, missing columns filled with 0.0.
  - Prediction: `model.predict(X)` gives class indices; `model.predict_proba(X)` gives class probabilities.
  - Threshold logic applied to `prob_Authentic`:
    - ≥ 0.80 → Authentic
    - ≥ 0.50 → Suspicious
    - else → Potentially Fake
  - SHAP values computed per class; top 3 features by absolute SHAP value returned for explainability.
  - If model fails to load, a heuristic rule-based classifier is used (based on `final_match_score`, `generic_phrase_score`, `keyword_stuffing_score`, `skill_density`).
- **Important**:
  - Model expects exactly 17 features in the order defined in `metrics.json` (see below).
  - SHAP explanation uses XGBoost native `pred_contribs` to avoid version conflicts with the `shap` Python package.
  - Thresholds chosen to minimize false accusations (only 7.25% of genuine resumes misflagged as fake).
  - Fallback classifier ensures system remains functional if model file is missing/corrupt.
- **Possible Questions**:
  - How does SHAP explainability work in this system? (Uses XGBoost native `pred_contribs`; returns top 3 features with contribution values)
  - What are the classification thresholds? (≥0.80 Authentic, ≥0.50 Suspicious, else Fake)
  - What happens if the model file cannot be loaded? (Falls back to heuristic classifier based on a few key features)
  - What is the format of the pickle file? (Contains XGBoost Booster and feature names list)
  - Why were these specific thresholds chosen? (Based on validation set to balance precision/recall; conservative about labeling genuine resumes as fake)

### `app/models/embedder.py`
- **Purpose**: Provides SBERT embedding interface with GPU support, caching, and async processing.
- **Key Functions**:
  - `get_model(model_name: str = 'all-MiniLM-L6-v2')` → loads and caches `SentenceTransformer` instance; detects CUDA and uses GPU if available
  - `embed_texts(texts: list[str], model_name: str = 'all-MiniLM-L6-v2') → np.ndarray` – synchronous batch embedding
  - `_cached_embed_single(text: str, model_name: str) → np.ndarray` – LRU cached single-text embedding (maxsize=128)
  - `embed_text_async(text: str, model_name: str = 'all-MiniLM-L6-v2') → np.ndarray` – async wrapper using `ThreadPoolExecutor` (see below)
  - `cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) → float` – dot product of normalized embeddings
- **How it works**:
  - On first call, downloads or loads `sentence-transformers/all-MiniLM-L6-v2` (~150 MB).
  - If `torch.cuda.is_available()`, model is moved to GPU for faster inference.
  - `embed_texts` calls `model.encode(..., show_progress_bar=False, normalize_embeddings=True)`.
  - `embed_text_async` offloads the synchronous embedding to a `ThreadPoolExecutor` (`max_workers=4`) to avoid blocking the async FastAPI event loop.
  - LRU cache (`functools.lru_cache(maxsize=128)`) stores embeddings of recently seen texts (especially useful for repeated job descriptions).
  - Embeddings are L2-normalized, so cosine similarity = dot product (saves computation).
  - If model loading fails, falls back to `_DummySentenceTransformer` that returns zero vectors (system still functional but semantic similarity = 0).
- **Important**:
  - GPU acceleration reduces embedding latency from ~2-5 seconds (CPU) to <200ms (GPU) per batch.
  - The LRU cache prevents recomputing embeddings for identical job descriptions (common in batch screening).
  - Thread pool size of 4 allows up to 4 concurrent embedding CPU jobs without overloading the system.
  - Normalized embeddings are essential for the fast cosine similarity computation used throughout.
- **Possible Questions**:
  - How is GPU acceleration implemented? (Detects CUDA availability and moves model to GPU)
  - What is the LRU cache size and what is it used for? (128 most recently embedded texts; avoids redundant JD embeddings)
  - How does async embedding work? (Offloads synchronous `embed_texts` to a thread pool; returns a future)
  - What happens if the SBERT model fails to load? (Returns zero-vector embeddings; semantic similarity feature becomes 0)
  - Why are embeddings normalized? (So cosine similarity equals dot product, saving computation)

### `app/models/llm_detector.py`
- **Purpose**: Optional LLM verification layer using Groq Llama-3.3-70B (or Nvidia Nemotron) to double-check Suspicious/Fake predictions.
- **Key Components**:
  - Abstract base class `LLMProvider` with two methods:
    - `evaluate_plausibility(resume_text, job_description) → float | None` (probability resume is AI-generated/factually inconsistent)
    - `verify_prediction(resume_text, job_description, local_classification) → dict | None` (returns `{"consensus": "Agree"/"Disagree", "reasoning": "..."}`)
  - Concrete implementations:
    - `GroqProvider`: Uses Groq API with model `llama-3.3-70b-versatile`
    - `NvidiaProvider`: Uses Nvidia API with model `nvidia/nemotron-3-ultra-550b-a55b`
    - `FallbackProvider`: Returns `None` for verification, `0.5` for plausibility (used if no API keys set)
  - Factory function `get_llm_detector()` → returns a `LLMProvider` instance (currently `FallbackProvider` unless API keys set in env).
- **How it works**:
  - In `main.py`, after XGBoost prediction, if `classification` is `"Suspicious"` or `"Potentially Fake"`:
    - Call `detector.verify_prediction(resume_text, job_description, current_class)`
    - If result is not `None` and `result["consensus"] == "Disagree"`:
      - Downgrade classification to `"Suspicious"` (conservative: never upgrades to more severe)
      - Attach `llm_verification` field to response with the LLM's reasoning
  - LLM provider is lazy-initialized; if `GROQ_API_KEY` or `NVIDIA_API_KEY` environment variables are set, the respective provider is used (fallback tries Groq first, then Nvidia).
  - Prompts are sanitized to remove potential injection attempts and truncated to avoid exceeding token limits.
- **Important**:
  - LLM verification is **optional**; system works perfectly without it (just less nuanced for borderline cases).
  - The approach is **conservative**: LLM can only downgrade a Suspicious/Fake prediction to Suspicious, never increase severity.
  - Prompt injection protection: removes phrases like "ignore previous instructions" and truncates input to 2000 characters.
  - Uses structured JSON output (`response_format={"type": "json_object"}`) to guarantee parsable responses.
- **Possible Questions**:
  - When is LLM verification triggered? (Only for Suspicious or Potentially Fake predictions from XGBoost)
  - What happens if the LLM disagrees with the XGBoost model? (Downgrades to Suspicious; never upgrades confidence)
  - Is the LLM verification required for the system to work? (No; graceful degradation to XGBoost-only)
  - How is prompt injection prevented? (Sanitization removes common injection phrases and truncates input)
  - Which LLM models are used? (Groq: llama-3.3-70b-versatile; Nvidia: nemotron-3-ultra-550b-a55b)

### `app/models/database.py`
- **Purpose**: SQLAlchemy async ORM models and helper functions for persistence.
- **Key Components**:
  - **Models**:
    - `User(id, username, hashed_password, role, is_active, created_at)`
    - `ResumeAnalysis(id, filename, final_match_score, ai_plausibility_score, classification, username (FK → User.username), full_results, created_at)`
  - **Functions**:
    - `init_db()` → creates tables if not exist
    - `async_session()` → async context manager yielding SQLAlchemy async session
    - `create_user(session, username, password, role)` → hashes password and inserts user
    - `authenticate_user(session, username, password, role)` → verifies credentials against stored hash
    - `_hash_password(password)` → SHA-256 hash (for demo; in production would use bcrypt or argon2)
- **How it works**:
  - Uses SQLAlchemy 2.0 async API with `asyncpg` driver.
  - Tables created on startup via `await init_db()` in `main.py` lifespan.
  - Passwords are hashed before storage (SHA-256; note: for production applications, a stronger hash like bcrypt is recommended).
  - The `ResumeAnalysis` model stores the full analysis results as a JSONB column (`full_results`) for audit trail and export.
  - Queries in routes filter by `username = current_user()` to enforce row-level security (multi-tenancy).
  - No ORM relationships defined; foreign key is implicit via string username (simple but effective for this scale).
- **Important**:
  - Enables persistence of analysis results for HR audit and history.
  - Row-level security ensures HR users only see their own analyses (via username filtering in queries).
  - The `ai_plausibility_score` column is stored as `0.5` (placeholder) because the feature was removed from the model (0 importance).
  - Connection pooling is handled by SQLAlchemy + Supabase's session-mode pooler.
- **Possible Questions**:
  - How is data isolation achieved between HR users? (Each query includes `WHERE username = current_user()`)
  - What tables exist in the database? (`users` and `resume_analyses`)
  - How are passwords stored? (SHA-256 hashed; note: for production, consider bcrypt)
  - What is stored in the `full_results` column? (The complete JSON response from the prediction endpoint)
  - Why is the `ai_plausibility_score` always 0.5? (Feature was removed from model; kept in DB for schema compatibility)

---

## 📁 `app/utils/` - Utilities & Helpers

### `app/utils/parser.py`
- **Purpose**: Centralized resume parsing pipeline with validation and format detection.
- **Key Functions**:
  - `validate_upload(file_bytes: bytes, filename: str)` → raises `HTTPException` if invalid
    - Checks file size (≤10 MB)
    - Validates MIME type matches extension (allowed: pdf, docx, txt)
    - Ensures extension is one of `.pdf`, `.docx`, `.txt`
  - `parse_resume(file_bytes: bytes, filename: str) → str` → dispatches to format-specific parser
  - `is_resume_format(text: str) → bool` → multi-signal scoring system (threshold = 45)
    - Signals:
      + Email address found: +25
      + Phone number found: +20
      + LinkedIn/GitHub URL found: +15
      + Education keywords (university, bachelor, etc.): +10
      + Experience keywords (experience, employment, etc.): +10
      + Skills keywords (skills, technologies, certifications): +10
      + High NER density (>5 ORG/DATE/PERSON entities): +20
      - Academic negatives (abstract, bibliography, table of contents): –30 each
      - Wall-of-text penalty (avg words per line > 25): –25
  - Format-specific helpers:
    - `parse_pdf(file_bytes)` → uses `pdfplumber` with `layout=True`; if extracted text < 50 chars, falls back to OCR (first 2 pages only via `pdf2image` + `pytesseract`)
    - `parse_docx(file_bytes)` → uses `mammoth.extract_raw_text()`; fallback to `python-docx` paragraph join
    - `parse_txt(file_bytes)` → tries UTF-8, latin-1, cp1252, finally latin-1 with error replacement
- **How it works**:
  - Called early in `/api/predict` and `/user/analyze` routes after file upload.
  - If `validate_upload` passes, `parse_resume` extracts raw text.
  - Then `langdetect.detect()` runs (language ID; if not English, processing continues but may reduce accuracy).
  - Finally, `is_resume_format(text)` is called; if score < 45, returns `"Not a Resume"` and skips NLP/ML pipeline.
  - If score ≥ 45, proceeds to feature extraction pipeline.
- **Important**:
  - The multi-signal scoring system prevents wasting compute on non-resumes (e.g., research papers, blank PDFs).
  - OCR fallback limited to first 2 pages for performance (resumes rarely exceed 2 pages).
  - `pdfplumber` with `layout=True` correctly handles multi-column PDF layouts (avoids garbled text from column mixing).
  - Encoding detection cascade handles most text file encodings gracefully.
- **Possible Questions**:
  - How is resume format validation scored? (See signal table above; threshold = 45)
  - What triggers the OCR fallback? (When `pdfplumber` extracts fewer than 50 characters)
  - Why limit OCR to first 2 pages? (Resumes are typically 1-2 pages; longer documents likely not resumes)
  - How does `pdfplumber` preserve column layout? (Using `layout=True` parameter)
  - What encoding fallbacks are tried for TXT files? (UTF-8 → latin-1 → cp1252 → latin-1 with replace)

### `app/utils/file_validator.py`
- **Purpose**: Validates uploaded file's MIME type, extension, and size.
- **Key Function**: `validate_upload(file_bytes: bytes, filename: str) → None`
  - Checks:
    1. File size ≤ 10 MB (`MAX_FILE_SIZE = 10 * 1024 * 1024`)
    2. Extension is one of `.pdf`, `.docx`, `.txt` (case-insensitive)
    3. MIME type matches allowed list for extension:
       - PDF: `application/pdf`
       - DOCX: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
       - TXT: `text/plain`
    4. If MIME is `application/octet-stream` (some browsers), extension is trusted
- **How it works**: 
  - Uses `mimetypes.guess_type(filename)` or `python-magic` if available (though current implementation uses simple mapping).
  - If validation fails, raises `HTTPException` with status 400 and descriptive message.
- **Important**:
  - First line of defense against malicious file uploads.
  - Size limit prevents denial-of-service via huge files.
  - MIME+extension double-check reduces risk of file masquerading.
- **Possible Questions**:
  - What is the maximum allowed file size? (10 MB)
  - Which file types are permitted? (PDF, DOCX, TXT)
  - How is MIME validation performed? (Simple mapping; could be enhanced with `python-magic`)

### `app/utils/nlp.py`
- **Purpose**: spaCy NER pipeline with custom EntityRuler for extracting domain-specific entities.
- **Key Functions**:
  - `get_nlp_with_ruler() → Language` – lazy-initialized singleton
    - Loads `en_core_web_md` (medium English model)
    - Adds custom `EntityRuler` with patterns for:
      - Skills (from `SKILL_KEYWORDS` + dynamic fallback)
      - Education (degree names, institution keywords)
      - Job titles (senior, lead, manager, director, etc.)
      - Certifications (AWS, Cisco, etc.)
      - Other: ORG, DATE, PERSON, MONEY (standard spaCy entities)
  - `_ensure_patterns(nlp: Language)` – adds the above patterns to the ruler if not already present
  - `extract_education_spacy(text) → list[Span]` – returns spans labeled as "EDUCATION" (custom)
  - `extract_job_titles_spacy(text) → list[Span]` – returns spans labeled as "JOB_TITLE" (custom)
- **How it works**:
  - On first call, `spacy.load("en_core_web_md")` is executed (~50 MB model).
  - The `EntityRuler` is added before the standard NER pipe in the pipeline.
  - Patterns are loaded from JSON-like lists; each pattern specifies `label` and `pattern` (token attributes like `LOWER`, `ENT_TYPE`, etc.).
  - When text is processed, the ruler assigns custom labels before standard NER runs; entities can be filtered by label.
  - Extraction functions return the span objects (or their `.text`) for further processing.
- **Important**:
  - Combines spaCy's strong general NER with domain-specific rules for better accuracy.
  - Lazy initialization ensures model is loaded only once per process lifetime.
  - The custom labels (`EDUCATION`, `JOB_TITLE`) make extraction straightforward.
  - Falls back to standard NER entities if custom patterns don't match (e.g., a university name not in patterns still caught as ORG).
- **Possible Questions**:
  - What entities does the custom ruler recognize? (Education, job titles, skills, certifications, plus standard spaCy entities)
  - How is the spaCy pipeline loaded efficiently? (Lazy singleton; model loaded once)
  - How does the EntityRuler work? (Assigns labels based on token patterns before standard NER)
  - What happens if a custom pattern is missing? (Standard NER may still catch the entity as ORG/PERSON/etc.)

### `app/utils/taxonomy.py`
- **Purpose**: Provides access to skill keywords and generic phrases loaded from `data/taxonomy.json`.
- **Key Variables**:
  - `SKILL_KEYWORDS: list[str]` – ~200 canonical skill names (e.g., "Python", "JavaScript", "AWS")
  - `JOB_CATEGORIES: dict` – mapping of job category names to keyword lists (less used)
  - `GENERIC_PHRASES: list[str]` – ~50 buzzwords/phrases (e.g., "results-driven", "team player", "synergy")
  - `_seed_embeddings: np.ndarray | None` – SBERT embeddings of seed phrases for dynamic skill detection
- **Key Functions**:
  - `_init_seed_embeddings()` → computes SBERT embeddings for seed phrases (used in `is_dynamic_skill`)
  - `is_dynamic_skill(noun_phrase: str) → bool` – returns True if the phrase is semantically similar to skill seeds (cosine > 0.82)
- **How it works**:
  - At module import, `data/taxonomy.json` is loaded and parsed.
  - The `SKILL_KEYWORDS` list is used by `skill_overlap.py` for exact matching.
  - The `GENERIC_PHRASES` list is used by `validation.py` for `compute_generic_phrase_score`.
  - Dynamic skill detection works by:
    1. Computing SBERT embedding of the input noun phrase
    2. Comparing it to precomputed seed vectors (averages of categories like "Programming Language", "Cloud Computing", etc.)
    3. If max cosine similarity > 0.82, the phrase is considered a skill
- **Important**:
  - Combines exact taxonomy lookup with semantic fallback for emerging/misspelled skills.
  - Generic phrases are used to detect buzzword-heavy resumes (often indicative of low quality or fabrication).
  - The seed embeddings are computed once and reused.
- **Possible Questions**:
  - Where do the skill keywords and generic phrases come from? (Loaded from `data/taxonomy.json`)
  - How does dynamic skill detection work? (Compare SBERT embedding to seed vectors; >0.82 similarity → skill)
  - What are the seed phrases used for dynamic detection? (Categories like "Programming Language", "Cloud Computing", etc.)
  - How many generic phrases are in the list? (~50)

### `app/utils/aliases.py`
- **Purpose**: Maps abbreviations and shorthand to canonical skill names before skill extraction and embedding.
- **Key Component**: `SKILL_ALIASES: dict[str, str]` – over 200 mappings (e.g., `"js"` → `"JavaScript"`, `"k8s"` → `"Kubernetes"`, `"ml"` → `"Machine Learning"`)
- **Key Functions**:
  - `normalize_skills_text(text: str) → str` – replaces all aliases in text using pre-compiled regex patterns (word-boundary safe)
  - `normalize_skill_token(token: str) → str` – returns canonical name if token is an alias, else original token
- **How it works**:
  - At module import, aliases are sorted by length descending and pre-compiled into regex patterns with `\b` word boundaries.
  - The `normalize_skills_text` function iterates over patterns and applies `pattern.sub(canonical, text)`.
  - Word boundaries prevent false positives (e.g., `"class"` not affected by `"c"` alias).
  - Applied to both resume and job description text before:
    - Skill extraction (`app.features.skill_overlap.extract_skills`)
    - SBERT embedding (`app.models.embedder`)
- **Important**:
  - Improves recall for skill matching by expanding abbreviations.
  - Applied consistently across resume and JD ensures fair comparison.
  - The dictionary is curated to match canonical names in `SKILL_KEYWORDS`.
- **Possible Questions**:
  - How does alias normalization improve semantic similarity? (Expands abbreviations so embeddings see full skill names)
  - What prevents false replacements like changing "class" to "c"? (\b word boundaries ensure whole-word matches)
  - How are aliases ordered for regex substitution? (Longest first to avoid partial matches)
  - Where do the canonical names come from? (Must exist in `SKILL_KEYWORDS` in taxonomy.py)

---

## 📁 `data/` - Data & Model Artifacts

### `data/processed/metrics.json`
- **Purpose**: Stores model performance metrics, feature importance, confusion matrix, and dataset characteristics.
- **Key Contents** (see `00_SYSTEM_METRICS.md` for full details):
  - `test_accuracy`: 0.87375
  - `test_f1_weighted`: 0.8721886308804665
  - `feature_importance`: list of objects with `feature` and `importance` (sorted descending)
  - `classification_report`: per-class precision, recall, f1-score, support
  - `dataset_shape`: [4000, 35]
  - `class_distribution`: Authentic 1930, Suspicious 1296, Potentially Fake 774
  - `best_params`: XGBoost hyperparameters
- **How it works**: Generated by `notebooks/01_eda_and_model.py` after model training and evaluation.
- **Important**: 
  - Used by `app.models.classifier.get_model_info()` and `get_feature_importance()` to report performance.
  - The `feature_importance` list matches the order of features expected by the model.
- **Possible Questions**:
  - Where do these metrics come from? (Model evaluation on hold-out test set)
  - What is the test accuracy? (87.375%)
  - Which feature has the highest importance? (`skill_overlap_score` at 20.23%)
  - How many samples were in the test set? (800)

### `data/processed/*.png`
- **Purpose**: Visual EDA artifacts generated during model development.
- **Files**:
  - `class_distribution.png`: Bar chart of class counts
  - `confusion_matrix.png`: Heatmap of true vs predicted class counts
  - `correlation_matrix.png`: 17x17 Pearson correlation heatmap of features
  - `feature_distributions.png`: 5x4 grid of KDE plots per class (20 subplots)
  - `feature_importance.png`: Horizontal bar chart of feature importances
  - `decision_tree.png`: Visual representation of a shallow Decision Tree (max_depth=4)
- **How it works**: Created using `matplotlib` and `seaborn` in the training notebook.
- **Important**: 
  - Useful for understanding model behavior and feature relationships.
  - Not required for runtime; only for analysis and documentation.
- **Possible Questions**:
  - What does the confusion matrix show? (True vs predicted class counts)
  - Which two features are most strongly correlated? (semantic_similarity and final_match_score)
  - What does the feature importance plot show? (Relative contribution of each feature to model decisions)

### `data/models/xgboost_model.pkl`
- **Purpose**: Serialized XGBoost model (Booster) and feature names list.
- **Contents**:
  - `model`: XGBoost Booster object (trained on 4,000 samples)
  - `feature_names`: list of 17 feature strings in order expected by model
- **How it works**: 
  - Loaded by `app.models.classifier._load_model_from_pkl()` via `joblib.load`.
  - The Booster is used for `predict` and `predict_proba` calls.
  - Feature names ensure input DataFrame columns match training order.
- **Important**:
  - File size ~294 KB (efficient for deployment).
  - If this file is corrupt or missing, the classifier falls back to a heuristic rule-based system.
  - Model was trained with hyperparameters: `learning_rate=0.2`, `max_depth=5`, `n_estimators=50`, `subsample=0.8`.
- **Possible Questions**:
  - What is stored in this pickle file? (XGBoost Booster and feature names)
  - What happens if this file is missing? (Falls back to heuristic classifier)
  - What were the final XGBoost hyperparameters? (See above)
  - How large is the model file? (~294 KB)

### `data/taxonomy.json`
- **Purpose**: Source file for skill keywords and generic phrases.
- **Structure**:
  ```json
  {
    "SKILL_KEYWORDS": ["Python", "Java", "JavaScript", ...],
    "JOB_CATEGORIES": { "...": [...] },
    "GENERIC_PHRASES": ["results-driven", "team player", "synergy", ...]
  }
  ```
- **How it works**: 
  - Loaded at import time by `app.utils.taxonomy`.
  - `SKILL_KEYWORDS` used for exact skill matching.
  - `GENERIC_PHRASES` used for buzzword detection.
- **Important**:
  - Centralizes domain-specific lists; easy to update without code changes.
  - The generic phrase list was curated based on common HR knowledge of low-quality resume indicators.
- **Possible Questions**:
  - Where is the generic phrase list defined? (In this JSON file)
  - How many skill keywords are there? (~200)
  - How many generic phrases are there? (~50)
  - Can this file be updated without retraining the model? (Yes; only affects feature extraction, not model weights)

---

## 📁 `notebooks/` - Development Notebooks

### `notebooks/01_eda_and_model.py`
- **Purpose**: Exploratory data analysis, feature engineering, and model training script.
- **Key Steps**:
  1. Load `resume_dataset_4000_tech.csv` (4,000 synthetic tech resumes)
  2. Perform initial cleaning and label encoding (`Authentic`=0, `Suspicious`=1, `Potentially Fake`=2)
  3. Engineer the 5 additional features:
     - `years_experience` (from `experience_extraction.py`)
     - `num_certifications` (count of certification keywords)
     - `num_skills` (count of skill keywords)
     - `education_level_encoded` (ordinal encoding of highest degree)
     - `has_previous_job` (binary flag for work history)
  4. Split data stratified 80/20 (`random_state=42`)
  5. Train baseline `DecisionTreeClassifier` (`class_weight='balanced'`)
  6. Tune Decision Tree with `GridSearchCV` (5-fold CV, `scoring='f1_weighted'`)
  7. Train final XGBoost model with best params from separate tuning (`learning_rate=0.2`, `max_depth=5`, `n_estimators=50`, `subsample=0.8`)
  8. Evaluate on test set; compute metrics, confusion matrix, feature importance
  9. Save model to `data/models/xgboost_model.pkl`
  10. Save metrics to `data/processed/metrics.json`
  11. Generate EDA plots and save to `data/processed/`
- **How it works**: 
  - Executed sequentially; each cell builds on the previous.
  - The notebook is the source of truth for how the model was trained and evaluated.
- **Important**:
  - Demonstrates proper ML practices: stratified split, class weight balancing, hyperparameter tuning.
  - The final model is the one used in production.
  - All 17 features are validated as predictive via feature importance.
- **Possible Questions**:
  - What hyperparameters were chosen for the final XGBoost model? (`learning_rate=0.2`, `max_depth=5`, `n_estimators=50`, `subsample=0.8`)
  - How was the dataset split? (80% train, 20% test, stratified by class)
  - What was the baseline Decision Tree performance? (~73% accuracy, ~72% weighted F1)
  - Why was `class_weight='balanced'` used? (To address class imbalance; gives minority class more influence)
  - What is the purpose of the engineered features? (To capture candidate profile information not in original 12 features)

---

## 📁 Other Notable Files

### `app/__init__.py`, `app/features/__init__.py`, `app/models/__init__.py`, `app/utils/__init__.py`
- **Purpose**: Mark directories as Python packages; enable imports like `from app.features import validation`.
- **Contents**: Typically empty (just enough for Python to recognize the package).

### `resume_dataset_4000_tech.csv` (referenced, not present in repo)
- **Purpose**: Original synthetic dataset used for training (4,000 resumes, 35 columns).
- **Note**: Not included in the repository to save space; the processed `combined_dataset.csv` in `data/processed/` contains the engineered features.
- **Important**: The model was trained on this dataset; its characteristics are reflected in the metrics.

### `data/processed/combined_dataset.csv`
- **Purpose**: Contains the 4,000 samples with all 17 engineered features plus original columns and label.
- **How it works**: Output of the feature engineering step in `notebooks/01_eda_and_model.py`.
- **Important**: Used for quick retraining or analysis without re-engineering features.

### `original_nlp.py`
- **Purpose**: Early prototype of NLP processing (superseded by current `app.utils.nlp` and related files).
- **Note**: Not used in current system; kept for historical reference.

### `scratch/` directory
- **Purpose**: Temporary workspace for experimentation; not part of the deployed system.

### `dev/` directory
- **Purpose**: Development tools or scripts; not part of the deployed system.

### `logs/` directory
- **Purpose**: Stores log files if logging to file is enabled (via `LOG_FILE` env var).
- **Note**: Empty by default; logs go to stdout unless configured otherwise.

### `tests/` directory
- **Purpose**: Unit and integration tests (not fully implemented in this academic project).
- **Note**: Placeholder for future test suite.

### `Pdf and MD/` directory
- **Purpose**: Contains PDFs and Markdown documents used for reference, presentations, and reports.
- **Note**: Includes items like `02_Senior_Backend_Engineer_StrongFit.pdf` (sample resume), `LATEST_FEATURES.md`, etc.
- **Important**: These are reference materials; not part of the running system.

---

## 🔐 Security & Privacy Considerations (Cross-Cutting)

- **Authentication**: Passwords stored as SHA-256 hashes (not ideal for production; consider bcrypt/argon2).
- **Session Management**: Secure cookies (`SameSite=None`, `Secure=True`) required for HF Spaces.
- **Input Validation**: File type/size/MIME validation prevents malicious uploads.
- **Rate Limiting**: Protects against brute-force and denial-of-service.
- **Data Isolation**: Row-level security via `username` filtering ensures HR users only see their own data.
- **PII Handling**: Analysis results store minimal PII (only filename and username linkage; resume text not persisted).
- **Environment Secrets**: Sensitive values (`SESSION_SECRET`, database credentials, API keys) loaded from environment, not hardcoded.
- **Model Security**: Pickle file loaded only from trusted source; fallback prevents execution of arbitrary code.

### Possible Security Questions:
  - How are passwords stored? (SHA-256 hashes; note: for production, use bcrypt)
  - How is data isolation achieved? (Each query filters by `username = current_user()`)
  - What protections exist against file upload attacks? (MIME/type/size validation, extension whitelist)
  - How does the system prevent prompt injection in LLM calls? (Sanitization removes dangerous phrases and truncates input)
  - Are dependencies checked for known vulnerabilities? (Not explicitly in this project; would use `pip-audit` in production)

---

## 🚀 Performance & Scalability (Cross-Cutting)

- **Latency**:
  - Best case (GPU + cached JD): <500 ms
  - Typical case (CPU + uncached): 1-2 seconds
  - Worst case (OCR + no GPU): 3-5 seconds
  - LLM verification adds 1-3 seconds when used
- **Throughput**:
  - Single predictions: ~20-30/min/core (SBERT-bound)
  - Batch processing: ~50-100 resumes/sec (DB-write-bound)
- **Scaling Strategies**:
  - Stateless API endpoints (except in-memory batch jobs)
  - Database connection pooling (SQLAlchemy + Supabase)
  - Caching: LRU for SBERT embeddings (128), model singleton
  - Async processing: ThreadPoolExecutor for CPU-bound work, async DB
  - Rate limiting prevents overload
- **Resource Usage**:
  - Memory: ~360 MB base + overhead per worker
    - SBERT Model: ~150 MB
    - spaCy Model: ~50 MB
    - XGBoost Model: ~10 MB
    - Python/FastAPI: ~50 MB
    - Buffers/Overhead: ~100 MB
  - CPU: SBERT inference is primary bottleneck (parallelized via thread pool)
  - Storage: Model files ~200 MB total; database grows with usage

### Possible Performance Questions:
  - What is the typical end-to-end latency for a resume analysis? (1-2 seconds)
  - How does GPU acceleration improve performance? (Reduces SBERT latency from seconds to sub-second)
  - What is the purpose of the LRU cache for embeddings? (Avoids recomputing embeddings for identical job descriptions)
  - How are database connections managed? (SQLAlchemy async connection pooling)
  - What happens under high load? (Rate limiting kicks in; latency increases; HF Spaces auto-scales replicas)

---

✅ **End of File Details Reference**

Use this document to:
- Refresh your memory on any file's purpose or implementation
- Prepare for deep-dive questions about specific components
- Understand how each piece fits into the overall system
- Recall important design decisions, bug fixes, and tradeoffs
---
title: ClearHire - AI Resume Screener
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# ClearHire — SBERT-Based Resume Screening & Authenticity Validation Using XGBoost Classification

> **Complete End-to-End Project — Ready for Final Defense Panel Presentation**
> Built with FastAPI + Sentence-BERT + XGBoost + spaCy + PostgreSQL + 6-Page Web UI
>
> 🌐 **Live Demo:** [https://resume.sarshijkarn.com.np](https://resume.sarshijkarn.com.np)
> 🚀 **Quick Start (Windows):** Double-click `run.bat` in the project folder to start the application.
> 🔐 **Default Login:** `admin` / `hr2026` (HR role) | `applicant` / `apply2026` (Applicant role)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Research & Development Approach](#3-research--development-approach)
4. [Dataset Collection & Preparation](#4-dataset-collection--preparation)
5. [Resume & Job Description Processing](#5-resume--job-description-processing)
6. [Resume Screening Method — SBERT Semantic Pipeline](#6-resume-screening-method--sbert-semantic-pipeline)
7. [Hybrid Candidate Scoring](#7-hybrid-candidate-scoring)
8. [Resume Validation Method — 17 Validation Features](#8-resume-validation-method--17-validation-features)
9. [Model Training & Evaluation](#9-model-training--evaluation)
10. [System Architecture](#10-system-architecture)
11. [Backend, Database & Authentication](#11-backend-database--authentication)
12. [Frontend — 6-Page Web UI](#12-frontend--6-page-web-ui)
13. [API Endpoints Reference](#13-api-endpoints-reference)
14. [NLP Layer — spaCy Integration](#14-nlp-layer--spacy-integration)
15. [LLM Verification Layer](#15-llm-verification-layer)
16. [SHAP Explainability](#16-shap-explainability)
17. [Document Format Support & OCR](#17-document-format-support--ocr)
18. [System Integration & Testing](#18-system-integration--testing)
19. [Experimental Setup](#19-experimental-setup)
20. [Project File Structure](#20-project-file-structure)
21. [Installation & Setup](#21-installation--setup)
22. [Environment Variables](#22-environment-variables)
23. [How to Run](#23-how-to-run)
24. [How to Use — Step by Step](#24-how-to-use--step-by-step)
25. [Classification & Color Psychology](#25-classification--color-psychology)
26. [Rate Limiting & Security](#26-rate-limiting--security)
27. [Edge Case Handling](#27-edge-case-handling)
28. [Cloud Deployment](#28-cloud-deployment)
29. [Bug Fixes & Changelog](#29-bug-fixes--changelog)
30. [Future Improvements](#30-future-improvements)
31. [Credits](#31-credits)

---

## 1. Project Overview

**ClearHire** is a production-grade, cloud-deployed **automated resume screening and authenticity
validation system** built as a Minor NCE (National College of Engineering) project. It combines
**Sentence-BERT (SBERT)** semantic embeddings with a trained **XGBoost Classifier** to screen
resumes across three authenticity dimensions: genuine, suspicious, or fabricated. The system is
further augmented by **spaCy NER**, **SHAP explainability**, **OCR fallback**, and an optional
**LLM (Groq Llama-3.3-70B) double-check layer**.

| Class                   | Meaning                                                    | Color           |
|-------------------------|------------------------------------------------------------|-----------------|
| ✅ Authentic            | Genuine resume with real skills & experience               | Green `#059669` |
| ⚠ Suspicious            | May contain exaggerations or inconsistencies               | Amber `#d97706` |
| ✗ Potentially Fake      | Fabricated or heavily keyword-stuffed                      | Red   `#dc2626` |
| 🤖 Not a Resume         | Uploaded document is not a resume (research paper, etc.)   | Gray  `#6b7280` |

### Key Capabilities

- **Single resume screening** — Upload PDF/TXT/DOCX + job description → instant analysis with
  semantic score, skill gap doughnut chart, SHAP explainability, and authenticity verdict
- **Async batch screening** — Upload multiple resumes → background processing with real-time
  progress polling; results ranked Authentic → Suspicious → Fake by match score
- **SBERT semantic similarity** — 384-dimensional SBERT cosine similarity between resume and JD
- **17-feature validation pipeline** — Keyword stuffing, generic phrases, skill density,
  promotion speed, gap years, overlapping jobs, education encoding, and 10 more signals
- **XGBoost classifier** — Trained on 4,000 labeled tech resumes: **87.375% test accuracy,
  87.22% weighted F1-score**
- **SHAP explainability** — Top-3 contributing features with directional contribution bars
  shown on every prediction — making AI decisions transparent and auditable
- **spaCy NER** — Education/job-title/skill entity extraction via `en_core_web_md` + custom EntityRuler
- **OCR fallback** — Scanned/image PDFs automatically processed via pytesseract + pdf2image
- **LLM double-check** — Groq Llama-3.3-70B optionally re-evaluates Suspicious/Fake verdicts
- **Multi-tenant auth** — HR and Applicant roles with row-level PostgreSQL data isolation
- **Analytics dashboard** — Model metrics, feature importance, confusion matrix, EDA visualizations
- **Export** — Per-user batch CSV, analytics metrics CSV, JSON history export

### Tech Stack Summary

| Layer          | Technology |
|----------------|-----------|
| Backend        | Python 3.10+ · FastAPI · Uvicorn (ASGI) |
| ML / NLP       | SBERT `all-MiniLM-L6-v2` (384-dim) · XGBoost · spaCy `en_core_web_md` · SHAP |
| Database       | PostgreSQL (Supabase cloud) · SQLAlchemy async ORM · asyncpg driver |
| Document Parse | pdfplumber (layout-aware) · mammoth (DOCX) · pytesseract · pdf2image (OCR) |
| Frontend       | Jinja2 templates · Vanilla CSS · JavaScript · Chart.js 4.4 |
| Auth           | Starlette SessionMiddleware · SHA-256 hashed passwords · signed session cookies |
| Rate Limiting  | slowapi (25 req/min single · 100 req/min batch · 10 req/min applicant submit) |
| LLM Layer      | Groq API — Llama-3.3-70B-versatile (optional, graceful fallback) |
| Deployment     | Docker · Hugging Face Spaces (Docker SDK) · Cloudflare custom domain · Supabase DB |

---

## 2. Problem Statement

### The Challenge

HR departments receive hundreds of resumes per job posting. Manually reviewing each for:

- **Skill match** — Does the candidate actually have the required technical skills?
- **Authenticity** — Is the resume genuine or does it contain fabricated/exaggerated claims?
- **Generic content** — Is it filled with buzzwords ("results-driven", "team player") vs. real
  quantifiable achievements?
- **Document validity** — Is this even a resume and not a research paper, textbook chapter, or
  blank PDF?

...is time-consuming, error-prone, subjective, and fundamentally does not scale. A hiring manager
screening 200 resumes at 5 minutes each spends 1,000 minutes (~17 hours) per job posting.

### Impact of the Problem

- Resume fraud affects an estimated **53% of job applications** (HireRight Employment Screening
  Benchmark Report, 2022)
- **78% of HR professionals** report receiving resumes with at least one materially false claim
- Manual screening leads to unconscious bias and inconsistent evaluation criteria across candidates
- The average cost of a bad hire is estimated at **30% of the employee's first-year salary**

### Our Solution

An automated SBERT + XGBoost pipeline that:

1. Extracts text from any resume format (PDF, DOCX, TXT — including scanned/image PDFs via OCR)
2. Validates the document is actually a resume using a multi-signal scoring system before
   wasting compute on classification
3. Computes SBERT-based semantic similarity between resume content and the job description
4. Extracts 17 carefully engineered validation features covering authenticity, consistency,
   and content quality signals
5. Classifies the resume via a trained XGBoost model achieving **87.375% accuracy**
6. Returns fully explainable results: matched/missing skills, SHAP feature contributions,
   per-class confidence probabilities, and an optional LLM second opinion
7. Persists all results to PostgreSQL for HR audit trail, history review, and CSV export
8. Provides an analytics dashboard with model metrics and dataset-level EDA visualizations

---

## 3. Research & Development Approach

### Overview of Development Phases

The project was structured across **7 development phases**, progressing from raw data collection
through cloud deployment and final testing:

| Phase   | Name                         | Key Output |
|---------|------------------------------|-----------|
| Phase 1 | Data Collection & EDA        | 4,000-row dataset · correlation matrix · KDE distributions |
| Phase 2 | Model Training & Evaluation  | XGBoost (87.375% acc) · confusion matrix · feature importance |
| Phase 3 | SBERT Semantic Pipeline      | Cosine similarity · skill extraction · short-JD blending |
| Phase 4 | 17-Feature Validation Engine | All 17 authenticity signals extracted from raw resume text |
| Phase 5 | System Integration           | FastAPI server · PostgreSQL · Jinja2 UI · auth · rate limiting |
| Phase 6 | Testing & Bug Fixes          | 17 bugs identified and resolved · 152+ unit/integration test methods |
| Phase 7 | Cloud Deployment             | Docker image · Hugging Face Spaces · Cloudflare · Supabase |

### Research Questions Addressed

1. Can SBERT sentence embeddings reliably measure resume-to-job-description semantic alignment?
2. Which combination of textual features best distinguishes authentic from fabricated resumes?
3. Can an XGBoost classifier trained on engineered feature signals generalize to unseen resumes?
4. How can SHAP explainability make ML-driven hiring decisions transparent and auditable?
5. Does an LLM second-opinion layer improve detection of borderline Suspicious cases?

### Technology Choices & Justification

| Choice | Alternatives Considered | Why Chosen |
|--------|------------------------|-----------|
| SBERT `all-MiniLM-L6-v2` | BERT-base, RoBERTa, TF-IDF cosine | Fast (384-dim), multilingual, pre-trained on 1B+ sentence pairs |
| XGBoost | Decision Tree, Random Forest, SVM | Best accuracy (87.375%), native SHAP via pred_contribs |
| FastAPI | Flask, Django REST | Async-native, auto OpenAPI docs, Starlette session middleware |
| PostgreSQL | SQLite, MongoDB | Production-grade, ACID, multi-tenant row isolation |
| SHAP (native pred_contribs) | LIME, manual explanations | No separate SHAP library calls; uses XGBoost built-in method |
| Groq Llama-3.3-70B | OpenAI GPT-4, Anthropic Claude | Free tier, fast inference, strong instruction-following |
| pdfplumber | PyMuPDF, PyPDF2 | Layout-aware column parsing; best for formatted resumes |
| mammoth | python-docx | Cleaner text extraction from complex DOCX layouts |
---

## 4. Dataset Collection & Preparation

### Source and Motivation

The dataset used is **`resume_dataset_4000_tech.csv`** — a synthetic tech-industry resume dataset
of **4,000 labeled records** specifically designed to capture the distribution of authentic,
suspicious, and potentially fake resumes. Using a synthetic dataset allows for controlled class
balance, avoids privacy concerns with real applicant data, and provides ground-truth labels
that would be impossible to obtain from real HR decisions at scale.

### Dataset Summary

| Attribute              | Value |
|------------------------|-------|
| Total records          | 4,000 |
| Total columns          | 35 (raw) → 35+ after feature engineering |
| File encoding          | `latin-1` (not UTF-8 — important for loading) |
| Filename               | `resume_dataset_4000_tech.csv` |
| Domain                 | Technology / IT sector |
| Label type             | 3-class classification |

### Class Distribution

| Class            | Count | Percentage | Risk Label |
|------------------|-------|-----------|-----------|
| Authentic        | 1,930 | 48.25%    | Low       |
| Suspicious       | 1,296 | 32.40%    | Medium    |
| Potentially Fake |   774 | 19.35%    | High      |
| **Total**        | **4,000** | **100%** | — |

**Observation:** The dataset is moderately imbalanced — Authentic is the majority class (48.25%)
and Potentially Fake is the minority class (19.35%). This is handled in training using
`class_weight='balanced'` for the Decision Tree baseline, and stratified train/test splitting
(`stratify=y`) for all models to ensure class ratios are preserved across both sets.

### Raw Dataset Columns (Key Fields)

| Column | Type | Description |
|--------|------|-------------|
| `classification` | str | Target label: Authentic / Suspicious / Potentially Fake |
| `risk_level` | str | Risk tier: Low / Medium / High |
| `semantic_similarity` | float | Pre-computed SBERT cosine similarity [0, 1] |
| `skill_overlap_score` | float | Pre-computed Jaccard skill similarity [0, 1] |
| `experience_relevance_score` | float | Pre-computed experience relevance [0, 1] |
| `final_match_score` | float | Weighted composite score [0, 1] |
| `overlapping_jobs` | int | Count of date-range overlaps |
| `promotion_speed` | float | Title promotions per year |
| `experience_graduation_gap` | float | Years since graduation minus claimed experience |
| `skill_density` | float | Skills per year of experience |
| `achievement_count` | int | Number of quantifiable achievements |
| `generic_phrase_score` | float | Proportion of buzzword phrases |
| `gap_years` | float | Total unexplained job gap years |
| `keyword_stuffing_score` | float | JD-keyword frequency in resume |
| `years_experience` | float | Total professional experience (years) |
| `certifications` | str | Comma-separated certification names |
| `skills` | str | Comma-separated skill names |
| `education_level` | str | "Bachelor's" / "Master's" / "PhD" |
| `previous_job_title` | str | Previous position title (nullable) |

### Feature Engineering Applied

Before model training, 4 additional feature columns were engineered from raw columns:

```python
# Count number of certifications from comma-separated string
df['num_certifications'] = df['certifications'].apply(
    lambda v: len([c for c in str(v).split(',') if c.strip()]) if pd.notna(v) else 0
)

# Count number of skills from comma-separated string
df['num_skills'] = df['skills'].apply(
    lambda v: len([s for s in str(v).split(',') if s.strip()]) if pd.notna(v) else 0
)

# Encode education level as ordinal integer
edu_map = {"Bachelor's": 1, "Master's": 2, "PhD": 3}
df['education_level_encoded'] = df['education_level'].map(edu_map).fillna(0).astype(int)

# Binary flag for having a previous job
df['has_previous_job'] = df['previous_job_title'].notna().astype(int)
```

This brings the total ML feature count to **17 features** (12 original + 5 engineered).

### Train/Test Split

```python
from sklearn.model_selection import train_test_split

X = df[feature_cols].values   # shape (4000, 17)
y = df['target'].values        # 0=Authentic, 1=Suspicious, 2=Potentially Fake

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,       # 20% test = 800 samples
    random_state=42,     # reproducibility seed
    stratify=y           # preserve class distribution in both splits
)
# Result: X_train (3200, 17) | X_test (800, 17)
```

| Split     | Size  | Authentic | Suspicious | Potentially Fake |
|-----------|-------|-----------|-----------|-----------------|
| Training  | 3,200 | 1,544     | 1,037     | 619             |
| Testing   |   800 |   386     |   259     | 155             |

### Missing Values

All 17 feature columns are complete across all 4,000 records. A fallback
`df[col].fillna(df[col].median())` is applied in the training script as a defensive measure.

### Data Preprocessing

1. **Encoding:** Loaded with `encoding='latin-1'` to handle special characters in resume text
2. **Label encoding:** `{'Authentic': 0, 'Suspicious': 1, 'Potentially Fake': 2}`
3. **Missing value imputation:** Median fill (no actual missing values found)
4. **Stratified splitting:** Ensures minority class (Potentially Fake) is represented in test set
5. **No normalization needed:** XGBoost is scale-invariant; Decision Tree is rank-based

### EDA Artifacts Generated

| File | Description |
|------|-------------|
| `class_distribution.png` | Bar chart of class and risk-level counts |
| `correlation_matrix.png` | 17x17 Pearson correlation heatmap |
| `feature_distributions.png` | 5x4 grid of KDE plots per class (20 subplots) |
| `confusion_matrix.png` | True vs. Predicted class heatmap |
| `feature_importance.png` | Horizontal bar chart of feature importances |
| `decision_tree.png` | Visual tree diagram (max_depth=4 for readability) |

### Key EDA Insights

- **`generic_phrase_score`** shows the clearest separation between Authentic (low) and
  Potentially Fake (high) across KDE plots
- **`skill_overlap_score`** is the single highest-importance feature at 20.23% in the final model
- **`final_match_score`** ranks second at 17.10% — confirming the composite score captures
  important signal from both semantic and skill dimensions
- **High correlation:** `semantic_similarity` and `final_match_score` are positively correlated
  (expected, since `final_match_score = 0.6 * semantic + 0.25 * skill + 0.15 * exp`)
- **Potentially Fake resumes** have distinctively high `keyword_stuffing_score` and
  `generic_phrase_score` — explaining the class's high F1 of 0.9608

---

## 5. Resume & Job Description Processing

### Document Ingestion Pipeline

All document parsing is implemented in `app/utils/parser.py`. The pipeline supports three file
formats natively, with OCR as a fallback for scanned PDFs:

```
Uploaded File
     |
     v
validate_upload()  <- MIME type check + file size limit
     |
     v
parse_resume(file_bytes, filename)
     |
     +-- .pdf  -> parse_pdf()   -- pdfplumber (layout-aware)
     |                          +---> if < 50 chars: OCR fallback (pytesseract)
     |
     +-- .docx -> parse_docx()  -- mammoth.extract_raw_text()
     |           / .doc         +---> fallback: python-docx paragraph join
     |
     +-- .txt  -> parse_txt()   -- UTF-8 -> latin-1 -> cp1252 -> latin-1/replace
     |
     v
langdetect.detect()  <- language identification
     |
     v
is_resume_format()   <- multi-signal scoring: reject non-resumes before classification
```

### PDF Parsing — pdfplumber

```python
import pdfplumber

with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
    for page in pdf.pages:
        page_text = page.extract_text(layout=True)  # layout=True preserves columns
        if page_text:
            text += page_text + "\n"
```

**Why pdfplumber?** Unlike PyPDF2/PyMuPDF, pdfplumber uses `layout=True` mode that correctly
handles multi-column resume layouts without merging text from different columns into garbled lines.

### OCR Fallback — pytesseract

Triggered when pdfplumber extracts fewer than 50 characters (scanned/image PDF):

```python
from pdf2image import convert_from_bytes
import pytesseract

# OPTIMIZATION: Only OCR the first 2 pages.
# Real resumes are 1-2 pages. Scanning a 50-page document would cause timeout.
images = convert_from_bytes(file_bytes, first_page=1, last_page=2)
for img in images:
    ocr_text += pytesseract.image_to_string(img) + "\n"
```

### DOCX Parsing — mammoth

```python
import mammoth

result = mammoth.extract_raw_text(io.BytesIO(file_bytes))
text = result.value
# Fallback to python-docx if mammoth fails
```

### TXT Parsing — Encoding Detection

```python
for enc in ['utf-8', 'latin-1', 'cp1252']:
    try:
        return file_bytes.decode(enc).strip()
    except (UnicodeDecodeError, ValueError):
        continue
# Final fallback
return file_bytes.decode('latin-1', errors='replace').strip()
```

### Resume Format Validation — is_resume_format()

Before feeding any document into the classification pipeline, a multi-signal scoring system
determines whether the document is actually a resume:

| Signal | Condition | Points |
|--------|-----------|--------|
| Email address | `[\w\.-]+@[\w\.-]+\.\w+` found | +25 |
| Phone number | Various formats matched | +20 |
| LinkedIn/GitHub URL | `linkedin.com/in/` or `github.com/` found | +15 |
| Education keywords | `education`, `university`, `bachelor`, etc. | +10 |
| Experience keywords | `experience`, `employment`, `work history` | +10 |
| Skills keywords | `skills`, `technologies`, `certifications` | +10 |
| High NER density | spaCy finds > 5 ORG/DATE/PERSON entities | +20 |
| Academic negatives | `abstract`, `bibliography`, `table of contents` | -30 each |
| Wall-of-text penalty | Average > 25 words per line | -25 |

**Threshold:** Score >= 45 → proceed to classification. Score < 45 → return `"Not a Resume"`.

### NLP Preprocessing — Feature Extraction from Text

| Extraction | Module | Method |
|-----------|--------|--------|
| Skill keywords | `app/utils/taxonomy.py` | Taxonomy lookup + SBERT embedding fallback |
| Skill alias normalization | `app/utils/aliases.py` | "js" -> "JavaScript", "ml" -> "Machine Learning" |
| Years of experience | `app/features/experience_extraction.py` | Date-range regex parsing |
| Graduation year | `app/features/experience_extraction.py` | Education section regex |
| Job titles | `app/utils/nlp.py` | spaCy EntityRuler + regex fallback |
| Education level | `app/utils/nlp.py` | Keyword matching + entity extraction |
| Certifications | `app/features/validation.py` | 26 regex patterns |
| Achievements | `app/features/validation.py` | Regex: % increase, $amounts, action verbs |
| Generic phrases | `data/taxonomy.json` | Exact phrase matching against 50+ buzzwords |

---

## 6. Resume Screening Method — SBERT Semantic Pipeline

### What is SBERT?

**Sentence-BERT (SBERT)** is a modification of the BERT architecture that uses siamese and
triplet network structures to derive semantically meaningful sentence embeddings. Unlike
word-level embeddings (Word2Vec, GloVe), SBERT produces **fixed-size sentence-level vectors**
that capture the overall meaning of a full sentence or paragraph.

The model used is **`all-MiniLM-L6-v2`** — a distilled, lightweight variant specifically
optimized for semantic similarity tasks.

### Model Specifications

| Property | Value |
|----------|-------|
| Model ID | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding dimension | 384 |
| Architecture | 6-layer MiniLM (distilled from BERT-base) |
| Training data | 1+ billion sentence pairs |
| Max sequence length | 256 tokens |
| Size on disk | ~80 MB |
| Inference speed (CPU) | ~2-5 seconds per resume |
| Multilingual | Yes (handles multiple languages natively) |

### Why all-MiniLM-L6-v2?

| Factor | all-MiniLM-L6-v2 | BERT-base | TF-IDF |
|--------|-----------------|-----------|--------|
| Embedding dim | 384 | 768 | Vocabulary-sized sparse |
| Semantic understanding | High | High | Lexical only |
| Inference speed | Fast | Slow | Very fast |
| Multilingual | Yes | Limited | No |
| Pre-training data | 1B+ pairs | Wikipedia + BooksCorpus | N/A |
| Resume-JD alignment quality | Excellent | Excellent | Poor for synonyms |

**Key advantage over TF-IDF:** SBERT understands synonyms and paraphrases. A resume listing
"supervised machine learning" matches a JD requiring "predictive modeling" via semantic
similarity, whereas TF-IDF would score these as having zero overlap.

### Embedding Implementation

The embedder is implemented as a singleton (`app/models/embedder.py`):

```python
from sentence_transformers import SentenceTransformer

_model = None  # Global singleton

def get_sbert_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_sbert_model()
    # Normalize embeddings for cosine similarity via dot product
    return model.encode(texts, normalize_embeddings=True)

def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    # For normalized embeddings: cosine_sim = dot product
    return float(np.clip(np.dot(emb1, emb2), 0.0, 1.0))
```

The model is **pre-warmed during server startup** (FastAPI lifespan) so the first HTTP
request does not pay the 2-5 second model loading penalty.

### Alias Normalization — Pre-Processing Before Embedding

Before embedding, both resume and JD texts are normalized via `app/utils/aliases.py`:

```python
# Examples of alias normalization
"js"  -> "JavaScript"
"ml"  -> "Machine Learning"
"k8s" -> "Kubernetes"
"py"  -> "Python"
"ai"  -> "Artificial Intelligence"
```

### Semantic Similarity Computation

```python
# async version used in production (app/features/semantic.py)
async def compute_semantic_similarity_async(resume_text, job_description):
    norm_resume = normalize_skills_text(resume_text)
    norm_jd = normalize_skills_text(job_description)

    # Embed both in parallel using asyncio
    resume_emb, jd_emb = await asyncio.gather(
        embed_text_async(norm_resume),
        embed_text_async(norm_jd)
    )
    sbert_sim = cosine_similarity(resume_emb, jd_emb)  # range [0, 1]

    # Short JD blending fix: for JDs < 15 words, SBERT embedding quality is
    # poor. Blend with token-level keyword overlap for better accuracy.
    jd_word_count = len(norm_jd.split())
    if jd_word_count >= 15:
        return round(sbert_sim, 4)

    # Weighted blend for short JDs
    token_sim = _token_overlap_score(norm_resume, norm_jd)
    sbert_weight = min(0.85, 0.3 + jd_word_count * 0.04)
    blended = sbert_weight * sbert_sim + (1.0 - sbert_weight) * token_sim
    return round(min(1.0, blended), 4)
```

### Skill Extraction and Overlap Scoring

```python
# Jaccard similarity for skill overlap
def compute_skill_overlap(resume_text, job_description):
    resume_skills = extract_skills(resume_text)  # set
    jd_skills = extract_skills(job_description)  # set

    intersection = resume_skills & jd_skills
    union = resume_skills | jd_skills

    jaccard = len(intersection) / len(union) if union else 0.0

    return {
        'score': round(jaccard, 4),
        'matched': sorted(intersection),
        'missing': sorted(jd_skills - resume_skills),
        'extra': sorted(resume_skills - jd_skills)
    }
```

---

## 7. Hybrid Candidate Scoring

### The Final Match Score Formula

All three scoring dimensions are combined into a single **`final_match_score`**:

```
final_match_score = 0.60 x semantic_similarity
                  + 0.25 x skill_overlap_score
                  + 0.15 x experience_relevance_score
```

### Weight Justification

| Component | Weight | Rationale |
|-----------|--------|----------|
| `semantic_similarity` (SBERT) | **60%** | Captures holistic resume-JD alignment including vocabulary, context, and implied expertise. Dominant because it understands meaning, not just keywords. |
| `skill_overlap_score` (Jaccard) | **25%** | Direct skills match is the most common HR screening criterion. Jaccard is unbiased and interpretable. |
| `experience_relevance_score` | **15%** | Confirms industry and role-type alignment. Lower weight because it is noisier (regex-based keyword matching vs. embeddings). |

### Score Interpretation

| Range | Interpretation | UI Color |
|-------|---------------|---------|
| 0.70 – 1.00 | Strong Match — candidate is well-suited for the role | Green |
| 0.35 – 0.69 | Moderate Match — partial fit, worthy of review | Amber |
| 0.00 – 0.34 | Weak Match — significant skill or semantic gap | Red |

The **composite `final_match_score` is the second most important feature at 17.10% importance**
in the trained XGBoost model — it integrates signal from all three dimensions into one
high-information feature.
---

## 8. Resume Validation Method — 17 Validation Features

The heart of the authenticity detection system is a set of **17 carefully engineered validation
features** extracted directly from raw resume text and the job description. These features are
designed to capture signals that distinguish genuine resumes from fabricated or exaggerated ones.

All 17 features are computed in `app/features/validation.py` (386 lines) and assembled by
`compute_all_validation_features()` into a single dictionary fed to the XGBoost classifier.

### Feature Reference Table

| # | Feature | Type | Range | What It Detects |
|---|---------|------|-------|----------------|
| 1 | `semantic_similarity` | float | [0, 1] | SBERT cosine similarity between resume and JD |
| 2 | `skill_overlap_score` | float | [0, 1] | Jaccard similarity of resume vs. JD skills |
| 3 | `experience_relevance_score` | float | [0, 1] | How relevant the resume experience is to the target role |
| 4 | `final_match_score` | float | [0, 1] | Composite: 60% sem + 25% skill + 15% exp |
| 5 | `overlapping_jobs` | int | [0, N] | Count of simultaneous employment date-range conflicts |
| 6 | `promotion_speed` | float | [0, N] | Promotion/title changes per year of experience |
| 7 | `experience_graduation_gap` | float | any | Gap between (now - graduation) and claimed years experience |
| 8 | `skill_density` | float | [0, N] | Skills per year of experience (high = possible stuffing) |
| 9 | `achievement_count` | int | [0, 50] | Count of quantifiable achievements (%, $, action verbs) |
| 10 | `generic_phrase_score` | float | [0, 1] | Proportion of generic buzzword phrases in resume text |
| 11 | `gap_years` | float | [0, N] | Total unexplained gap years between consecutive jobs |
| 12 | `keyword_stuffing_score` | float | [0, 1] | Unusual JD-keyword frequency in resume (stopword-filtered) |
| 13 | `years_experience` | float | [0, 50] | Total professional experience extracted from date ranges |
| 14 | `num_certifications` | int | [0, 30] | Number of distinct certifications detected |
| 15 | `num_skills` | int | [0, N] | Count of distinct skills identified in resume |
| 16 | `education_level_encoded` | int | [0, 3] | Encoded: 0=Diploma, 1=Bachelor, 2=Master, 3=PhD |
| 17 | `has_previous_job` | int | [0, 1] | Binary: whether a previous job title is present |

### Detailed Feature Descriptions

#### Feature 1: `semantic_similarity`
SBERT (`all-MiniLM-L6-v2`) cosine similarity between resume embedding and JD embedding.
Normalized to [0, 1]. Measures holistic semantic alignment.

#### Feature 2: `skill_overlap_score` — Top Feature (20.23% importance)
Jaccard similarity between the set of skills found in the resume and the set of skills
found in the job description. Formula: `|A ∩ B| / |A ∪ B|`.

#### Feature 3: `experience_relevance_score`
Scores how relevant the resume's work history is to the target job category. Uses keyword
overlap between JD tokens and resume job-title tokens, with a baseline scaling factor
to prevent legitimate candidates from receiving 0% due to synonymous terminology.

#### Feature 4: `final_match_score` — Second Feature (17.10% importance)
```
final_match_score = 0.60 x semantic_similarity
                  + 0.25 x skill_overlap_score
                  + 0.15 x experience_relevance_score
```

#### Feature 5: `overlapping_jobs`
Detects simultaneous employment at multiple full-time positions — a common red flag in
fabricated resumes. Implemented by parsing all date ranges in the resume text and checking
each pair for date overlap:

```python
def detect_overlapping_jobs(text: str) -> int:
    ranges = extract_date_ranges(text)  # list of (start_year, end_year) tuples
    overlaps = 0
    for i in range(len(ranges)):
        for j in range(i + 1, len(ranges)):
            s1, e1 = ranges[i]
            s2, e2 = ranges[j]
            if s1 < e2 and s2 < e1:  # actual date overlap
                overlaps += 1
    return overlaps
```

#### Feature 6: `promotion_speed`
Measures how many title promotions appear relative to the candidate's total years of experience.
Excessive promotions in a short time frame is a fabrication signal.

#### Feature 7: `experience_graduation_gap`
Computes the difference between how many years have passed since graduation and how many
years of experience the candidate claims:

```python
gap = (current_year - graduation_year) - years_experience
```

A large positive gap (graduated in 2015 but claims 12 years experience in 2024) is a
chronological inconsistency signal.

#### Feature 8: `skill_density`
Skills per year of experience. High density may indicate keyword stuffing — listing 50 skills
in a 1-year experience profile is unrealistic.

#### Feature 9: `achievement_count`
Counts concrete, quantifiable achievements using regex patterns for numbers, percentages,
monetary values, and strong action verbs:

```python
patterns = [
    r'\b\d+%\b',             # "increased by 50%"
    r'\b\d+x\b',             # "improved 3x"
    r'\$\s*\d+[kKmMbB]?\b',  # "$500K", "$1.5M"
    r'increased\b', r'reduced\b', r'improved\b', r'generated\b',
    r'led\b', r'managed\b', r'created\b', r'developed\b',
]
achievement_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in patterns)
return min(achievement_count, 50)  # capped to prevent extreme values
```

High achievement_count = genuine resume. Fake resumes often lack specific numbers.

#### Feature 10: `generic_phrase_score` — Third Feature (15.24% importance)
Measures the density of buzzword/filler phrases. Phrases detected include: `results-driven`,
`team player`, `think outside the box`, `synergy`, `leverage`, `dynamic professional`,
`proven track record`, `innovative`, and 40+ others stored in `data/taxonomy.json`.

Fake resumes are characteristically heavy in buzzwords and light in specifics.

#### Feature 11: `gap_years`
Detects unexplained employment gaps by finding all years mentioned in the resume and
measuring intervals between consecutive job date ranges exceeding 2 years.

#### Feature 12: `keyword_stuffing_score`
Measures if the resume contains an unusually high density of job-description keywords —
a common tactic where candidates literally paste JD keywords throughout their resume.

**Critical fix applied (Bug 8):** Stopwords (`the`, `and`, `or`, `is`, `with`, etc.) are
filtered out before computing the ratio — otherwise every resume would appear keyword-stuffed
because of common prepositions shared with any JD.

```python
jd_words = {w for w in re.findall(r'\b[a-z]{3,}\b', jd_lower) if w not in _STOPWORDS}
resume_words = [w for w in re.findall(r'\b[a-z]{3,}\b', resume_lower) if w not in _STOPWORDS]

jd_word_hits = sum(1 for w in resume_words if w in jd_words)
ratio = jd_word_hits / len(resume_words)
return min(ratio * 2.5, 1.0)  # scale up, cap at 1.0
```

#### Feature 13: `years_experience`
Dynamically extracted from resume text using date-range parsing, overlap merging, and
"X years of experience" pattern matching. Capped at 50 years.

#### Feature 14: `num_certifications`
Counts distinct certifications using 26 specialized regex patterns:
AWS certified, Google Cloud professional/associate, Azure certified, CISSP, CEH, PMP,
Scrum Master, CSPO, Coursera/Udemy certificates, and 16 more. Capped at 30.

#### Feature 15: `num_skills`
Count of distinct skills identified using the `SKILL_KEYWORDS` taxonomy (200+ skills in
`data/taxonomy.json`) plus dynamic SBERT-based detection for unknown terms.

#### Feature 16: `education_level_encoded`
Ordinal encoding of the highest detected education level:

| Value | Education Level |
|-------|----------------|
| 0 | Diploma / Associate / High School / Unknown |
| 1 | Bachelor's / BA / BS / BSc / BTech / BEng |
| 2 | Master's / MBA / MA / MS / MSc / MEng |
| 3 | PhD / Doctorate / DPhil |

#### Feature 17: `has_previous_job`
Binary flag: 1 if the resume mentions a previous job title (work history), 0 otherwise.
Detected using 4-strategy detection logic (Bug 9 fix — no longer depends on newline
placement after date ranges).

---

## 9. Model Training & Evaluation

### Training Procedure Overview

Model training is implemented in `notebooks/01_eda_and_model.py` (289 lines). The pipeline
trains and evaluates both a **baseline Decision Tree** and a **GridSearchCV-tuned model**.

> **Important note:** The training script uses `DecisionTreeClassifier` (sklearn) for the
> initial baseline and tuning. The production server loads `xgboost_model.pkl` — an XGBoost
> model trained in a separate tuning session — which achieves the final metrics documented
> below. The XGBoost model supersedes the Decision Tree for all production predictions.

### Step 1: Label Encoding

```python
label_map = {'Authentic': 0, 'Suspicious': 1, 'Potentially Fake': 2}
df['target'] = df['classification'].map(label_map)

X = df[feature_cols].values   # shape: (4000, 17)
y = df['target'].values        # shape: (4000,)
```

### Step 2: Stratified Train/Test Split

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
# Training set: (3200, 17) | Test set: (800, 17)
```

### Step 3: Baseline Decision Tree

```python
from sklearn.tree import DecisionTreeClassifier
base_dt = DecisionTreeClassifier(random_state=42, class_weight='balanced')
base_dt.fit(X_train, y_train)
# Baseline performance: ~0.73 accuracy | ~0.72 weighted F1
```

**Why `class_weight='balanced'`?** The dataset has class imbalance (Potentially Fake is only
19.35%). Balanced weighting gives the minority class proportionally more influence during
training.

### Step 4: GridSearchCV Hyperparameter Tuning

```python
param_grid = {
    'max_depth': [3, 5, 7, 10, 15, None],
    'min_samples_split': [2, 5, 10, 20],
    'min_samples_leaf': [1, 2, 5, 10],
    'criterion': ['gini', 'entropy'],
    'class_weight': ['balanced', None]
}

grid = GridSearchCV(
    DecisionTreeClassifier(random_state=42),
    param_grid,
    cv=5,               # 5-fold cross-validation
    scoring='f1_weighted',
    n_jobs=-1,          # use all CPU cores
    verbose=1
)
grid.fit(X_train, y_train)
```

#### XGBoost Best Parameters (Production Model)

```python
best_params = {
    'learning_rate': 0.2,
    'max_depth': 5,
    'n_estimators': 50,
    'subsample': 0.8
}
```

| Parameter | Value | Rationale |
|-----------|-------|----------|
| `learning_rate` | 0.2 | Moderate — balances convergence speed and overfitting |
| `max_depth` | 5 | Prevents deep trees from memorizing noise |
| `n_estimators` | 50 | Sufficient boosting rounds given the feature count |
| `subsample` | 0.8 | Row subsampling reduces overfitting |

### Step 5: Evaluation Results

#### Final Model Performance (XGBoost — Production)

| Metric | Value |
|--------|-------|
| **Test Accuracy** | **0.87375 (87.375%)** |
| **Weighted F1** | **0.87219 (87.22%)** |
| Macro F1 | 0.8812 (88.12%) |
| Macro Precision | 0.8905 (89.05%) |
| Macro Recall | 0.8750 (87.50%) |

#### Per-Class Classification Report

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| **Authentic** | 0.8544 | 0.9275 | 0.8894 | 386 |
| **Suspicious** | 0.8435 | 0.7490 | 0.7935 | 259 |
| **Potentially Fake** | 0.9735 | 0.9484 | **0.9608** | 155 |
| macro avg | 0.8905 | 0.8750 | 0.8812 | 800 |
| weighted avg | 0.8739 | 0.8738 | 0.8722 | 800 |

#### Analysis of Per-Class Results

**Potentially Fake has the highest F1 (0.9608):** Fabricated resumes have very distinctive
patterns — extremely high `generic_phrase_score`, elevated `keyword_stuffing_score`, and low
`achievement_count`. These create clear boundaries that XGBoost detects with high confidence.

**Suspicious has the lowest recall (0.749):** 25% of suspicious resumes are misclassified as
Authentic. This is the primary area for model improvement.

**Authentic has high recall (0.9275):** The model is conservative about flagging genuine resumes
as fake — only 7.25% of genuine resumes are incorrectly flagged, minimizing false accusations.

### Confusion Matrix (Actual Values from metrics.json)

```
                  Predicted
               Auth.  Susp.  Fake
Actual Auth.    358     24     4     (386 total)
       Susp.     56    194     9     (259 total)
       Fake        4     4   147     (155 total)
```

### Feature Importance (From metrics.json — Actual Values)

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | `skill_overlap_score` | **20.23%** |
| 2 | `final_match_score` | **17.10%** |
| 3 | `generic_phrase_score` | **15.24%** |
| 4 | `keyword_stuffing_score` | 7.43% |
| 5 | `skill_density` | 7.03% |
| 6 | `semantic_similarity` | 5.70% |
| 7 | `promotion_speed` | 5.49% |
| 8 | `experience_relevance_score` | 3.55% |
| 9 | `overlapping_jobs` | 3.52% |
| 10 | `achievement_count` | 2.61% |
| 11 | `experience_graduation_gap` | 2.38% |
| 12 | `gap_years` | 2.08% |
| 13 | `education_level_encoded` | 1.78% |
| 14 | `num_skills` | 1.73% |
| 15 | `num_certifications` | 1.53% |
| 16 | `years_experience` | 1.41% |
| 17 | `has_previous_job` | 1.16% |
| — | `skill_experience_alignment` | 0.00% (no-op) |
| — | `ai_plausibility_score` | 0.00% (no-op) |

The top 5 features account for **67.0%** of the model's decision-making power.

### Classification Threshold Logic (Post-Processing)

```python
auth_prob = float(probs[i][0])   # probability of class 0 (Authentic)

if auth_prob >= 0.80:
    label = 'Authentic'
    confidence = auth_prob
elif auth_prob >= 0.50:
    label = 'Suspicious'
    confidence = max(auth_prob, float(probs[i][1]))
else:
    label = 'Potentially Fake'
    confidence = max(float(probs[i][2]), 1.0 - auth_prob)
```

**Why threshold post-processing?** Resumes with auth_prob >= 0.80 are firmly Authentic;
those between 0.50-0.79 are flagged as Suspicious rather than immediately condemned as Fake.
This reduces false accusations and gives candidates the benefit of the doubt.

### Saved Model Artifacts

```python
import joblib
joblib.dump({
    'model': best_estimator,           # XGBClassifier object
    'feature_names': feature_cols,      # list of 17 feature names
    'label_map': label_map,             # {'Authentic': 0, ...}
    'params': best_params,              # GridSearch best parameters
    'test_accuracy': float(test_acc),   # 0.87375
    'test_f1': float(test_f1),          # 0.87219
    'feature_importance': importance_list
}, 'data/models/xgboost_model.pkl')

# Also saved: data/processed/metrics.json (full classification report in JSON)
```
---

## 10. System Architecture

### High-Level Architecture Diagram

```
                    +--------------------------------------------------+
                    |                 User Browser                      |
                    |  Login | Register | HR Dashboard | Batch          |
                    |  Analytics | Applicant Portal                     |
                    +------------------+-----------------------------------+
                                       |  HTTPS (HTML/JS/CSS)
                                       v
                    +--------------------------------------------------+
                    |            FastAPI Application Server             |
                    |            app/main.py  (~1,014 lines)            |
                    |                                                   |
                    |  Middleware Stack:                                |
                    |  1. SlowAPIMiddleware   (rate limiting)           |
                    |  2. SessionMiddleware   (cookie auth)             |
                    |  3. RequestLogMiddleware (audit logging)          |
                    |                                                   |
                    |  Lifespan Startup:                                |
                    |  init_db() -> seed_users() -> load_model()        |
                    |  -> warm_spacy() -> warm_sbert()                  |
                    |  -> start _cleanup_batch_jobs() task             |
                    +---+------------+------------+--------------+------+
                        |            |            |             |
              +---------+    +-------+    +-------+    +--------+
              v              v            v            v
    +--------------+  +----------+  +----------+  +------------------+
    |  Document    |  |  SBERT   |  |  spaCy   |  |  PostgreSQL      |
    |  Parser      |  |  Embedder|  |  en_core |  |  (Supabase)      |
    |  PDF+OCR     |  |  384-dim |  |  _web_md |  |  users           |
    |  DOCX        |  |singleton |  |  + Ruler |  |  resume_analyses |
    |  TXT         |  +----+-----+  +----+-----+  |  job_descriptions|
    +---------+----+       |             |         +------------------+
              |             +------+------+
              +--------------------+
                                   v
                    +-----------------------------+
                    |  17-Feature Extractor        |
                    |  compute_all_validation_     |
                    |  features()                  |
                    +-------------+---------------+
                                  |
                                  v
                    +-----------------------------+
                    |  is_resume_format()          |
                    |  Score >= 45 -> OK           |
                    |  Score < 45  -> Not a Resume |
                    +-------------+---------------+
                                  |
                                  v
                    +-----------------------------+
                    |  XGBoost Classifier          |
                    |  87.375% test accuracy       |
                    |  + SHAP pred_contribs        |
                    +-------------+---------------+
                                  |
                    +-------------+---------------+
                    |                             |
                    v                             v
        +------------------+       +------------------------+
        |  Classification  |       |  LLM Verification      |
        |  Result +        |       |  Groq Llama-3.3-70B    |
        |  Confidence %    |       |  (only for Susp/Fake)  |
        |  Per-class probs |       |  Agree / Disagree      |
        |  SHAP Top-3      |       +------------------------+
        +------------------+
```

### Data Flow for a Single Prediction

1. User uploads resume (PDF/DOCX/TXT) + job description via `POST /api/predict`
2. `validate_upload()` — MIME type check + file size limit
3. `parse_resume()` — text extraction (pdfplumber -> OCR fallback / mammoth / encoding detection)
4. `langdetect.detect()` — language identification (logged; SBERT handles non-English)
5. `is_resume_format()` — multi-signal scoring; score < 45 -> return "Not a Resume"
6. `extract_years_experience()` + `extract_graduation_year()` — dynamic parsing
7. `compute_semantic_similarity_async()` — parallel SBERT embedding + cosine similarity
8. `compute_skill_overlap()` — taxonomy + dynamic SBERT skill extraction
9. `score_experience_relevance()` — job category keyword matching
10. `compute_all_validation_features()` — assembles all 17 features into dict
11. `predict()` — XGBoost classification + SHAP native pred_contribs
12. (Optional) `LLMDetector.verify_prediction()` — Groq second opinion for Suspicious/Fake
13. `extract_education_spacy()` + `extract_job_titles_spacy()` — NER for summary preview
14. DB save: `ResumeAnalysis` row inserted (linked to logged-in HR user)
15. JSON response returned with all results

### Async Batch Processing Architecture

```
POST /api/predict_batch
        |
        v
Generate job_id (UUID) -> store in batch_jobs dict -> return immediately
        |
        v (BackgroundTask)
for each resume file:
    asyncio.wait_for(process_resume(), timeout=60s)  <- per-file timeout
    -- asyncio.Semaphore(4) <- max 4 concurrent processes

        |
        v (parallel)
GET /api/batch_status/{job_id}  <- frontend polls every 2 seconds
        |
        +-- status: "processing" -> { total, completed, progress % }
        +-- status: "completed"  -> { results: [...all ranked results] }

Background: _cleanup_batch_jobs() coroutine
        +-- removes batch_jobs entries older than 30 minutes (TTL)
            runs every 5 minutes
```

---

## 11. Backend, Database & Authentication

### FastAPI Server — app/main.py (~1,014 lines)

**Server startup sequence (lifespan):**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()                    # 1. Load .env (PostgreSQL creds, API keys)
    await init_db()                  # 2. Create tables, run migrations
    await seed_default_users()       # 3. Ensure admin + applicant accounts exist
    load_model()                     # 4. Pre-warm XGBoost from xgboost_model.pkl
    get_nlp_with_ruler()             # 5. Pre-warm spaCy + EntityRuler
    get_sbert_model()                # 6. Pre-warm SBERT (all-MiniLM-L6-v2)
    asyncio.create_task(             # 7. Start TTL cleanup for batch jobs
        _cleanup_batch_jobs())
    yield
```

### Middleware Stack

| Middleware | Purpose | Configuration |
|-----------|---------|--------------|
| `SlowAPIMiddleware` | Rate limiting | 25/100/10 requests per minute per endpoint |
| `SessionMiddleware` | Session cookies | `SameSite="none"`, `https_only=True` |
| `RequestLogMiddleware` | Audit logging | Logs method, path, status code, duration ms |

### Authentication System

```python
async def authenticate(username, password, role, session):
    hashed = hashlib.sha256(password.encode()).hexdigest()

    # 1. Try PostgreSQL first
    db_user = await get_user_by_username(username)
    if db_user and db_user.password_hash == hashed and db_user.role == role:
        session['user'] = username
        session['role'] = role
        return True

    # 2. Fallback to hardcoded USERS dict
    if username in USERS and USERS[username]['password'] == hashed:
        if USERS[username]['role'] == role:
            session['user'] = username
            session['role'] = role
            return True

    return False
```

| Role | Access Level | Default Credentials |
|------|-------------|-------------------|
| `hr` | HR Dashboard, Batch, Analytics, History, Export, Delete | admin / hr2026 |
| `user` | Applicant Upload Portal only | applicant / apply2026 |

### Database Models — app/models/database.py

```python
class User(Base):
    __tablename__ = 'users'
    id            = Column(Integer, primary_key=True)
    username      = Column(String(80), unique=True, index=True, nullable=False)
    password_hash = Column(String(64), nullable=False)   # SHA-256 hex
    role          = Column(String(20), nullable=False)    # 'hr' | 'user'
    created_at    = Column(DateTime, server_default=func.now())

class JobDescription(Base):
    __tablename__ = 'job_descriptions'
    id               = Column(Integer, primary_key=True)
    title            = Column(String(255))
    description_text = Column(Text)
    created_at       = Column(DateTime, server_default=func.now())

class ResumeAnalysis(Base):
    __tablename__ = 'resume_analyses'
    id                    = Column(Integer, primary_key=True)
    job_id                = Column(Integer, ForeignKey('job_descriptions.id'), nullable=True)
    filename              = Column(String(255))
    candidate_name        = Column(String(255), nullable=True)
    username              = Column(String(80), index=True)    # which HR user ran this
    final_match_score     = Column(Float)
    ai_plausibility_score = Column(Float, default=0.5)
    classification        = Column(String(50))
    full_results          = Column(JSON)                      # complete API response
    created_at            = Column(DateTime, server_default=func.now())
```

**Multi-tenant data isolation:** Every database query is filtered by `username` —
each HR user sees only their own records.

### PostgreSQL Connection

```python
# Priority: DATABASE_URL env var -> then individual POSTGRES_* vars
url = os.environ.get("DATABASE_URL") or (
    f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
)
engine = create_async_engine(url, pool_pre_ping=True)
# pool_pre_ping=True: validates connection before each use
```

### Schema Migration (Auto-Run on Startup)

```python
# Safe idempotent migration - adds columns if missing
ALTER TABLE resume_analyses ADD COLUMN IF NOT EXISTS candidate_name VARCHAR(255);
ALTER TABLE resume_analyses ADD COLUMN IF NOT EXISTS full_results JSON;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
```

---

## 12. Frontend — 6-Page Web UI

### Design System

| Element | Value |
|---------|-------|
| Font (headings) | Plus Jakarta Sans |
| Font (body) | DM Sans |
| Background | `#f0f4f9` (soft blue-gray) |
| Card surfaces | `#ffffff` |
| Primary text | `#1e3a5f` (navy) |
| Accent color | `#2563eb` (blue) |
| Navbar | Glassmorphism `backdrop-filter: blur(16px)` |
| Charts | Chart.js 4.4 animated doughnut |

### Page 1: Login — `/login`
- Role selector: HR Professional or Applicant
- Dual auth: PostgreSQL users first, hardcoded fallback second
- Redirect: HR -> `/` | Applicant -> `/user/upload`

### Page 2: Register — `/register`
- Fields: username (min 3), password (min 6), confirm, role selector
- Writes to PostgreSQL `users` table with SHA-256 hashed password

### Page 3: HR Dashboard — `/` (Single Resume Analysis)

**Left column (upload form):**
- File picker (PDF/DOCX/TXT)
- Optional job title field (max 200 chars)
- Job description textarea (max 3,000 chars) OR JD file upload

**Right column (results panel):**
- **Classification badge** — green/amber/red/gray with confidence %
- **Decision Explainability card** — SHAP top-3 feature contribution bars
- **Skill Gap Analytics** — Chart.js animated doughnut (matched / missing / extra)
- **Skills section** — green (matched), red (missing), blue (extra) chips
- **Match scores grid** — semantic, skill, experience, final; color-coded
- **Validation signals grid** — all 17 feature values
- **LLM verification panel** — consensus + reasoning text (if GROQ_API_KEY set)
- **Resume summary** — anonymized preview: experience, past roles, education, top skills
- **History section** — last 50 scans; clickable rows; per-row delete

### Page 4: Batch Screening — `/batch`
- Multi-file picker, job description (text or file)
- Progress bar polls every 2 seconds
- Results table: sorted Authentic -> Suspicious -> Fake -> Not a Resume, then by match score
- SHAP top-3 inline for each batch result row
- **"Download CSV"** button — client-side CSV generation

### Page 5: Analytics Dashboard — `/analytics`

Parallel fetch on page load:
1. **Hero stats** — 4,000 samples | 87.375% accuracy | 87.22% F1
2. **Model configuration** — best params table
3. **Feature importance** — animated horizontal bars with % labels
4. **Class distribution** — SVG donut with legend
5. **Confusion matrix PNG** — served from `/static/confusion_matrix.png`
6. **Correlation matrix PNG** — served from `/static/correlation_matrix.png`
7. **Export Metrics CSV** -> `GET /api/export/analytics`

### Page 6: Applicant Upload Portal — `/user/upload`
- Simple file upload form (no JD required)
- `POST /user/submit` — saves to DB with `classification="Pending"`
- No prediction result returned (privacy by design)
- Rate limited: 10 req/min per IP
---

## 13. API Endpoints Reference

### Auth Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/login` | Show login form |
| POST | `/login` | Authenticate; set session cookie; redirect |
| GET | `/logout` | Clear session; redirect to `/login` |
| GET | `/register` | Show registration form |
| POST | `/register` | Create user in PostgreSQL; redirect |

### Page Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | HR | Single resume HR dashboard |
| GET | `/batch` | HR | Batch screening page |
| GET | `/analytics` | HR | Analytics + model metrics dashboard |
| GET | `/user/upload` | Any | Applicant resume upload portal |

### Utility Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | `{"status":"ok","model_loaded":true/false}` |
| GET | `/favicon.ico` | Favicon |
| GET | `/robots.txt` | robots.txt with `text/plain` MIME type |
| GET | `/sitemap.xml` | sitemap with `application/xml` MIME type |
| GET | `/static/{path}` | Static files (CSS, PNG charts) |

### REST API — ML / Data Endpoints

#### POST /api/predict — Single Resume Analysis
**Rate limit:** 25 req/min per IP

**Request:** `multipart/form-data`
- `resume` — UploadFile (required, .pdf/.docx/.txt)
- `job_title` — str (optional, max 200 chars)
- `job_description` — str (max 3,000 chars)
- `job_description_file` — UploadFile (optional alternative)

**Success Response (`200 OK`):**
```json
{
  "status": "success",
  "filename": "resume.pdf",
  "resume_preview": "Experience: ~5 years\nPast Roles: Software Engineer\nEducation: Bachelor Of Science (2019)\nTop Skills: Python, AWS, Docker",
  "scores": {
    "semantic_similarity": 0.5851,
    "skill_overlap_score": 0.1429,
    "experience_relevance_score": 1.0,
    "final_match_score": 0.5341
  },
  "skills": {
    "matched": ["Python", "AWS"],
    "missing": ["Kubernetes"],
    "extra": ["Docker", "React"],
    "match_count": 2, "missing_count": 1, "extra_count": 2
  },
  "validation": {
    "semantic_similarity": 0.5851,
    "skill_overlap_score": 0.1429,
    "overlapping_jobs": 0,
    "generic_phrase_score": 0.12,
    "keyword_stuffing_score": 0.33,
    "achievement_count": 7,
    "skill_density": 1.4,
    "gap_years": 0,
    "years_experience": 5,
    "num_certifications": 2,
    "num_skills": 15,
    "education_level_encoded": 1,
    "skill_experience_alignment": 0.76
  },
  "classification": {
    "classification": "Authentic",
    "confidence": 0.87,
    "prob_Authentic": 0.87,
    "prob_Suspicious": 0.09,
    "prob_Potentially Fake": 0.04,
    "top_features": [
      {"feature": "skill_overlap_score", "value": 0.14, "contribution": 0.38},
      {"feature": "generic_phrase_score", "value": 0.12, "contribution": -0.19},
      {"feature": "final_match_score",    "value": 0.53, "contribution": 0.28}
    ],
    "llm_verification": {
      "consensus": "Agree",
      "reasoning": "Resume demonstrates concrete projects and realistic progression."
    }
  }
}
```

#### POST /api/predict_batch — Async Batch Screening
**Rate limit:** 100 req/min per IP

Immediate response:
```json
{"status": "processing", "job_id": "550e8400-e29b-41d4-a716-446655440000"}
```

#### GET /api/batch_status/{job_id} — Poll Batch Progress
```json
{"status": "processing", "total": 10, "completed": 7, "progress": 70, "results": null}
```
When done: `"status": "completed"` and `"results": [...]`

#### GET /api/history — User History
Query params: `limit=50`, `offset=0`. Returns records for current user only.

#### DELETE /api/history/{id} — Delete Record
HR role only. Deletes record belonging to current user.

#### GET /api/export — Export History
Query params: `format=csv` (default) | `format=json`. Streaming response.

#### GET /api/model/info — Model Metadata
Returns feature names, hyperparameters, test_accuracy (0.87375), test_f1, feature_importance.

#### GET /api/class_distribution — Class Counts
Returns `{Authentic: 1930, Suspicious: 1296, Potentially Fake: 774}` from metrics.json.

#### GET /api/dataset/stats — Feature Statistics
Returns mean, std, min, max for all 17 features from `combined_dataset.csv`.

#### GET /api/export/analytics — Analytics CSV Download
Returns `clearhire_analytics.csv` with model accuracy, F1, per-class metrics, feature importance.

#### POST /user/submit — Applicant File Submit
**Rate limit:** 10 req/min per IP. Saves resume to DB with `classification="Pending"`.

---

## 14. NLP Layer — spaCy Integration

### Model

**spaCy model:** `en_core_web_md` (medium English — 40MB, better NER than `sm`)

Downloaded at Docker build time:
```dockerfile
RUN python -m spacy download en_core_web_md
```

### Pipeline Architecture

```python
# app/utils/nlp.py

_nlp = None  # singleton

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load('en_core_web_md')
        except OSError:
            _nlp = False   # triggers regex fallback everywhere
    return _nlp if _nlp is not False else None

def get_nlp_with_ruler():
    nlp = get_nlp()
    if nlp is None:
        return None
    if "entity_ruler" not in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", before="ner")
    return nlp
```

### Custom EntityRuler Patterns

A custom `EntityRuler` is added before the `ner` component, injecting skill, education, and
job-title patterns:

```python
# SKILL patterns (200+ from taxonomy)
{"label": "SKILL", "pattern": "Python"}
{"label": "SKILL", "pattern": "Kubernetes"}

# EDUCATION patterns
{"label": "EDUCATION", "pattern": [{"LOWER": "bachelor"}, {"LOWER": "of"}, {"LOWER": "science"}]}

# JOB_TITLE patterns
{"label": "JOB_TITLE", "pattern": "Software Engineer"}
{"label": "JOB_TITLE", "pattern": "Data Scientist"}
```

### Extraction Functions

| Function | Entities Used | Fallback |
|----------|--------------|---------|
| `extract_education_spacy(text)` | EDUCATION entities | Regex: `bachelor`, `master`, `phd` |
| `extract_job_titles_spacy(text)` | JOB_TITLE, ORG entities | Regex: common title keywords |
| `is_resume_format(text)` | ORG + DATE + PERSON count | Scoring still works without NER |

**Graceful fallback** — if `en_core_web_md` is missing (OSError), every function that calls
`get_nlp()` receives `None` and silently switches to regex-based extraction. No crash.

---

## 15. LLM Verification Layer

### Purpose

A **second-opinion layer** using Groq Llama-3.3-70B to re-evaluate authenticity for cases
where XGBoost classifies a resume as `Suspicious` or `Potentially Fake`.

### Module: `app/models/llm_detector.py` (237 lines)

```python
class LLMProvider(ABC):          # Abstract base class
    @abstractmethod
    async def verify_prediction(text, jd, local_classification): ...

class GroqProvider(LLMProvider): # Groq implementation
    model = "llama-3.3-70b-versatile"
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
```

### Verification Logic

```python
async def verify_prediction(resume_text, job_description, local_classification):
    # Only run for borderline/negative classifications
    if local_classification == "Authentic":
        return None

    # Sanitize against prompt injection
    safe_resume = sanitize_llm_input(resume_text[:2000])
    safe_jd = sanitize_llm_input(job_description[:500])

    prompt = f"""You are an expert HR consultant reviewing a resume.
The ML model classified this resume as: {local_classification}

Resume: {safe_resume}
Job Description: {safe_jd}

Does the ML model's classification seem correct?
Reply EXACTLY: "Agree: [reason]" or "Disagree: [reason]"
"""
    response = await client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=150
    )
```

### Prompt Injection Protection

```python
def sanitize_llm_input(text: str) -> str:
    patterns = [
        r'ignore previous instructions',
        r'system prompt',
        r'forget everything',
        r'you are now',
        r'jailbreak'
    ]
    for pattern in patterns:
        text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
    return text
```

### Graceful Degradation

| Condition | Behavior |
|-----------|---------|
| `GROQ_API_KEY` not set | LLM layer skipped silently |
| API call fails / timeout | Exception caught; XGBoost result used |
| LLM response unparseable | Returns `None`; XGBoost result used |
| Classification is Authentic | LLM not called (not needed) |

---

## 16. SHAP Explainability

### Why SHAP?

Black-box ML decisions in HR contexts raise fairness and transparency concerns. SHAP explains
WHY the model made a specific decision by attributing each feature's contribution to the
final prediction score — making ClearHire **auditable**.

### Implementation — XGBoost Native pred_contribs

```python
# app/models/classifier.py

def _compute_xgboost_shap(model, X: np.ndarray):
    import xgboost as xgb

    booster = model.get_booster()
    dmat = xgb.DMatrix(X)

    # pred_contribs returns shape: (n_samples, n_features+1, n_classes)
    # Last column is the bias term -> exclude with [:-1]
    contribs = booster.predict(dmat, pred_contribs=True)

    # Return per-class list of (n_samples, n_features) arrays
    return [contribs[:, :-1, c] for c in range(contribs.shape[2])]
```

### SHAP Output Format

```python
instance_shap = shap_vals[cls_int][i]
top_indices = np.argsort(np.abs(instance_shap))[::-1][:3]  # top 3 by magnitude

explanations = [
    {
        'feature':      cols[idx],
        'value':        round(float(X[i][idx]), 4),
        'contribution': round(float(instance_shap[idx]), 4)
    }
    for idx in top_indices if abs(instance_shap[idx]) > 0.0001
]
```

### UI Display

Each prediction page shows a **Decision Explainability card** with colored horizontal bars:

- **Green bar** (positive contribution) — feature pushed toward Authentic
- **Red bar** (negative contribution) — feature pushed toward Suspicious/Fake

Example for an Authentic resume:
```
skill_overlap_score  = 0.4800  ||||||||||||||||  +0.38 (pushes -> Authentic)
generic_phrase_score = 0.0300  ||||              +0.15 (very low, good sign)
keyword_stuffing     = 0.1200  ||||||            -0.08 (slightly suspicious)
```

Example for a Potentially Fake resume:
```
generic_phrase_score = 0.8700  ||||||||||||||||  +0.62 (pushes -> Fake)
keyword_stuffing     = 0.9200  |||||||||||||     +0.51 (pushes -> Fake)
skill_overlap_score  = 0.0100  ||                -0.12 (low -> against Authentic)
```

---

## 17. Document Format Support & OCR

### Format Support Matrix

| Format | Parser | Fallback | Notes |
|--------|--------|---------|-------|
| `.pdf` | pdfplumber `layout=True` | pytesseract OCR | Layout-aware; handles multi-column |
| `.docx` | mammoth | python-docx | mammoth gives cleaner text |
| `.doc` | mammoth | python-docx | Same as DOCX |
| `.txt` | UTF-8 decode | latin-1 -> cp1252 -> replace | 4-tier encoding detection |
| Other | Treated as TXT | — | Best effort |

### OCR Fallback Details

```python
# Triggered when pdfplumber extracts < 50 characters
if len(text) < 50:
    from pdf2image import convert_from_bytes
    import pytesseract

    # LIMIT: First 2 pages only — critical performance optimization
    images = convert_from_bytes(file_bytes, first_page=1, last_page=2)
    for img in images:
        ocr_text += pytesseract.image_to_string(img) + "\n"
```

**System dependencies required for OCR:**
- `tesseract-ocr` — OCR engine (auto-installed in Dockerfile)
- `poppler-utils` — PDF -> image conversion (auto-installed in Dockerfile)

For Windows local development: install Tesseract from
`https://github.com/UB-Mannheim/tesseract/wiki`

---

## 18. System Integration & Testing

### How Components Are Integrated

| Component | Integrated via | Communication |
|-----------|---------------|--------------|
| SBERT Embedder | `app/models/embedder.py` singleton | In-process |
| XGBoost Classifier | `app/models/classifier.py` singleton | In-process (joblib) |
| spaCy NER | `app/utils/nlp.py` singleton | In-process (spaCy pipeline) |
| PostgreSQL | `app/models/database.py` async | asyncpg connection pool |
| Groq LLM | `app/models/llm_detector.py` | HTTPS API call (optional) |
| Document Parser | `app/utils/parser.py` | In-process |
| Frontend Templates | `app/templates/*.html` | Jinja2 server-side rendering |

**All ML components are pre-warmed at startup** — no cold-start delay on first request.

### Testing Overview

**Test directory:** `tests/` (15 test files, 152+ test methods — all passing)

| Test File | What it covers |
|-----------|---------------|
| `test_api.py` | All API endpoints |
| `test_classifier.py` | XGBoost wrapper, `predict()`, SHAP output structure |
| `test_experience.py` | `score_experience_relevance()` correctness |
| `test_experience_extraction.py` | `extract_years_experience()`, `extract_graduation_year()` |
| `test_validation.py` | All 17 validation feature functions individually |
| `test_skill_overlap.py` | `compute_skill_overlap()`, `extract_skills()`, Jaccard scoring |
| `test_parser.py` | PDF/DOCX/TXT parsing, OCR fallback path |
| `test_pg_migration.py` | PostgreSQL schema migration |
| `test_live_api.py` | Live integration tests against running server |
| `e2e_test.py` | End-to-end test scenarios (upload -> classify -> history -> delete) |
| `conftest.py` | Shared fixtures: `auth_client` + `client` |

#### Running Tests

```cmd
..\venv\Scripts\python.exe -m pytest tests/ -v
# Expected: all tests passed
```

### Integration Test Scenarios

#### Scenario 1: Full Single Analysis (Happy Path)
1. POST `/login` with HR credentials -> session cookie set
2. POST `/api/predict` with valid PDF + JD -> `status: success`
3. Verify: classification, confidence, scores, skills, validation, top_features all present
4. GET `/api/history` -> new record in first position
5. DELETE `/api/history/{id}` -> record removed

#### Scenario 2: Not-a-Resume Detection
1. POST `/api/predict` with a PDF of a research paper
2. Verify: `classification: "Not a Resume"`, `confidence: 1.0`
3. Verify: no PostgreSQL record saved

#### Scenario 3: Batch Processing Async Flow
1. POST `/api/predict_batch` with 5 resumes -> immediate `job_id` response
2. Poll `GET /api/batch_status/{job_id}` -> `{"status":"processing","progress":60}`
3. Poll until -> `{"status":"completed","results":[...]}`
4. Verify results sorted: Authentic first, then Suspicious, then Fake

#### Scenario 4: Rate Limit Enforcement
1. Send 26 consecutive POST `/api/predict` requests within 60 seconds
2. Verify: requests 1-25 return 200; request 26 returns 429 Too Many Requests

#### Scenario 5: Multi-Tenant Isolation
1. Login as `admin` -> analyze resume -> record in DB
2. Login as `applicant` -> GET `/api/history` -> admin's record NOT visible
---

## 19. Experimental Setup

### Hardware Environment

| Component | Specification |
|-----------|-------------|
| Development OS | Windows 11 (64-bit) |
| CPU | Intel Core i5/i7 (4-8 cores) |
| RAM | 8 GB minimum (16 GB recommended) |
| Storage | 2 GB for models + dataset |
| GPU | Not required — all inference on CPU |

### Software Environment

| Software | Version |
|---------|---------|
| Python | 3.10.x |
| PostgreSQL | 14.x or 15.x |
| spaCy | 3.5.x+ |
| Docker | 24.x+ |
| OS (production) | Ubuntu 22.04 (Docker on Hugging Face Spaces) |

### Python Library Versions (from requirements.txt)

| Library | Purpose |
|---------|---------|
| `fastapi >= 0.100.0` | REST API framework |
| `uvicorn >= 0.23.0` | ASGI server |
| `xgboost >= 2.0.0` | Gradient boosting classifier |
| `sentence-transformers >= 2.2.0` | SBERT embeddings |
| `spacy >= 3.5.0` | NLP / NER pipeline |
| `SQLAlchemy >= 2.0.20` | Async ORM |
| `asyncpg >= 0.29.0` | Async PostgreSQL driver |
| `psycopg2-binary >= 2.9.9` | Sync PostgreSQL driver |
| `pdfplumber >= 0.10.0` | PDF text extraction (layout-aware) |
| `mammoth >= 1.6.0` | DOCX text extraction |
| `pytesseract >= 0.3.10` | OCR for scanned PDFs |
| `pdf2image >= 1.16.3` | PDF -> image for OCR |
| `langdetect >= 1.0.9` | Language detection |
| `slowapi >= 0.1.8` | Rate limiting |
| `python-dotenv >= 1.0.0` | .env file loading |
| `groq >= 0.4.2` | Groq LLM API client |
| `itsdangerous >= 2.1.0` | Session cookie signing |
| `cachetools >= 5.3.1` | In-memory caching |
| `Pillow >= 10.0.0` | Image processing (OCR) |
| `pandas >= 1.5.0` | Data manipulation |
| `numpy >= 1.24.0,<2.0.0` | Numerical arrays |
| `scikit-learn >= 1.2.0` | GridSearchCV, metrics, DT |
| `matplotlib >= 3.7.0` | EDA chart generation |
| `seaborn >= 0.12.0` | Statistical visualization |
| `aiofiles >= 23.1.0` | Async file I/O |
| `python-multipart >= 0.0.6` | Form/file upload parsing |
| `shap >= 0.42.1` | SHAP explainability (imported) |

### Dataset Configuration

| Parameter | Value |
|-----------|-------|
| Dataset file | `resume_dataset_4000_tech.csv` |
| Encoding | `latin-1` |
| Rows | 4,000 |
| Feature columns | 17 (after engineering) |
| Target column | `classification` (3 classes) |
| Training samples | 3,200 (80%) |
| Test samples | 800 (20%) |
| Random seed | 42 |
| CV folds | 5 |
| CV scoring | `f1_weighted` |

### Model Configuration

| Parameter | Value |
|-----------|-------|
| Model type | XGBoost (`XGBClassifier`) |
| Learning rate | 0.2 |
| Max depth | 5 |
| N estimators | 50 |
| Subsample | 0.8 |
| Eval metric | `mlogloss` (multiclass log loss) |
| SHAP method | `pred_contribs` (XGBoost native) |
| Model file | `data/models/xgboost_model.pkl` |
| Model size | ~1.2 MB (serialized via joblib) |

### Inference Performance (CPU)

| Operation | Typical Time |
|-----------|-------------|
| SBERT embedding (per text) | 200-500ms |
| XGBoost prediction (per resume) | < 5ms |
| spaCy NER (per resume) | 50-150ms |
| pdfplumber PDF parsing | 100-800ms |
| OCR fallback (2 pages) | 5-30 seconds |
| Groq LLM call | 1-3 seconds |
| **Total single-resume (no OCR/LLM)** | **~2-5 seconds** |
| **Total with OCR + LLM** | **~8-35 seconds** |

---

## 20. Project File Structure

```
resume-screener/
|
+-- app/                              # APPLICATION SOURCE CODE
|   +-- __init__.py
|   +-- main.py                       # FastAPI server (~1,014 lines, 20+ endpoints)
|   +-- logger.py                     # Centralized structured logging setup
|   |
|   +-- models/                       # ML model wrappers + database layer
|   |   +-- __init__.py
|   |   +-- classifier.py             # XGBoost wrapper + SHAP (307 lines)
|   |   +-- embedder.py               # SBERT singleton + cosine similarity
|   |   +-- database.py               # SQLAlchemy async ORM models (165 lines)
|   |   +-- llm_detector.py           # Groq Llama-3.3-70B integration (237 lines)
|   |
|   +-- features/                     # Feature extraction pipeline
|   |   +-- __init__.py
|   |   +-- semantic.py               # SBERT cosine similarity, sync + async versions
|   |   +-- skill_overlap.py          # extract_skills(), compute_skill_overlap()
|   |   +-- experience.py             # score_experience_relevance()
|   |   +-- experience_extraction.py  # extract_years_experience(), extract_graduation_year()
|   |   +-- validation.py             # All 17 validation feature extractors (386 lines)
|   |
|   +-- utils/                        # Utility modules
|   |   +-- __init__.py
|   |   +-- parser.py                 # PDF+OCR, DOCX, TXT parser (194 lines)
|   |   +-- taxonomy.py               # Dynamic taxonomy loader from taxonomy.json
|   |   +-- aliases.py                # Skill alias normalization (10,926 bytes)
|   |   +-- file_validator.py         # MIME type + file size validation
|   |   +-- nlp.py                    # spaCy NER helpers (196 lines)
|   |
|   +-- static/                       # Static assets
|   |   +-- class_distribution.png
|   |   +-- confusion_matrix.png
|   |   +-- correlation_matrix.png
|   |   +-- decision_tree.png
|   |   +-- feature_distributions.png
|   |   +-- feature_importance.png
|   |   +-- style.css                 # Global stylesheet (37,105 bytes)
|   |   +-- favicon.ico
|   |
|   +-- templates/                    # Jinja2 HTML templates
|       +-- index.html                # HR Dashboard (43,332 bytes)
|       +-- batch.html                # Batch screening (53,549 bytes)
|       +-- analytics.html            # Analytics dashboard (60,776 bytes)
|       +-- login.html                # Login page (18,715 bytes)
|       +-- register.html             # Registration page (17,921 bytes)
|       +-- user_upload.html          # Applicant portal (16,150 bytes)
|
+-- data/
|   +-- processed/
|   |   +-- combined_dataset.csv      # Processed 4,000-row dataset (3.7 MB, 35 cols)
|   |   +-- metrics.json              # Full training metrics + classification report
|   |   +-- *.png                     # EDA charts (copied to app/static/ for serving)
|   +-- models/
|   |   +-- xgboost_model.pkl         # Serialized XGBoost model (joblib, ~1.2 MB)
|   +-- taxonomy.json                 # Skill keywords, job categories, generic phrases
|
+-- notebooks/
|   +-- 01_eda_and_model.py           # EDA + model training script (289 lines)
|
+-- tests/                            # Test suite (16 files, 152+ tests)
|   +-- conftest.py
|   +-- test_api.py
|   +-- test_classifier.py
|   +-- test_experience.py
|   +-- test_experience_extraction.py
|   +-- test_validation.py
|   +-- test_skill_overlap.py
|   +-- test_parser.py
|   +-- test_pg_migration.py
|   +-- test_live_api.py
|   +-- e2e_test.py
|   +-- test_validation.json
|
+-- logs/
|   +-- app.log
|
+-- .env                              # Environment variables (git-ignored)
+-- .gitignore
+-- Dockerfile                        # Docker container definition
+-- requirements.txt                  # Python dependencies (36 packages)
+-- robots.txt
+-- sitemap.xml
+-- run.bat                           # Windows one-click launcher
+-- LATEST_FEATURES.md
+-- README.md                         # This document
```

---

## 21. Installation & Setup

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | 3.10 or 3.11 recommended |
| pip | 23.x | Bundled with Python |
| PostgreSQL | 14 or 15 | Must be running on port 5432 |
| Tesseract OCR | 5.x | Optional — only for scanned PDFs |
| Docker | 24.x | Optional — only for containerized run |

### Step 1: Navigate to the Project Directory

```cmd
cd "c:\Users\acer\PROJECTS\A Minor NCE\FOR FINAL DEFENSE\resume-screener - Copy (2) (1)\resume-screener - Copy\resume-screener - Copy\resume-screener"
```

### Step 2: Create Virtual Environment (One Level Up)

```cmd
cd ..
python -m venv venv
```

### Step 3: Activate the Virtual Environment

```cmd
venv\Scripts\activate
```

### Step 4: Install Python Dependencies

```cmd
pip install -r resume-screener\requirements.txt
```

### Step 5: Download spaCy Language Model

```cmd
python -m spacy download en_core_web_md
```

### Step 6: Configure Environment Variables

```cmd
copy resume-screener\.env resume-screener\.env.local
# Edit .env and set POSTGRES_PASSWORD to your PostgreSQL password
```

### Step 7: Create PostgreSQL Database

```sql
-- Run in psql or pgAdmin
CREATE DATABASE resume_screener;
```

The application will **auto-create all tables** on first startup via `init_db()`.

### Step 8: Verify Model and Dataset Files Exist

```cmd
dir resume-screener\data\models\xgboost_model.pkl
dir resume-screener\data\processed\combined_dataset.csv
dir resume-screener\data\processed\metrics.json
```

If `xgboost_model.pkl` is missing, retrain:
```cmd
python resume-screener\notebooks\01_eda_and_model.py
```

---

## 22. Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `POSTGRES_HOST` | `localhost` | No | PostgreSQL server hostname |
| `POSTGRES_PORT` | `5432` | No | PostgreSQL server port |
| `POSTGRES_DB` | `resume_screener` | No | Database name |
| `POSTGRES_USER` | `postgres` | No | Database username |
| `POSTGRES_PASSWORD` | _(empty)_ | **Yes** | Database password |
| `DATABASE_URL` | _(none)_ | No | Full connection URL — overrides all POSTGRES_* vars |
| `SESSION_SECRET` | _(random UUID)_ | Recommended | Session cookie signing key |
| `GROQ_API_KEY` | _(none)_ | No | Groq API key — enables LLM double-check layer |

### Example .env

```env
# PostgreSQL - Local Development
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=resume_screener
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mypassword

# Session (fixed for persistence across restarts)
SESSION_SECRET=a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4

# Groq LLM (optional)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxx
```

### For Supabase (Production)

```env
DATABASE_URL=postgresql+asyncpg://postgres.PROJECTID:PASSWORD@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres
```

---

## 23. How to Run

### Quick Start — Windows (Recommended)

```cmd
run.bat
```

**What `run.bat` does automatically:**
1. Activates `../venv/Scripts/activate.bat`
2. Checks if PostgreSQL is running on port 5432
3. Checks if `en_core_web_md` is installed (downloads if missing)
4. Checks if SBERT `all-MiniLM-L6-v2` is cached (downloads if missing)
5. Starts server: `python app\main.py` on port 8000

### Manual Start

```cmd
python app/main.py
# Or with auto-reload for development:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Application URLs

| URL | Page | Auth Required |
|-----|------|--------------|
| http://localhost:8000/login | Login (start here) | None |
| http://localhost:8000/ | HR Dashboard | HR |
| http://localhost:8000/batch | Batch Screening | HR |
| http://localhost:8000/analytics | Analytics Dashboard | HR |
| http://localhost:8000/user/upload | Applicant Upload | Any |
| http://localhost:8000/health | Health Check API | None |

### Docker Run

```cmd
docker build -t clearhire .

docker run -p 8000:7860 ^
  -e POSTGRES_HOST=host.docker.internal ^
  -e POSTGRES_PASSWORD=your_password ^
  -e SESSION_SECRET=your_fixed_secret ^
  -e GROQ_API_KEY=gsk_xxx ^
  clearhire
```

---

## 24. How to Use — Step by Step

### HR: Single Resume Analysis

1. Navigate to http://localhost:8000/login
2. Select **HR Professional**, enter `admin` / `hr2026`, click Login
3. Upload a **resume file** (PDF/DOCX/TXT)
4. Enter **Job Title** (optional) and **Job Description**
5. Click **"Analyze Resume"** — wait 2-5 seconds
6. Results appear:
   - Classification badge with confidence %
   - SHAP Decision Explainability — top 3 contributing features
   - Skill Gap Chart — animated doughnut
   - All match scores and 17 validation feature values
   - Resume summary preview

### HR: Batch Screening

1. Navigate to http://localhost:8000/batch
2. Select **multiple resume files** (Ctrl+click)
3. Enter Job Description, click **"Screen All Resumes"**
4. Progress bar updates every 2 seconds
5. Ranked results table when complete — click **"Download CSV"** to export

### HR: Analytics Dashboard

1. Navigate to http://localhost:8000/analytics
2. Dashboard auto-loads: accuracy, F1, feature importance, confusion matrix
3. Click **"Export Metrics CSV"** to download model performance data

### Applicant: Upload Resume

1. Navigate to http://localhost:8000/login
2. Select **Applicant**, enter `applicant` / `apply2026`, click Login
3. Upload resume file, click Submit
4. (No classification shown to applicants — privacy by design)

### Register a New Account

1. Navigate to http://localhost:8000/register
2. Enter username (min 3 chars), password (min 6 chars), confirm password, select role
3. Click Register -> redirects to Login with success message
---

## 25. Classification & Color Psychology

| UI Element | Color Hex | Psychology |
|-----------|----------|-----------|
| Primary headings | `#1e3a5f` (navy) | Trust, authority, professionalism |
| Action buttons | `#2563eb` (blue) | Reliability, clarity, calls to action |
| Page background | `#f0f4f9` (soft blue-gray) | Clean, calm, non-distracting |
| Card surfaces | `#ffffff` (white) | Focus, clarity |
| Authentic badge | `#059669` (green) | **Safety, verified, approved, success** |
| Suspicious badge | `#d97706` (amber) | **Caution, needs review, warning** |
| Potentially Fake badge | `#dc2626` (red) | **Danger, reject, fraud alert** |
| Not a Resume badge | `#6b7280` (gray) | **Neutral, informational** |
| SHAP positive bar | `#059669` (green) | Feature pushes toward Authentic |
| SHAP negative bar | `#dc2626` (red) | Feature pushes toward Fake |
| Match score — high | `#059669` (green) | >= 70% — strong alignment |
| Match score — medium | `#d97706` (amber) | 35-69% — partial fit |
| Match score — low | `#dc2626` (red) | < 35% — weak fit |

**Color-blind accessibility:** All badges include both color AND text label AND icon (check/warning/X/robot)
so color-blind users can distinguish classifications without relying on color alone.

---

## 26. Rate Limiting & Security

### Rate Limits

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `POST /api/predict` | 25 req/min per IP | ML inference is CPU-intensive |
| `POST /api/predict_batch` | 100 req/min per IP | Batch job size already limits load |
| `POST /user/submit` | 10 req/min per IP | Prevents applicant spam |

**Implementation:** `slowapi` with `Limiter(key_func=get_remote_address)`.
Exceeding limits returns `HTTP 429 Too Many Requests`.

### Security Measures

| Measure | Implementation |
|---------|---------------|
| Password hashing | SHA-256 hex digest; plaintext never stored |
| Session cookies | `itsdangerous`-signed; `SameSite=None; Secure=True` |
| Multi-tenant isolation | All DB queries filtered by `username` |
| File type validation | MIME type check before processing |
| Input length limits | job_title: 200 chars; JD: 3,000 chars |
| LLM prompt injection | Regex strips "ignore instructions" patterns |
| Record delete auth | Only HR role; only own records |
| SESSION_SECRET | From env var; random fallback for dev |
| HTTPS in production | Enforced by Hugging Face Spaces + Cloudflare |

---

## 27. Edge Case Handling

| Scenario | Detection | Response |
|----------|-----------|---------|
| Empty resume / < 20 chars extracted | Text length check | `400`: "Could not extract enough text" |
| Not a resume (research paper, etc.) | `is_resume_format()` score < 45 | Classification: "Not a Resume" |
| No job description provided | Input validation | `400`: "Job description required" |
| Wrong file type | MIME type check | `422` validation error |
| Scanned/image PDF | pdfplumber < 50 chars | OCR fallback via pytesseract (2 pages) |
| DOCX parse failure | mammoth exception | python-docx fallback |
| TXT encoding issues | UTF-8 decode failure | latin-1 -> cp1252 -> replace fallback |
| Model file missing | FileNotFoundError | `_HeuristicFallbackClassifier` used |
| spaCy model not installed | OSError on load | Regex-based NER fallback (no crash) |
| Groq API key missing | env var absent | LLM layer silently skipped |
| Groq API call failure | Exception caught | LLM skipped; XGBoost result used |
| Short job description (< 15 words) | Word count check | SBERT + token-overlap blend |
| Batch corrupt/unreadable file | Exception per file | Error dict for that file; batch continues |
| Batch file taking > 60 seconds | `asyncio.wait_for` timeout | File marked timed-out; batch continues |
| Batch > 4 concurrent processes | `asyncio.Semaphore(4)` | Queued; no server overload |
| Batch memory leak | TTL cleanup coroutine | Entries > 30 min auto-deleted (every 5 min) |
| PostgreSQL idle timeout | `pool_pre_ping=True` | Connection validated before each use |
| Schema migration on old DB | `ADD COLUMN IF NOT EXISTS` | Idempotent; runs safely every startup |
| User accessing other user's data | username filter in all DB queries | Returns only own records |

---

## 28. Cloud Deployment

### Production Stack

| Component | Service | Configuration |
|-----------|---------|--------------|
| Application host | Hugging Face Spaces (Docker SDK) | Port 7860 |
| Database | Supabase PostgreSQL | ap-northeast-2 region, session pooler |
| Custom domain | `https://resume.sarshijkarn.com.np` | Cloudflare Redirect Rule -> HF Spaces |
| Session secret | Hugging Face Secrets | `SESSION_SECRET` env var |
| SBERT model | Pre-baked in Docker image | No runtime download |
| spaCy model | Pre-downloaded at Docker build | `RUN python -m spacy download en_core_web_md` |

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# System dependencies: Tesseract OCR + Poppler + build tools
RUN apt-get update && apt-get install -y \
    tesseract-ocr poppler-utils libgl1 libglib2.0-0 gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model at build time (baked into image)
RUN python -m spacy download en_core_web_md --quiet

# Pre-download SBERT model at build time (avoids startup delay)
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('all-MiniLM-L6-v2')"

RUN mkdir -p logs scratch

COPY . .

ENV POSTGRES_HOST=localhost
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=resume_screener
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=

# Hugging Face Spaces requires port 7860
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### Session Cookie for Hugging Face Spaces (iframe fix)

```python
SessionMiddleware(
    app,
    secret_key=SESSION_SECRET,
    max_age=3600,       # 1 hour session
    same_site="none",   # Required for cross-origin iframe embedding
    https_only=True     # SameSite=None requires Secure flag
)
```

Without these settings, login sessions would not persist inside the HF Spaces iframe.

---

## 29. Bug Fixes & Changelog

### v3.0 — Final Defense Release (Current Production)

**New Additions:**
- LLM double-check layer (Groq Llama-3.3-70B)
- `is_resume_format()` — multi-signal document validator
- Language detection via `langdetect`
- DOCX support via mammoth (+ python-docx fallback)
- OCR fallback for scanned PDFs (2-page limit optimization)
- Applicant registration portal (`/register`)
- Multi-tenant data isolation (username-scoped DB queries)
- Async batch with real-time progress bar polling
- SHAP decision explainability with contribution bars in UI
- Chart.js animated doughnut for skill gap visualization
- Batch CSV export (client-side generation)
- Analytics metrics CSV export (`/api/export/analytics`)
- Per-user history view + delete
- `skill_experience_alignment` as 17th feature
- Dynamic taxonomy SBERT fallback (unknown skill detection)
- spaCy `en_core_web_md` + custom EntityRuler
- slowapi rate limiting on all major endpoints
- robots.txt + sitemap.xml with correct MIME types
- Cloud deployment: Docker + Hugging Face + Cloudflare + Supabase

### v2.0 — Critical Bug Fix Release

17 bugs identified and resolved:

| # | Bug | Root Cause | Fix Applied |
|---|-----|-----------|------------|
| 1 | Skills not displaying | JS read `skills.matched_skills` (wrong key) | Fixed to `skills.matched` |
| 2 | Validation features not showing | JS read `data.validation_features` | Fixed to `data.validation` |
| 3 | Resume preview blank | JS read `data.resume_text` | Fixed to `data.resume_preview` |
| 4 | Experience relevance always 0% | No baseline for context-matched candidates | Added baseline scaling |
| 5 | Semantic similarity near-zero for short JDs | Poor SBERT embeddings < 15 words | Short-JD blending with token overlap |
| 6 | Skills not recognized (HTML, CSS, PHP) | Taxonomy had only ~60 skills | Expanded to 200+ in taxonomy.json |
| 7 | `_extract_required_years` matching "React 18" = 18 years | Regex matched any number | Constrained to year/experience keywords |
| 8 | Keyword stuffing score inflated | Common stopwords counted | Added 100-word stopword filter |
| 9 | `has_previous_job` rarely triggered | Depended on newline after date range | Added 4-strategy detection |
| 10 | Overlapping jobs not detected | Only counted if > 2 ranges existed | Changed to actual date-range overlap check |
| 11 | `skill_density` inconsistent for 0-experience | Word-count path used different scale | Normalized both paths equivalently |
| 12 | SQLite -> PostgreSQL migration | SQLite limited multi-user deployment | Full async PostgreSQL migration |
| 13 | Batch results memory leak | Old batch_jobs dict entries never cleared | TTL cleanup coroutine (30 min, every 5 min) |
| 14 | One corrupt file stalls batch | No per-file timeout | `asyncio.wait_for(timeout=60)` per file |
| 15 | Batch exceptions not handled | Raw exception propagated | `gather(return_exceptions=True)` + error dict |
| 16 | Jinja2 TemplateResponse crash | Wrong argument order | Fixed positional vs. keyword args |
| 17 | Batch results not saved to DB | Only single-resume endpoint saved | Added DB persistence for batch results |

### v1.0 — Initial Release

- Basic FastAPI server with 3 HTML pages
- Decision Tree Classifier (sklearn) — baseline accuracy ~0.73
- 12 validation features
- PDF + TXT parsing only
- SQLite database

### Code Backups & Reversions
During updates to add database-less crash resilience (graceful degradation), original copies of critical files were preserved as backups. If you ever need to revert to the original strict database implementation, you can find them here:
- `app/main.py.bak(prod)` (Backup for the FastAPI main application)
- `app/models/database.py.bak(prod)` (Backup for the database connection layer)

To restore the previous behavior, simply delete the current `.py` files and rename these `.bak(prod)` files to `.py`.

---

## 30. Future Improvements

| Priority | Improvement | Rationale |
|----------|------------|----------|
| High | **Improve Suspicious recall (currently 0.749)** | Collect more labeled borderline resumes; try SMOTE oversampling |
| High | **ATS compatibility score** | Industry-standard keyword match percentage |
| Medium | **PDF/DOCX report export** | Generate formatted screening reports for HR managers |
| Medium | **Resume ranking score (continuous)** | Sort candidates by numerical score |
| Medium | **Email notifications** | Send batch screening summaries to HR email |
| Medium | **Real-time WebSocket progress** | Replace 2-second polling for batch progress |
| Low | **Multi-language UI** | Internationalization for non-English HR teams |
| Low | **Candidate comparison view** | Side-by-side comparison of two candidates |
| Low | **More LLM providers** | Wire OpenAI GPT-4 and Anthropic Claude |
| Research | **Fine-tuned SBERT** | Fine-tune `all-MiniLM-L6-v2` on domain-specific resume-JD pairs |
| Research | **LLM-generated features** | Use Groq to extract structured features |

---

## 31. Credits

```
+==================================================================+
|                                                                  |
|     ClearHire - AI-Powered Resume Screening System              |
|     SBERT-Based Resume Screening & Authenticity Validation       |
|     Using XGBoost Classification                                 |
|                                                                  |
|                                            |
|     Minor NCE Project - National College of Engineering          |
|                                                                  |
|     Live:      https://resume.sarshijkarn.com.np                |
|     Server:    http://localhost:8000  (run.bat)                 |
|     HR Login:  admin / hr2026                                   |
|     Applicant: applicant / apply2026                             |
|                                                                  |
+==================================================================+

Technology Stack:
  FastAPI | Uvicorn | Python 3.10
  Sentence-BERT (all-MiniLM-L6-v2, 384-dim)
  XGBoost (87.375% accuracy, 87.22% F1)
  SHAP (native XGBoost pred_contribs)
  spaCy en_core_web_md + custom EntityRuler
  PostgreSQL (Supabase) | SQLAlchemy async | asyncpg
  pdfplumber | mammoth | pytesseract | pdf2image
  Groq Llama-3.3-70B (optional LLM verification)
  slowapi | python-dotenv | itsdangerous
  Jinja2 | Vanilla CSS | JavaScript | Chart.js 4.4
  Docker | Hugging Face Spaces | Cloudflare | Supabase

Project Status:
  Development Complete
  Production Deployed
  152\+ Tests Passing
  Ready for Final Defense Panel
```

---

*README generated from a complete source-code audit of every module, endpoint, feature, and
deployment configuration in the ClearHire project. All metrics are taken directly from
`data/processed/metrics.json` and reflect actual trained-model performance.*

*Test accuracy: **0.87375** | Weighted F1: **0.87219** | Dataset: 4,000 tech resumes*
*Server: `http://localhost:8000` | Start: `run.bat` | Live: `https://resume.sarshijkarn.com.np`*

---

> **Built by SARSHIJ KARN**
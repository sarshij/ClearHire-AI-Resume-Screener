# Key Formulas, Short Forms, and Critical Terms in ClearHire Resume Screener

This document contains the most important technical terms, formulas, and concepts specific to the ClearHire resume screening system that may be difficult to understand for individuals without technical background.

## Key Formulas

### 1. Final Match Score Formula
```
final_match_score = 0.60 × semantic_similarity
                  + 0.25 × skill_overlap_score
                  + 0.15 × experience_relevance_score
```
**Purpose**: Combines three scoring dimensions into a single score for candidate evaluation
**Source**: Section 7 (Hybrid Candidate Scoring)

### 2. Jaccard Similarity (Skill Overlap Score)
```
Jaccard = |A ∩ B| / |A ∪ B|
```
Where:
- A = set of skills found in resume
- B = set of skills found in job description
**Purpose**: Measures similarity between resume and job description skills
**Source**: Section 6 (Resume Screening Method)

### 3. Cosine Similarity (SBERT)
```
cosine_similarity = dot product of normalized embeddings
```
**Purpose**: Measures semantic similarity between resume and job description
**Source**: Section 6 (Resume Screening Method)

### 4. Experience Graduation Gap
```
gap = (current_year - graduation_year) - years_experience
```
**Purpose**: Detects chronological inconsistencies in resumes
**Source**: Section 8 (Feature 7)

### 5. Skill Density
```
skill_density = number_of_skills / years_of_experience
```
**Purpose**: Identifies potential keyword stuffing (unrealistically high skill counts)
**Source**: Section 8 (Feature 8)

### 6. Keyword Stuffing Score (with stopword filtering)
```
ratio = (JD keyword hits in resume) / (total resume words after stopword removal)
keyword_stuffing_score = min(ratio × 2.0 + repeat_penalty, 1.0)
where repeat_penalty = min(0.3, max_repeat × 0.02) for max_repeat > 10, else 0
and max_repeat = maximum frequency of any JD keyword in the resume
```
**Purpose**: Detects resumes that overly mimic job description keywords, with additional penalty for excessive repetition of specific keywords
**Source**: Section 8 (Feature 12, Bug 8 fix)

### 7. Achievement Count Regex Patterns
Patterns used to detect quantifiable achievements:
- `\b\d+%\b` - Percentage increases (e.g., "increased by 50%")
- `\b\d+x\b` - Multiplier improvements (e.g., "improved 3x")
- `\$\s*\d+[kKmMbB]?\b` - Monetary values (e.g., "$500K", "$1.5M")
- Action verbs: increased, reduced, improved, generated, led, managed, created, developed
**Source**: Section 8 (Feature 9)

### 8. Short Job Description Blending (for JD < 15 words)
```
blended_score = (sbert_weight × sbert_similarity) + ((1 - sbert_weight) × token_overlap_score)
where sbert_weight = min(0.85, 0.3 + jd_word_count × 0.04)
```
**Purpose**: Improves accuracy for very short job descriptions
**Source**: Section 6 (Semantic Similarity Computation)

### 9. Classification Threshold Logic
```
if auth_probability >= 0.80:
    classification = "Authentic"
elif auth_probability >= 0.50:
    classification = "Suspicious" 
else:
    classification = "Potentially Fake"
```
**Purpose**: Post-processing to reduce false accusations
**Source**: Section 9 (Classification Threshold Logic)

### 10. Overlapping Jobs Detection
```
for each pair of date ranges (s1,e1) and (s2,e2):
    if s1 < e2 and s2 < e1:
        overlaps += 1
```
**Purpose**: Detects simultaneous employment (red flag for fabricated resumes)
**Source**: Section 8 (Feature 5)

## Critical Short Forms & Acronyms

| Term | Meaning | Context in ClearHire |
|------|---------|----------------------|
| SBERT | Sentence-BERT | Core NLP model for semantic similarity (`all-MiniLM-L6-v2`) |
| XGBoost | Extreme Gradient Boosting | Primary classification model (87.375% accuracy) |
| SHAP | SHapley Additive exPlanations | Explainability method showing feature contributions |
| NER | Named Entity Recognition | spaCy-based entity extraction (skills, education, job titles) |
| OCR | Optical Character Recognition | Fallback for scanned PDFs (pytesseract + pdf2image) |
| JD | Job Description | Input for resume matching analysis |
| HR | Human Resources | Target user role for the system |
| AI | Artificial Intelligence | Optional LLM verification layer (Groq Llama-3.3-70B) |
| EDA | Exploratory Data Analysis | Initial phase of model development |
| CV | Cross-Validation | Used in model tuning (5-fold) |
| F1 Score | F1-Score | Primary metric for model evaluation (weighted F1: 87.22%) |
| TP/FP/TN/FN | True/False Positives/Negatives | Used in confusion matrix analysis |
| AUC | Area Under Curve | ROC curve analysis metric |
| UUID | Universally Unique Identifier | Batch job tracking IDs |
| API | Application Programming Interface | REST endpoints for prediction (`/api/predict`) |
| REST | Representational State Transfer | Architectural style for ClearHire API |
| JWT | JSON Web Token | Session authentication mechanism |
| GDPR | General Data Protection Regulation | Data privacy compliance consideration |
| CI/CD | Continuous Integration/Deployment | Automated testing and deployment pipeline |
| ORM | Object-Relational Mapping | SQLAlchemy async ORM for PostgreSQL |
| DDL/DML | Data Definition/Manipulation Language | SQL schema operations |
| VCS | Version Control System | Git for source code management |
| Docker | Containerization platform | Deployment environment |
| Kubernetes | Orchestration system | Container management (implied for scaling) |
| SVM | Support Vector Machine | Alternative algorithm considered (not selected) |
| TF-IDF | Term Frequency-Inverse Document Frequency | Baseline NLP approach (rejected for SBERT) |
| LIME | Local Interpretable Model-agnostic Explanations | Alternative explainability (not used - SHAP preferred) |
| RoBERTa | Robustly Optimized BERT Pretraining Approach | Alternative to SBERT (not selected) |
| BERT-base | Base BERT model | Larger alternative to SBERT (not selected) |
| Precision | TP/(TP+FP) | Classification metric by class |
| Recall | TP/(TP+FN) | Classification metric by class |
| Macro Avg | Unweighted mean of per-class metrics | Overall performance measure |
| Weighted Avg | Support-weighted mean of per-class metrics | Primary reported metric |

## Critical Technical Concepts

### 1. 17-Feature Validation Engine
The core authenticity detection system uses exactly 17 engineered features:
1. semantic_similarity (SBERT cosine similarity)
2. skill_overlap_score (Jaccard similarity)
3. experience_relevance_score (job category alignment)
4. final_match_score (weighted composite of above three)
5. overlapping_jobs (simultaneous employment detection)
6. promotion_speed (title changes per year experience)
7. experience_graduation_gap (chronological consistency)
8. skill_density (skills per year experience)
9. achievement_count (quantifiable results count)
10. generic_phrase_score (buzzword density)
11. gap_years (unexplained employment gaps)
12. keyword_stuffing_score (JD keyword density with stopwords)
13. years_experience (total professional experience)
14. num_certifications (certification count)
15. num_skills (distinct skill count)
16. education_level_encoded (ordinal education level)
17. has_previous_job (binary work history flag)

### 2. Model Training Approach
- Dataset: 4,000 synthetic tech resumes (`resume_dataset_4000_tech.csv`)
- Class Distribution: Authentic (48.25%), Suspicious (32.40%), Potentially Fake (19.35%)
- Train/Test Split: 80%/20% stratified (3,200 train, 800 test)
- Algorithm: XGBoost with hyperparameters:
  - learning_rate: 0.2
  - max_depth: 5
  - n_estimators: 50
  - subsample: 0.8
- Class Balancing: Used during Decision Tree baseline training
- Feature Engineering: 5 additional features from raw data (total 17)

### 3. System Architecture Components
- **Backend**: FastAPI + Uvicorn (ASGI server)
- **Database**: PostgreSQL (Supabase cloud) with SQLAlchemy async ORM
- **ML/NLP**: 
  - SBERT `all-MiniLM-L6-v2` (384-dim embeddings)
  - XGBoost classifier
  - spaCy `en_core_web_md` + custom EntityRuler
  - SHAP explainability (native XGBoost pred_contribs)
- **Document Processing**:
  - pdfplumber (layout-aware PDF parsing)
  - mammoth (DOCX text extraction)
  - pytesseract + pdf2image (OCR fallback for scanned PDFs)
- **Frontend**: Jinja2 templates + Vanilla CSS + JavaScript + Chart.js 4.4
- **Authentication**: SHA-256 hashed passwords + signed session cookies
- **Rate Limiting**: slowapi (25/100/10 req/min for different endpoints)
- **LLM Layer**: Groq Llama-3.3-70B (optional second-opinion)
- **Deployment**: Docker + Hugging Face Spaces + Cloudflare + Supabase

### 4. Performance Metrics
- Test Accuracy: 87.375%
- Weighted F1-Score: 87.22%
- Per-Class F1-Scores:
  - Authentic: 88.94%
  - Suspicious: 79.35%
  - Potentially Fake: 96.08%
- Top 5 Features by Importance:
  1. skill_overlap_score (20.23%)
  2. final_match_score (17.10%)
  3. generic_phrase_score (15.24%)
  4. keyword_stuffing_score (7.43%)
  5. skill_density (7.03%)

### 5. Processing Pipeline
1. Document Upload → MIME validation → Text extraction (PDF/DOCX/TXT)
2. Language Detection → Resume Format Validation (≥45 score threshold)
3. Feature Extraction:
   - Semantic: SBERT embeddings + cosine similarity
   - Skills: Taxonomy + Jaccard similarity
   - Experience: Date-range parsing + relevance scoring
   - Validation: All 17 authenticity features
4. Classification: XGBoost prediction + SHAP explainability
5. (Optional) LLM Verification: Groq Llama-3.3-70B second opinion
6. Result Storage: PostgreSQL + JSON response return

## Color Coding System

| Classification | Badge Color | Hex Code | Psychological Meaning |
|----------------|-------------|----------|----------------------|
| Authentic | Green | `#059669` | Safety, verified, approved |
| Suspicious | Amber | `#d97706` | Caution, needs review |
| Potentially Fake | Red | `#dc2626` | Danger, reject, fraud alert |
| Not a Resume | Gray | `#6b7280` | Neutral, informational |

SHAP Visualization:
- Positive Contribution (→ Authentic): Green bar
- Negative Contribution (→ Fake): Red bar

Match Score Interpretation:
- Strong Match (≥70%): Green
- Moderate Match (35-69%): Amber
- Weak Match (<35%): Red

This document summarizes the key technical elements that would be most challenging for non-technical audience members to understand during a final defense presentation.
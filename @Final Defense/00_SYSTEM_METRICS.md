# ClearHire System Metrics Reference

This file contains all key performance metrics, dataset characteristics, and system specifications for the ClearHire Resume Screener system.

## 📊 Overall Performance Metrics
- **Test Accuracy**: 87.375% (0.87375)
- **Weighted F1-Score**: 87.22% (0.8721886308804665)
- **Macro F1**: 88.12% (0.8812)
- **Macro Precision**: 89.05% (0.8905)
- **Macro Recall**: 87.50% (0.8750)

## 📈 Dataset Characteristics
- **Total Samples**: 4,000 resumes
- **Initial Features**: 35 columns
- **Final Features Used**: 17 engineered features
- **Class Distribution**:
  - Authentic: 1,930 samples (48.25%)
  - Suspicious: 1,296 samples (32.40%)
  - Potentially Fake: 774 samples (19.35%)

## 🔀 Train/Test Split
- **Training Set**: 3,200 samples (80%)
  - Authentic: 1,544 (48.25%)
  - Suspicious: 1,037 (32.40%)
  - Potentially Fake: 619 (19.35%)
- **Test Set**: 800 samples (20%)
  - Authentic: 386 (48.25%)
  - Suspicious: 259 (32.40%)
  - Potentially Fake: 155 (19.35%)
- **Method**: Stratified split with random_state=42

## 🏆 Feature Importance Ranking (Top 5 = 67.0% of decision power)
| Rank | Feature | Importance Value | Percentage |
|------|---------|------------------|------------|
| 1 | skill_overlap_score | 0.20231124758720398 | 20.23% |
| 2 | final_match_score | 0.1709515005350113 | 17.10% |
| 3 | generic_phrase_score | 0.15243767201900482 | 15.24% |
| 4 | keyword_stuffing_score | 0.07432091981172562 | 7.43% |
| 5 | skill_density | 0.07033894956111908 | 7.03% |
| 6 | semantic_similarity | 0.057022202759981155 | 5.70% |
| 7 | promotion_speed | 0.05491243302822113 | 5.49% |
| 8 | experience_relevance_score | 0.03554640710353851 | 3.55% |
| 9 | overlapping_jobs | 0.03524557873606682 | 3.52% |
| 10 | achievement_count | 0.026128023862838745 | 2.61% |
| 11 | experience_graduation_gap | 0.02383802831172943 | 2.38% |
| 12 | gap_years | 0.02080131694674492 | 2.08% |
| 13 | education_level_encoded | 0.017836682498455048 | 1.78% |
| 14 | num_skills | 0.017330002039670944 | 1.73% |
| 15 | num_certifications | 0.01527572050690651 | 1.53% |
| 16 | years_experience | 0.014075366780161858 | 1.41% |
| 17 | has_previous_job | 0.011627841740846634 | 1.16% |
| — | skill_experience_alignment | 0.0 | 0.00% (no-op) |
| — | ai_plausibility_score | 0.0 | 0.00% (no-op) |

## 📋 Per-Class Classification Report (Test Set: 800 samples)

### Authentic Class
- **Precision**: 85.44% (0.8544152744630071)
- **Recall**: 92.75% (0.927461139896373)
- **F1-Score**: 88.94% (0.8894409937888199)
- **Support**: 386 samples

### Suspicious Class
- **Precision**: 84.35% (0.8434782608695652)
- **Recall**: 74.90% (0.749034749034749)
- **F1-Score**: 79.35% (0.7934560327198364)
- **Support**: 259 samples

### Potentially Fake Class
- **Precision**: 97.35% (0.9735099337748344)
- **Recall**: 94.84% (0.9483870967741935)
- **F1-Score**: 96.08% (0.9607843137254902)
- **Support**: 155 samples

### Averages
- **Macro Avg**: Precision 89.05%, Recall 87.50%, F1 88.12%
- **Weighted Avg**: Precision 87.39%, Recall 87.38%, F1 87.22%

## 🎯 Confusion Matrix (Actual Values)
```
                  Predicted
               Auth.  Susp.  Fake
Actual Auth.    358     24     4     (386 total)
       Susp.     56    194     9     (259 total)
       Fake        4     4   147     (155 total)
```

### Error Analysis:
- **Authentic misclassified**: 24 as Suspicious, 4 as Fake (7.25% error rate)
- **Suspicious misclassified**: 56 as Authentic, 9 as Fake (25.1% error rate)  
- **Fake misclassified**: 4 as Authentic, 4 as Suspicious (5.2% error rate)
- Model shows conservative bias: prefers to call things Suspicious rather than Fake when uncertain

## ⚙️ Model Hyperparameters (Production XGBoost)
```json
{
  "learning_rate": 0.2,
  "max_depth": 5,
  "n_estimators": 50,
  "subsample": 0.8
}
```

## 📝 Feature Columns Used in Model
1. semantic_similarity
2. skill_overlap_score  
3. experience_relevance_score
4. final_match_score
5. overlapping_jobs
6. promotion_speed
7. experience_graduation_gap
8. skill_density
9. achievement_count
10. generic_phrase_score
11. gap_years
12. keyword_stuffing_score
13. years_experience
14. num_certifications
15. num_skills
16. education_level_encoded
17. has_previous_job
18. skill_experience_alignment (engineered but 0 importance)
19. ai_plausibility_score (engineered but 0 importance - placeholder in DB)

## 🔬 Key Formulas
### Final Match Score
```
final_match_score = 0.60 × semantic_similarity
                  + 0.25 × skill_overlap_score
                  + 0.15 × experience_relevance_score
```

### Experience Graduation Gap
```
gap = (current_year - graduation_year) - years_experience
```

### Skill Density
```
skill_density = number_of_skills / years_of_experience
```

### Keyword Stuffing Score (with Bug 8 fix)
```
ratio = (JD keyword hits in resume) / (total resume words after stopword removal)
repeat_penalty = min(0.3, max_repeat × 0.02) for max_repeat > 10, else 0
keyword_stuffing_score = min(ratio × 2.0 + repeat_penalty, 1.0)
```

### Short JD Blending (for JD < 15 words)
```
blended_score = (sbert_weight × sbert_similarity) + ((1 - sbert_weight) × token_overlap_score)
where sbert_weight = min(0.85, 0.3 + jd_word_count × 0.04)
```

## 🏷️ Classification Threshold Logic
```
if auth_probability >= 0.80:
    classification = "Authentic"
elif auth_probability >= 0.50:
    classification = "Suspicious" 
else:
    classification = "Potentially Fake"
```

## 📊 EDA Artifacts Generated
- class_distribution.png
- confusion_matrix.png  
- correlation_matrix.png
- feature_distributions.png
- feature_importance.png
- decision_tree.png

## 💻 System Specifications
### Core Technologies
- **Backend**: Python 3.10 + FastAPI + Uvicorn (ASGI)
- **ML/NLP**: 
  - SBERT `all-MiniLM-L6-v2` (384-dim embeddings)
  - XGBoost classifier
  - spaCy `en_core_web_md` + custom EntityRuler
  - SHAP explainability
- **Database**: PostgreSQL (Supabase cloud) with SQLAlchemy async ORM
- **Document Processing**:
  - pdfplumber (layout-aware PDF parsing)
  - mammoth (DOCX text extraction)
  - pytesseract + pdf2image (OCR fallback)
- **Frontend**: Jinja2 templates + Vanilla CSS + JavaScript + Chart.js 4.4
- **Authentication**: SHA-256 hashed passwords + signed session cookies
- **Rate Limiting**: slowapi (25/100/10 req/min for different endpoints)
- **LLM Layer**: Groq Llama-3.3-70B (optional second-opinion)
- **Deployment**: Docker + Hugging Face Spaces + Cloudflare + Supabase

### Performance Characteristics
- **End-to-End Latency**:
  - Best Case (GPU + cached JD): <500ms
  - Typical Case (CPU + uncached): 1-2 seconds
  - Worst Case (OCR + no GPU): 3-5 seconds
  - LLM Verification Add: +1-3 seconds (when used)
- **Throughput Capacity**:
  - Single Predictions: ~20-30/min/core (SBERT-bound)
  - Batch Processing: ~50-100 resumes/sec (DB-write-bound)
- **Resource Usage**:
  - Memory: ~360MB base + overhead per worker
  - CPU: SBERT Inference is primary bottleneck (parallelized)
  - Storage: Model files ~200MB, Database grows with usage

## 📋 Key System Files
- **Main Entrypoint**: `app/main.py`
- **Validation Features**: `app/features/validation.py` (all 17 features)
- **Model Wrapper**: `app/models/classifier.py` (XGBoost + SHAP)
- **SBERT Implementation**: `app/models/embedder.py`
- **Formulas Reference**: `Formulas.md`
- **Performance Metrics**: `data/processed/metrics.json` (source of above data)
- **Feature Importance**: `data/processed/feature_importance.png`
- **Confusion Matrix**: `data/processed/confusion_matrix.png`

---
*Metrics sourced from: data/processed/metrics.json and model evaluation*
*Last Updated: 2026-08-26*
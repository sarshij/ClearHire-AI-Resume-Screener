# ClearHire — Quick Reference & Defense Notes

A concise, at-a-glance summary of the entire project for final defense preparation.

---

## 🔗 Live Links
| Resource | URL |
|---|---|
| **Live App** | https://sarshijkarn-resume-screener.hf.space |
| **Custom Domain** | https://resume.sarshijkarn.com.np/ (Cloudflare redirect) |
| **GitHub Repo** | https://github.com/sarshij/ClearHire-AI-Resume-Screener |
| **Supabase DB** | ap-northeast-2 region (PostgreSQL) |

---

## 🧠 ML Pipeline (What the Examiner Will Ask)

### Scoring Formula (Matching Phase)
```
Final Match Score = 0.60 × Semantic Similarity (SBERT)
                  + 0.25 × Skill Overlap (Jaccard)
                  + 0.15 × Experience Relevance
```

### Classification Thresholds (XGBoost output)
| Auth Probability | Label |
|---|---|
| ≥ 0.80 | ✅ Authentic |
| 0.50 – 0.79 | ⚠️ Suspicious |
| < 0.50 | ❌ Potentially Fake |

### Model Performance
- **Test Accuracy:** 87.4% (on 800 held-out test samples from 4,000 total)
- **Weighted F1:** 87.2%
- **Per-class F1:** Authentic 88.9% | Suspicious 79.3% | Potentially Fake 96.1%
- **Best Params:** `learning_rate=0.2, max_depth=5, n_estimators=50, subsample=0.8`

---

## 📐 The 17 Validation Features

> **Note:** The original training notebook had 19 columns in `metrics.json` (`has_previous_job` + `ai_plausibility_score` included). After training, both showed **0.0 feature importance** in XGBoost and were removed from inference. The live system uses exactly **17 features** at prediction time. This is consistent across all code.

| # | Feature | What it Measures |
|---|---|---|
| 1 | `semantic_similarity` | SBERT cosine similarity between resume and JD |
| 2 | `skill_overlap_score` | Jaccard similarity of extracted skill sets |
| 3 | `experience_relevance_score` | Resume experience vs. target job role |
| 4 | `final_match_score` | Composite weighted score (above formula) |
| 5 | `overlapping_jobs` | Count of overlapping job date ranges (fabrication signal) |
| 6 | `promotion_speed` | Promotions / years worked (exaggeration signal) |
| 7 | `experience_graduation_gap` | Years since graduation vs. claimed experience |
| 8 | `skill_density` | Skills per year of experience (or per 150 words) |
| 9 | `achievement_count` | Quantified achievements + action verbs |
| 10 | `generic_phrase_score` | Cliché phrases like "team player", "hardworking" |
| 11 | `gap_years` | Total unexplained employment gap years |
| 12 | `keyword_stuffing_score` | Ratio of JD keywords in resume (stopword-filtered) |
| 13 | `years_experience` | Extracted years of total work experience |
| 14 | `num_certifications` | Count of professional certifications detected |
| 15 | `num_skills` | Total skills extracted from the resume |
| 16 | `education_level_encoded` | PhD=3, Master=2, Bachelor=1, Diploma=0 |
| 17 | `skill_experience_alignment` | Skills backed by action verbs in experience sections |

---

## 🏗️ Architecture Summary

```
User → FastAPI (Docker, HF Spaces)
         ├── Auth: SHA-256 hashed passwords, Starlette SessionMiddleware
         ├── SBERT (multilingual-MiniLM-L12-v2) → Semantic Similarity
         ├── spaCy (en_core_web_md) → NER, Job Title & Education extraction
         ├── 17-feature Validation Pipeline → XGBoost (xgboost_model.pkl)
         ├── SHAP Explainability → Top 3 features per prediction
         ├── Groq/LLaMA-3.3-70B → Double-check for Suspicious/Fake verdicts
         └── Supabase PostgreSQL → Persistent multi-tenant scan history
```

---

## 🚀 Deployment Stack
| Layer | Technology | Detail |
|---|---|---|
| **Container** | Docker | `python:3.10-slim` + tesseract, poppler, libgl1 |
| **Host** | Hugging Face Spaces | Port 7860, Docker runtime |
| **Database** | Supabase PostgreSQL | Session-mode pooler (port 5432), `asyncpg` |
| **Domain** | Cloudflare Redirect | `resume.sarshijkarn.com.np` → HF Space |
| **Rate Limiting** | SlowAPI | 25/min single scan, 100/min batch |

---

## ⚠️ Known Limitations (Say This Confidently in Defense)

### 1. Session Secret Resets on Restart
**What it means:** The session cookie secret key is generated fresh every time the server starts:
```python
SESSION_SECRET = secrets.token_hex(32)  # New key each restart
```
**Why it matters:** Every time Hugging Face restarts the Docker container (daily, or on new deploys), all currently logged-in users are automatically logged out. Their **data is not lost** (it's in Supabase), but they need to log in again.

**Why it's acceptable for demo:** This is a well-known trade-off for stateless container deployments. The fix in production would be to store the secret in an environment variable (e.g., a Hugging Face Secret), so it persists across restarts. For a defense demo with a single session, this is a non-issue.

### 2. Supabase Free Tier Limits
- Max 500MB storage, 2 active connections via pooler.
- Sufficient for demo; would need upgrading at scale.

### 3. HF Free Tier — Container Sleeps After Inactivity
- After ~15 minutes of no traffic, the Space sleeps. First request after wakeup takes ~30-60s to cold-start all models (SBERT, spaCy, XGBoost).
- **Fix:** The models are pre-warmed in the `lifespan` startup event, so once awake, they're fast.

---

## ✅ Defense Readiness Checklist
- [x] Live app accessible at custom domain
- [x] HR multi-tenancy isolation working
- [x] Batch screening persists to database
- [x] SHAP explainability shown per scan
- [x] LLM double-check layer active
- [x] Favicon on all pages
- [x] All "19 feature" references corrected to 17 across README.md, Defense.md
- [x] GitHub remote URL updated to `ClearHire-AI-Resume-Screener`
- [x] Supabase connected and schema migrated

---

*Built by SARSHIJ KARN*

# The 17 Validation Features of ClearHire

These features form the input to the XGBoost classifier for authenticity prediction.

## Features List (in order of importance)

### 1. skill_overlap_score (20.23% importance)
- **What it is**: Jaccard similarity between resume skills and job description skills
- **Formula**: |A ∩ B| / |A ∪ B| where A=resume skills, B=JD skills
- **Purpose**: Measures skill match between candidate and job requirements
- **High score**: Good skill match
- **Low score**: Poor skill match

### 2. final_match_score (17.10% importance)
- **What it is**: Weighted composite of three scoring dimensions
- **Formula**: 0.60 × semantic_similarity + 0.25 × skill_overlap_score + 0.15 × experience_relevance_score
- **Purpose**: Overall candidate suitability score
- **Range**: 0-1 (higher is better)

### 3. generic_phrase_score (15.24% importance)
- **What it is**: Density of buzzword/filler phrases in resume
- **Detection**: Exact phrase matching against 50+ generic phrases (results-driven, team player, etc.)
- **Purpose**: Identifies low-quality or fabricated resumes (high buzzword, low substance)
- **High score**: Likely fake/exaggerated resume
- **Low score**: More concrete, specific content

### 4. keyword_stuffing_score (7.43% importance)
- **What it is**: Measures resume "stuffing" with JD keywords
- **Formula**: min(ratio × 2.0 + repeat_penalty, 1.0)
  - ratio = (JD keyword hits in resume) / (total resume words after stopword removal)
  - repeat_penalty = min(0.3, max_repeat × 0.02) for max_repeat > 10, else 0
  - max_repeat = maximum frequency of any JD keyword in resume
- **Bug 8 Fix**: Stopwords filtered before computing ratio
- **Purpose**: Detects resumes that overly mimic JD (paste JD throughout)
- **High score**: Potential keyword stuffing
- **Low score**: Natural skill distribution

### 5. skill_density (7.03% importance)
- **What it is**: Skills per year of experience
- **Formula**: number_of_skills / years_of_experience
- **Purpose**: Identifies unrealistic skill counts (keyword stuffing)
- **High score**: Potential exaggeration (too many skills for experience)
- **Low score**: May indicate insufficient skill development

### 6. semantic_similarity (5.70% importance)
- **What it is**: SBERT cosine similarity between resume and JD embeddings
- **Model**: all-MiniLM-L6-v2 (384-dimensional)
- **Purpose**: Holistic semantic alignment understanding
- **Range**: 0-1 (higher = more semantically similar)
- **Note**: Uses layout-aware pdfplumber for better column handling

### 7. promotion_speed (5.49% importance)
- **What it is**: Title progression speed (promotions per year experience)
- **Detection**: Counts title keywords (senior, lead, manager, etc.) / unique years
- **Purpose**: Flags unusually fast career progression (exaggeration signal)
- **High score**: Rapid promotions (potential red flag)
- **Low score**: Normal or slow progression

### 8. experience_relevance_score (3.55% importance)
- **What it is**: Work history relevance to target job category
- **Method**: Keyword overlap between JD tokens and resume job titles
- **Purpose**: Measures if candidate's background fits the role
- **High score**: Relevant experience
- **Low score**: Irrelevant or mismatched experience

### 9. overlapping_jobs (3.52% importance)
- **What iti s**: Count of simultaneous employment periods
- **Detection**: Parses date ranges, checks for actual overlaps (s1 < e2 AND s2 < e1)
- **Bug 10 Fix**: Now checks actual date overlap, not just count of ranges
- **Purpose**: Detects impossible simultaneous full-time jobs
- **High score**: Likely fabricated resume
- **Low score**: Normal sequential employment

### 10. achievement_count (2.61% importance)
- **What it is**: Count of quantifiable achievements and action verbs
- **Patterns**: 
  - % increase: \b\d+%\b
  - Multiplier: \b\d+x\b
  - Monetary: \$\s*\d+[kKmMbB]?\b
  - Action verbs: increased, reduced, improved, generated, led, managed, etc.
- **Purpose**: Measures concrete, evidence-based experience
- **High score**: Strong quantifiable achievements (genuine resume)
- **Low score**: Vague, non-quantified claims (potential fake)

### 11. experience_graduation_gap (2.38% importance)
- **What it is**: Chronological consistency check
- **Formula**: gap = (current_year - graduation_year) - years_experience
- **Purpose**: Detects fabricated experience/education dates
- **Interpretation**:
  - Large positive: Claims more experience than possible since graduation
  - Large negative: Claims experience before graduation
  - Near zero: Chronologically consistent
- **Typical range**: -2 to +2 years (accounting for internships, etc.)

### 12. gap_years (2.08% importance)
- **What it is**: Unexplained employment gap detection
- **Detection**: Finds all years mentioned, measures intervals > 2 years
- **Purpose**: Identifies suspicious unemployment periods
- **High score**: Multiple/long unexplained gaps
- **Low score**: Minimal or explained gaps

### 13. education_level_encoded (1.78% importance)
- **What it is**: Ordinal education level
- **Mapping**:
  - 0: Diploma/High School/Unknown
  - 1: Bachelor's
  - 2: Master's
  - 3: PhD/Doctorate
- **Purpose**: Educational qualification signal
- **Note**: Extracted via spaCy NER + keyword matching

### 14. num_skills (1.73% importance)
- **What it is**: Count of distinct skills identified
- **Sources**: 
  - SKILL_KEYWORDS taxonomy (200+ skills)
  - Dynamic SBERT-based detection for unknown terms
- **Purpose**: Broad skill set indicator
- **Note**: Capped at reasonable values in validation

### 15. num_certifications (1.53% importance)
- **What it is**: Professional certification count
- **Detection**: 26 specialized regex patterns (AWS, Azure, CISSP, PMP, etc.)
- **Purpose**: Credential verification signal
- **High score**: Many certifications (positive signal)
- **Low score**: Few or no certifications (context dependent)

### 16. years_experience (1.41% importance)
- **What it is**: Total professional experience
- **Detection**: Date-range parsing, overlap merging, "X years" pattern matching
- **Purpose**: Experience level validation
- **Capped**: At 50 years (unrealistic beyond)
- **Note**: Dynamically extracted from resume text

### 17. has_previous_job (1.16% importance)
- **What it is**: Binary work history flag
- **Detection**: 4-strategy logic (Bug 9 fix):
  1. Explicit past-tense indicators
  2. Multiple distinct date-range blocks
  3. Multiple job title keywords
  4. Multiple company name indicators
- **Bug 9 Fix**: No longer depends on newline after date ranges (PDF-safe)
- **Purpose**: Distinguishes entry-level from experienced candidates
- **Value**: 0 = no previous work, 1 = has work history

## Features Removed (0.0 importance)
- skill_experience_alignment: No predictive power in final model
- ai_plausibility_score: Not used in production (placeholder in DB)

## Feature Engineering Process
1. Start with 12 raw features from initial dataset
2. Engineer 5 additional features:
   - years_experience
   - num_certifications
   - num_skills
   - education_level_encoded
   - has_previous_job
3. Apply stratified train/test split (80/20, preserving class distribution)
4. Train XGBoost with optimized parameters
5. Validate and confirm 17-feature set optimal
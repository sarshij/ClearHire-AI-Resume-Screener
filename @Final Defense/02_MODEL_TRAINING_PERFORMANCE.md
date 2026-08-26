# Model Training and Performance Details

## Dataset Overview
- **Source**: 4,000 synthetic tech resumes (`resume_dataset_4000_tech.csv`)
- **Size**: 4,000 samples × 35 columns initially
- **Features**: 17 final features used for training
- **Target Variable**: 3-class classification
  - 0 = Authentic
  - 1 = Suspicious  
  - 2 = Potentially Fake

## Class Distribution
- **Authentic**: 1,930 samples (48.25%)
- **Suspicious**: 1,296 samples (32.40%)
- **Potentially Fake**: 774 samples (19.35%)
- **Note**: Naturally imbalanced (fake resumes are minority)

## Train/Test Split
- **Method**: Stratified train/test split
- **Ratio**: 80% training / 20% testing
- **Random State**: 42 (for reproducibility)
- **Stratification**: Preserves class distribution in both splits
- **Results**:
  - Training: 3,200 samples (1,544 Authentic, 1,037 Suspicious, 619 Fake)
  - Testing: 800 samples (386 Authentic, 259 Suspicious, 155 Fake)

## Data Preprocessing Steps
1. **Encoding**: Loaded with `encoding='latin-1'` for special character handling
2. **Label Encoding**: `{'Authentic': 0, 'Suspicious': 1, 'Potentially Fake': 2}`
3. **Missing Value Imputation**: Median fill (defensive measure - no actual missing values found)
4. **No Normalization**: XGBoost is scale-invariant; tree-based methods use ranks
5. **Feature Engineering**: 5 additional features created from raw data

## Engineered Features (from raw columns)
```python
# 1. Certifications count
df['num_certifications'] = df['certifications'].apply(
    lambda v: len([c for c in str(v).split(',') if c.strip()]) if pd.notna(v) else 0
)

# 2. Skills count  
df['num_skills'] = df['skills'].apply(
    lambda v: len([s for s in str(v).split(',') if s.strip()]) if pd.notna(v) else 0
)

# 3. Education level (ordinal)
edu_map = {"Bachelor's": 1, "Master's": 2, "PhD": 3}
df['education_level_encoded'] = df['education_level'].map(edu_map).fillna(0).astype(int)

# 4. Previous job flag
df['has_previous_job'] = df['previous_job_title'].notna().astype(int)

# 5. Years experience (calculated separately during feature extraction)
```

## Model Selection Process

### Baseline Model: Decision Tree
- **Algorithm**: DecisionTreeClassifier (sklearn)
- **Parameters**: `random_state=42, class_weight='balanced'`
- **Purpose**: Establish baseline performance
- **Result**: ~0.73 accuracy, ~0.72 weighted F1
- **Why class_weight='balanced'**: Compensates for class imbalance (Fake class only 19.35%)

### Tuned Model: GridSearchCV Decision Tree
- **Algorithm**: GridSearchCV with DecisionTreeClassifier
- **Cross-Validation**: 5-fold
- **Scoring Metric**: f1_weighted
- **Parallel Processing**: n_jobs=-1 (all CPU cores)
- **Verbose**: 1 (progress reporting)

#### Parameter Grid Explored
```python
param_grid = {
    'max_depth': [3, 5, 7, 10, 15, None],
    'min_samples_split': [2, 5, 10, 20],
    'min_samples_leaf': [1, 2, 5, 10],
    'criterion': ['gini', 'entropy'],
    'class_weight': ['balanced', None]
}
```

### Production Model: XGBoost
- **Why XGBoost**: Superior performance to tuned Decision Tree
- **Best Parameters** (from separate tuning session):
  ```python
  best_params = {
      'learning_rate': 0.2,
      'max_depth': 5,
      'n_estimators': 50,
      'subsample': 0.8
  }
  ```

#### XGBoost Parameter Rationales
- **learning_rate: 0.2**: Moderate rate balances convergence speed vs overfitting
- **max_depth: 5**: Prevents deep trees from memorizing noise in data
- **n_estimators: 50**: Sufficient boosting rounds given 17 feature count
- **subsample: 0.8**: Row subsampling (80%) reduces overfitting through randomness

## Training Procedure (notebooks/01_eda_and_model.py)
1. Load and preprocess dataset
2. Perform exploratory data analysis (EDA)
3. Split data stratified
4. Train baseline Decision Tree
5. Tune Decision Tree with GridSearchCV
6. Train final XGBoost model with optimized parameters
7. Evaluate on test set
8. Generate EDA artifacts and performance reports

## Evaluation Results (Test Set: 800 samples)

### Overall Metrics
- **Test Accuracy**: 0.87375 (87.375%)
- **Weighted F1-Score**: 0.8721886308804665 (87.22%)
- **Macro F1**: 0.8812 (88.12%)
- **Macro Precision**: 0.8905 (89.05%)
- **Macro Recall**: 0.8750 (87.50%)

### Per-Class Performance
| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Authentic | 0.8544 | 0.9275 | 0.8894 | 386 |
| Suspicious | 0.8435 | 0.7490 | 0.7935 | 259 |
| Potentially Fake | 0.9735 | 0.9484 | **0.9608** | 155 |
| Macro Avg | 0.8905 | 0.8750 | 0.8812 | 800 |
| Weighted Avg | 0.8739 | 0.8738 | 0.8722 | 800 |

### Per-Class Analysis

#### Potentially Fake (Highest F1: 0.9608)
- **Why highest**: Very distinctive patterns
  - Extremely high `generic_phrase_score` (buzzword overload)
  - Elevated `keyword_stuffing_score` (JD pasting)
  - Low `achievement_count` (lack of quantifiable results)
- **Result**: Clear boundaries easily detected by XGBoost

#### Suspicious (Lowest Recall: 0.749)
- **Challenge**: 25% misclassified as Authentic
- **Reason**: Intermediate characteristics - some real, some exaggerated
- **Improvement Area**: Primary target for model enhancement
- **Current Strategy**: LLM verification layer helps reduce false negatives

#### Authentic (Highest Recall: 0.9275)
- **Strength**: Conservative about flagging genuine resumes as fake
- **False Positive Rate**: Only 7.25% of genuine resumes incorrectly flagged
- **Benefit**: Minimizes unfair accusations of real candidates

## Confusion Matrix (Actual Values)
```
                  Predicted
               Auth.  Susp.  Fake
Actual Auth.    358     24     4     (386 total)
       Susp.     56    194     9     (259 total)
       Fake        4     4   147     (155 total)
```

### Key Insights from Confusion Matrix
- **Authentic misclassified**: 24 as Suspicious, 4 as Fake (7.25% error)
- **Suspicious misclassified**: 56 as Authentic, 9 as Fake (25.1% error)  
- **Fake misclassified**: 4 as Authentic, 4 as Suspicious (5.2% error)
- **Model is the conservative**: Prefers to call things Suspicious rather than Fake when uncertain

## Feature Importance (Top 5 = 67.0% of decision power)
1. **skill_overlap_score**: 20.23% - Single most important feature
2. **final_match_score**: 17.10% - Composite score validating approach
3. **generic_phrase_score**: 15.24% - Buzzword detection critical
4. **keyword_stuffing_score**: 7.43% - JD pasting detection
5. **skill_density**: 7.03% - Experience vs skill count realism

### Top 5 Features Account For: 67.0% of model's decision-making
### Remaining 12 Features: 33.0% (each < 6% individually)

## EDA Artifacts Generated
1. **class_distribution.png**: Bar chart of class/risk-level counts
2. **correlation_matrix.png**: 17x17 Pearson correlation heatmap
3. **feature_distributions.png**: 5x4 grid of KDE plots per class (20 subplots)
4. **confusion_matrix.png**: True vs Predicted class heatmap
5. **feature_importance.png**: Horizontal bar chart of importances
6. **decision_tree.png**: Visual tree (max_depth=4 for readability)

### Key EDA Insights
- `generic_phrase_score`: Clearest separation Authentic (low) vs Fake (high)
- `skill_overlap_score`: Highest importance (20.23%) - validates skill focus
- `final_match_score`: 2nd importance (17.10%) - confirms hybrid approach
- **Expected Correlation**: semantic_similarity ↔ final_match_score (positive)
- **Fake Resume Signatures**: high keyword_stuffing + high generic_phrase + low achievement

## Model Training Best Practices Applied
1. **Stratified Splitting**: Maintains class representation
2. **Class Weighting**: Addresses imbalance during baseline training
3. **Cross-Validation**: 5-fold CV prevents overfitting to single split
4. **Metric Selection**: f1_weighted for imbalanced multi-class
5. **Feature Engineering**: Domain knowledge creates meaningful signals
6. **Regularization**: XGBoost parameters prevent overfitting
7. **Holdout Testing**: Unseen test set for honest evaluation
8. **Reproducibility**: Fixed random seeds
9. **Artifact Generation**: Saves plots/models for documentation
10. **Interpretability**: Feature importance and SHAP for explainability

## Production Model Specifications
- **Format**: Pickle file (`data/models/xgboost_model.pkl`)
- **Wrapper**: `app/models/classifier.py` with SHAP explainability
- **Input**: 17-feature dictionary matching training columns exactly
- **Output**: Class prediction + probabilities + SHAP explanations
- **Fallback**: Heuristic classifier if model loading fails
- **Pre-warming**: Loaded during FastAPI startup lifecycle
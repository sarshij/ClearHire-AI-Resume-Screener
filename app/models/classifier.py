"""
XGBoost Classifier Wrapper
Loads the trained model from data/models/xgboost_model.pkl and runs predictions.
Integrates SHAP to provide local explainability (top 3 contributing features).
"""
import joblib
import numpy as np
import pandas as pd
import json
from pathlib import Path

from app.logger import setup_logger

logger = setup_logger(__name__)

# Path to the trained XGBoost model
MODEL_PATH = Path(__file__).parents[2] / 'data' / 'models' / 'xgboost_model.pkl'
METRICS_PATH = Path(__file__).parents[2] / 'data' / 'processed' / 'metrics.json'

_LABEL_MAP = {0: 'Authentic', 1: 'Suspicious', 2: 'Potentially Fake'}

_loaded_model = None       
_feature_names = None      
_model_meta = None

def _load_feature_names_from_metrics() -> list:
    try:
        with open(METRICS_PATH, 'r') as f:
            data = json.load(f)
        cols = data.get('feature_cols')
        if cols:
            return cols
    except Exception as e:
        logger.warning(f"Could not load feature names from metrics.json: {e}")

    # Fallback 17 features
    return [
        "semantic_similarity", "skill_overlap_score", "experience_relevance_score",
        "final_match_score", "overlapping_jobs", "promotion_speed",
        "experience_graduation_gap", "skill_density", "achievement_count",
        "generic_phrase_score", "gap_years", "keyword_stuffing_score",
        "years_experience", "num_certifications", "num_skills",
        "education_level_encoded", 
        # "has_previous_job",
        "skill_experience_alignment"
        # "ai_plausibility_score"
    ]


def _load_model_from_pkl():
    logger.info(f"Loading trained model from: {MODEL_PATH}")
    payload = joblib.load(MODEL_PATH)
    if isinstance(payload, dict):
        model = payload['model']
        feat_names = payload.get('feature_names', _load_feature_names_from_metrics())
        return model, feat_names, payload
    else:
        feat_names = _load_feature_names_from_metrics()
        return payload, feat_names, {}


def load_model():
    global _loaded_model, _feature_names, _model_meta

    if _loaded_model is not None:
        return _loaded_model, _feature_names

    try:
        _loaded_model, _feature_names, _model_meta = _load_model_from_pkl()
        return _loaded_model, _feature_names
    except Exception as e:
        logger.error(f"Failed to load XGBoost pkl ({e}). Using fallback.")

    _feature_names = _load_feature_names_from_metrics()
    _loaded_model = _HeuristicFallbackClassifier()
    _model_meta = {}
    return _loaded_model, _feature_names


class _HeuristicFallbackClassifier:
    def _classify(self, row: np.ndarray, cols: list) -> tuple:
        col_idx = {name: i for i, name in enumerate(cols)}
        match   = float(row[col_idx.get("final_match_score", 3)])
        generic = float(row[col_idx.get("generic_phrase_score", 9)])
        stuffing = float(row[col_idx.get("keyword_stuffing_score", 11)])
        density  = float(row[col_idx.get("skill_density", 7)])

        if generic >= 0.60 or match < 0.20:
            cls = 2
            proba = np.array([0.05, 0.10, 0.85])
        elif generic >= 0.40 or stuffing >= 0.60 or match < 0.40:
            cls = 1
            proba = np.array([0.15, 0.70, 0.15])
        else:
            cls = 0
            confidence = min(0.95, 0.60 + match * 0.35 + density * 0.01)
            proba = np.array([confidence, (1 - confidence) * 0.6, (1 - confidence) * 0.4])
        return cls, proba

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array([self._classify(row, self._cols)[0] for row in X])

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return np.array([self._classify(row, self._cols)[1] for row in X])


def predict(features: dict | list[dict]) -> list[dict]:
    model, cols = load_model()

    if isinstance(features, dict):
        features = [features]

    df = pd.DataFrame(features)
    for col in cols:
        if col not in df.columns:
            df[col] = 0.0

    X = df[cols].fillna(0.0).values.astype(float)

    if isinstance(model, _HeuristicFallbackClassifier):
        model._cols = cols
        logger.info("[Prediction Engine: FALLBACK HEURISTIC] -> Using dummy/fallback logic.")
    else:
        logger.info("[Prediction Engine: REAL XGBOOST] -> Using trained ML model.")

    classes = model.predict(X)
    probs   = model.predict_proba(X)

    # ── SHAP Explainability ──────────────────────────────────────────────
    # Use XGBoost native SHAP for real model, heuristic approximation for fallback.
    # This provides transparency on which features drove the classification decision.
    if not isinstance(model, _HeuristicFallbackClassifier):
        shap_vals = _compute_xgboost_shap(model, X)
    else:
        shap_vals = _compute_heuristic_shap(X, cols)

    results = []
    for i, _ in enumerate(classes):
        auth_prob = float(probs[i][0])
        
        # Apply proposed threshold logic
        if auth_prob >= 0.80:
            cls_int = 0
            label = 'Authentic'
            confidence = auth_prob
        elif auth_prob >= 0.50:
            cls_int = 1
            label = 'Suspicious'
            # If it's suspicious, we might want to just show the auth_prob as the confidence, 
            # or the prob of suspicious. Let's show auth_prob as the defining metric, 
            # or max prob. Actually, let's use the probability of the assigned class to be consistent.
            confidence = float(probs[i][1]) if float(probs[i][1]) > auth_prob else auth_prob
        else:
            cls_int = 2
            label = 'Potentially Fake'
            confidence = float(probs[i][2]) if float(probs[i][2]) > auth_prob else (1.0 - auth_prob)
            
        result = {
            'classification': label,
            'confidence': round(confidence, 4),
        }
        for j, class_label in _LABEL_MAP.items():
            result[f'prob_{class_label}'] = round(float(probs[i][j]), 4)
            
        # Add SHAP explanation (Top 3 features) — displayed on the HR dashboard
        # to explain exactly why the classifier gave this specific verdict.
        if shap_vals is not None:
            try:
                instance_shap = shap_vals[cls_int][i]
                top_indices = np.argsort(np.abs(instance_shap))[::-1][:3]

                explanations = []
                for idx in top_indices:
                    feat_name = cols[idx]
                    shap_val  = float(instance_shap[idx])
                    feat_val  = float(X[i][idx])
                    # Only include features that actually contributed something
                    if abs(shap_val) > 0.0001:
                        explanations.append({
                            'feature':      feat_name,
                            'value':        round(feat_val, 4),
                            'contribution': round(shap_val, 4)
                        })
                result['top_features'] = explanations
            except Exception as e:
                logger.error(f"Failed to extract SHAP features: {e}")
                result['top_features'] = []
                
        results.append(result)

    return results


def _compute_xgboost_shap(model, X: np.ndarray):
    """Compute SHAP values using XGBoost's native pred_contribs (avoids shap library compat issues)."""
    try:
        import xgboost as xgb
        booster = model.get_booster()
        dmat = xgb.DMatrix(X)
        # Shape: (n_samples, n_features+1, n_classes) for multiclass
        # Last column is the bias term
        contribs = booster.predict(dmat, pred_contribs=True)
        # Convert to list of (n_samples, n_features) per class
        return [contribs[:, :-1, c] for c in range(contribs.shape[2])]
    except Exception as e:
        logger.error(f"XGBoost native SHAP failed: {e}")
        return None


def _compute_heuristic_shap(X: np.ndarray, cols: list):
    """Compute pseudo-SHAP contributions for the fallback heuristic classifier."""
    try:
        n_samples, n_features = X.shape
        n_classes = len(_LABEL_MAP)
        shap_vals = np.zeros((n_samples, n_features, n_classes))

        key_idx = {
            'final_match_score': cols.index('final_match_score'),
            'generic_phrase_score': cols.index('generic_phrase_score'),
            'keyword_stuffing_score': cols.index('keyword_stuffing_score'),
            'skill_density': cols.index('skill_density'),
        }

        for i in range(n_samples):
            match   = float(X[i, key_idx['final_match_score']])
            generic = float(X[i, key_idx['generic_phrase_score']])
            stuffing = float(X[i, key_idx['keyword_stuffing_score']])
            density = float(X[i, key_idx['skill_density']])

            # Approximate per-feature directional contribution for each class
            # Class 0 (Authentic): match and density push toward, generic/stuffing push away
            # Class 2 (Potentially Fake): opposite
            if generic >= 0.60 or match < 0.20:
                fake_strength = 1.0
            elif generic >= 0.40 or stuffing >= 0.60 or match < 0.40:
                fake_strength = 0.5
            else:
                fake_strength = 0.0

            # Per-class contributions (simplified heuristic)
            for c in range(n_classes):
                feat_contribs = np.zeros(n_features)
                if c == 0:  # Authentic
                    feat_contribs[key_idx['final_match_score']] = match * (1 - fake_strength)
                    feat_contribs[key_idx['skill_density']] = density * 0.01
                    feat_contribs[key_idx['generic_phrase_score']] = -generic * fake_strength
                    feat_contribs[key_idx['keyword_stuffing_score']] = -stuffing * fake_strength
                elif c == 2:  # Potentially Fake
                    feat_contribs[key_idx['final_match_score']] = -match * fake_strength
                    feat_contribs[key_idx['generic_phrase_score']] = generic * fake_strength
                    feat_contribs[key_idx['keyword_stuffing_score']] = stuffing * fake_strength
                    feat_contribs[key_idx['skill_density']] = -density * 0.01
                # c == 1 (Suspicious) - mid-range contributions
                shap_vals[i, :, c] = feat_contribs

        return [shap_vals[:, :, c] for c in range(n_classes)]
    except Exception as e:
        logger.error(f"Heuristic SHAP failed: {e}")
        return None


def get_feature_importance() -> list[dict]:
    load_model()
    if _model_meta and 'feature_importance' in _model_meta:
        return _model_meta['feature_importance']
    try:
        with open(METRICS_PATH, 'r') as f:
            data = json.load(f)
        if 'feature_importance' in data:
            return data['feature_importance']
    except Exception:
        pass
    names = _feature_names or _load_feature_names_from_metrics()
    return [{'feature': f, 'importance': 0.0} for f in names]


def get_model_info() -> dict:
    load_model()
    if _model_meta:
        return {
            'feature_names':      _feature_names,
            'params':             _model_meta.get('params', {}),
            'test_accuracy':      _model_meta.get('test_accuracy', 0.0),
            'test_f1':            _model_meta.get('test_f1', 0.0),
            'feature_importance': get_feature_importance(),
            'classes':            list(_LABEL_MAP.values()),
        }
    try:
        with open(METRICS_PATH, 'r') as f:
            data = json.load(f)
        return {
            'feature_names':      data.get('feature_cols', _feature_names),
            'params':             data.get('best_params', {}),
            'test_accuracy':      data.get('test_accuracy', 0.0),
            'test_f1':            data.get('test_f1_weighted', 0.0),
            'feature_importance': data.get('feature_importance', []),
            'classes':            list(_LABEL_MAP.values()),
        }
    except Exception as e:
        return {
            'feature_names':      _feature_names or [],
            'params':             {},
            'test_accuracy':      0.0,
            'test_f1':            0.0,
            'feature_importance': [],
            'classes':            list(_LABEL_MAP.values()),
        }

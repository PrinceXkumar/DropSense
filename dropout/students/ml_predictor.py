import os
import joblib
import numpy as np
from django.conf import settings

# Directory where models are stored
MODEL_DIR = os.path.join(settings.BASE_DIR, "ml_models")

# Cache loaded model objects in memory
_model = None
_encoder = None
_features = None
_importances = None
_feature_encoder = None


def _load_model():
    """Load model artifacts from disk (cached after first call)."""
    global _model, _encoder, _features, _importances, _feature_encoder

    if _model is not None:
        return True

    # Use names matching train_model.py
    model_path = os.path.join(MODEL_DIR, "dropout_model.joblib")
    encoder_path = os.path.join(MODEL_DIR, "label_encoder.joblib")
    f_encoder_path = os.path.join(MODEL_DIR, "feature_encoder.joblib")
    features_path = os.path.join(MODEL_DIR, "feature_names.joblib")
    importances_path = os.path.join(MODEL_DIR, "feature_importances.joblib")

    if not os.path.exists(model_path):
        return False

    try:
        _model = joblib.load(model_path)
        _encoder = joblib.load(encoder_path)
        _features = joblib.load(features_path)
        if os.path.exists(f_encoder_path):
            _feature_encoder = joblib.load(f_encoder_path)
        if os.path.exists(importances_path):
            _importances = joblib.load(importances_path)
        return True
    except Exception:
        return False


def _extract_features(student):
    """Extract and encode the feature vector from a Student object."""
    import pandas as pd
    
    # Extract raw data
    raw_data = {field: getattr(student, field, 0) for field in _features}
    df = pd.DataFrame([raw_data])
    
    # Apply ordinal encoding if available
    if _feature_encoder:
        # Match CATEGORICAL_FIELDS from train_model.py
        categorical_cols = [
            "daytime_evening_attendance",
            "gender"
        ]
        # Only encode fields that were targeted during training
        active_cats = [c for c in categorical_cols if c in df.columns]
        df[active_cats] = _feature_encoder.transform(df[active_cats].astype(str))
    
    return df.astype(float).values


def predict_student(student):
    """
    Predict dropout probability for a student using a Hybrid System (ML + Rules).
    """
    if not _load_model():
        return {"prediction": "Unknown", "confidence": 0, "model_available": False}

    try:
        from .risk_engine import calculate_risk
        
        # 1. Base ML Prediction
        X = _extract_features(student)
        proba = _model.predict_proba(X)[0]
        
        # Mapping labels
        # _encoder.classes_ should contain ['Dropout', 'Non-Dropout']
        classes = list(_encoder.classes_)
        dropout_idx = classes.index('Dropout')
        
        raw_dropout_prob = proba[dropout_idx]
        
        # 2. Rule-Based Factor
        risk_data = calculate_risk(student)
        risk_score = risk_data['risk_score'] # 0 - 100
        
        # 3. Rule-Based Correction Logic
        correction_applied = False
        adjusted_prob = raw_dropout_prob
        
        # Case A: False Positive Guard (0% rule risk but high ML dropout)
        if risk_score <= 10 and raw_dropout_prob > 0.5:
            # Dampen the probability: blend it towards a safer value
            # We cut the dropout probability significantly if the student has no risk factors
            adjusted_prob = (raw_dropout_prob * 0.2) + (0.05 * 0.8) 
            correction_applied = True
            
        # Case B: High Risk Safety Override
        elif risk_score >= 60 and raw_dropout_prob < 0.6:
            # Boost the dropout probability if physical rules suggest high danger
            adjusted_prob = max(raw_dropout_prob, 0.8)
            correction_applied = True

        # 4. Final Interpretation
        # Re-map back to final status
        final_label = 'Dropout' if adjusted_prob > 0.5 else 'Non-Dropout'
        # Confidence is distance from decision boundary (0.5) scaled or just the probability
        confidence = adjusted_prob if final_label == 'Dropout' else (1 - adjusted_prob)

        return {
            "prediction": final_label,
            "confidence": round(confidence * 100, 2),
            "probabilities": {
                "Dropout": round(adjusted_prob * 100, 2),
                "Non-Dropout": round((1 - adjusted_prob) * 100, 2)
            },
            "raw_dropout_prob": round(raw_dropout_prob * 100, 2),
            "model_available": True,
            "correction_applied": correction_applied,
            "risk_score": risk_score,
            "risk_level": risk_data['risk_level']
        }

    except Exception as e:
        return {
            "prediction": f"Error: {str(e)}", 
            "confidence": 0, 
            "model_available": False
        }


def get_feature_importances(top_n=10):
    """Return top N feature importances."""
    if not _load_model() or _importances is None:
        return []
    sorted_imps = sorted(_importances.items(), key=lambda x: x[1], reverse=True)
    return sorted_imps[:top_n]


def get_student_feature_contributions(student, top_n=8):
    """
    Returns feature contributions for a specific student.
    """
    if not _load_model():
        return []
        
    X = _extract_features(student)[0]
    importances = _importances or {}
    
    contributions = []
    for i, name in enumerate(_features):
        val = X[i]
        imp = importances.get(name, 0)
        # We use a simple product as a proxy for 'importance' in this report
        contributions.append({
            "feature": name.replace("_", " ").title(),
            "importance": round(imp * 100, 1),
            "value": round(float(val), 2)
        })
        
    contributions.sort(key=lambda x: abs(x["importance"]), reverse=True)
    return contributions[:top_n]

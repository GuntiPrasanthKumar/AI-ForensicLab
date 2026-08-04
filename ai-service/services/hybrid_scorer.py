import numpy as np
from typing import Dict, Any, List

def compute_hybrid_score(
    model_score: float,
    artifact_score: float,
    metadata_score: float,
    is_camera_authentic: bool,
    has_ai_signature: bool
) -> Dict[str, Any]:
    """
    Computes weighted hybrid confidence scoring:
    AI Probability = 0.55 * Model + 0.25 * Artifacts + 0.20 * Metadata
    Includes override rules for verified AI signatures and camera EXIF.
    """
    # 1. Weighted Linear Hybrid Score
    weighted_ai_prob = (0.55 * model_score) + (0.25 * artifact_score) + (0.20 * metadata_score)

    # 2. Hard Override Rules for Definitive Evidence
    if has_ai_signature:
        # Explicit AI generator tag found in EXIF/PNG chunks
        final_ai_prob = max(95.0, weighted_ai_prob)
        override_reason = "Definitive AI Generator Signature Tag Present"
    elif is_camera_authentic and model_score < 30.0:
        # Authentic camera EXIF + low model AI score = Authentic photo
        final_ai_prob = min(8.5, weighted_ai_prob)
        override_reason = "Authentic Camera Hardware Optics Confirmed"
    else:
        final_ai_prob = weighted_ai_prob
        override_reason = None

    final_ai_prob = round(float(np.clip(final_ai_prob, 0.5, 99.5)), 1)
    human_prob = round(float(max(0.0, 100.0 - final_ai_prob)), 1)

    # 3. Determine Signal Alignment & Confidence Level
    signals = [model_score, artifact_score]
    if metadata_score != 50.0: # Only include metadata in variance if not missing/neutral
        signals.append(metadata_score)

    signal_std = float(np.std(signals))

    if has_ai_signature or (is_camera_authentic and final_ai_prob < 15.0):
        confidence = "High"
    elif signal_std < 18.0:
        confidence = "High"
    elif signal_std < 32.0:
        confidence = "Medium"
    else:
        confidence = "Low"

    # 4. Risk Level Assignment
    if final_ai_prob >= 75.0:
        risk_level = "High Risk (AI-Generated)"
    elif final_ai_prob >= 40.0:
        risk_level = "Medium Risk (Potentially Manipulated)"
    else:
        risk_level = "Low Risk (Authentic Photograph)"

    return {
        "aiProbability": final_ai_prob,
        "humanProbability": human_prob,
        "morphProbability": 0.0,
        "confidence": confidence,
        "risk_level": risk_level,
        "signal_std": round(signal_std, 2),
        "weights": {
            "model_weight": 0.55,
            "artifact_weight": 0.25,
            "metadata_weight": 0.20
        },
        "override_applied": override_reason
    }

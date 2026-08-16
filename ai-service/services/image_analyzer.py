"""
Image Analyzer Module
Main entry point for evaluating image authenticity using deep learning models.
"""
import os
import time
from typing import Dict, Any

from services.image_preprocessor import preprocess_image
from services.cv_model_engine import run_cv_model_inference
from services.metadata_engine import analyze_metadata
from services.artifact_engine import analyze_digital_artifacts
from services.hybrid_scorer import compute_hybrid_score
from services.explainability_engine import generate_explainability_report

def analyze_image_authenticity(image_bytes: bytes) -> Dict[str, Any]:
    """
    Main entry point for AI Image Forensics Analysis.
    Executes complete multi-layer computer vision pipeline:
    1. Preprocessing & Integrity Check
    2. Deep Learning Model Inference (PyTorch)
    3. EXIF & AI Generator Metadata Inspection
    4. Digital Artifact Signal Processing (ELA + 2D FFT)
    5. Hybrid Scoring Engine
    6. Explainability & Heatmap Generation
    """
    t0 = time.time()
    print(f"\n=======================================================")
    print(f"[Forensic Engine] Starting Image Analysis ({len(image_bytes)} bytes)")
    print(f"=======================================================")

    try:
        # Step 1: Preprocessing & Color Space Conversion
        prep = preprocess_image(image_bytes)
        pil_img = prep["pil_image"]
        np_img = prep["np_image"]

        # Step 2: Deep Learning Vision Model Inference
        cv_res = run_cv_model_inference(pil_img, np_img)

        # Step 3: Metadata & EXIF Analysis
        meta_res = analyze_metadata(pil_img, image_bytes)

        # Step 4: Digital Image Artifact Analysis (ELA + FFT)
        art_res = analyze_digital_artifacts(pil_img, np_img)

        # Step 5: Hybrid Confidence Scoring Engine
        scoring = compute_hybrid_score(
            model_score=cv_res["ai_model_probability"],
            artifact_score=art_res["artifact_ai_score"],
            metadata_score=meta_res["metadata_ai_score"],
            is_camera_authentic=meta_res["is_camera_authentic"],
            has_ai_signature=meta_res["has_ai_signature"]
        )

        # Step 6: Explainability & Heatmap Report
        report = generate_explainability_report(scoring, meta_res, art_res, cv_res)

        elapsed = round(time.time() - t0, 3)
        print(f"[Forensic Engine] Completed in {elapsed}s | Result: {scoring['aiProbability']}% AI ({scoring['risk_level']})")

        # Package complete structured forensic JSON payload
        response = {
            "aiProbability": scoring["aiProbability"],
            "humanProbability": scoring["humanProbability"],
            "morphProbability": scoring["morphProbability"],
            "confidence": scoring["confidence"],
            "risk_level": scoring["risk_level"],
            "explanation": report["explanation"],
            "reasons": report["reasons"],
            "detectedArtifacts": report["detectedArtifacts"],
            "heatmap_base64": report.get("heatmap_base64"),
            "provider_used": cv_res.get("model_name", "PyTorch Hybrid Vision Engine"),
            "engine_status": "Active Computer Vision Pipeline",
            "is_cached": False,
            "metrics": {
                "model_score": cv_res["ai_model_probability"],
                "artifact_score": art_res["artifact_ai_score"],
                "metadata_score": meta_res["metadata_ai_score"],
                "file_width": prep["width"],
                "file_height": prep["height"],
                "file_format": prep["format"],
                "processing_time_sec": elapsed,
                **art_res.get("artifact_metrics", {})
            },
            "metadata_summary": meta_res.get("metadata_summary", {})
        }

        return response

    except Exception as e:
        print(f"[Forensic Engine Error] Pipeline failed: {e}")

        # Fail-safe dynamic inspection if unexpected exception occurs
        return _fallback_error_response(image_bytes, str(e))


def _fallback_error_response(image_bytes: bytes, err_msg: str) -> Dict[str, Any]:
    """Graceful error fallback returning dynamic basic container properties."""
    return {
        "aiProbability": 50.0,
        "humanProbability": 50.0,
        "morphProbability": 0.0,
        "confidence": "Low (Fail-safe)",
        "risk_level": "Uncertain",
        "explanation": f"Forensic vision pipeline encountered exception: {err_msg}",
        "reasons": ["Processing exception handled cleanly"],
        "detectedArtifacts": ["Standard file format"],
        "heatmap_base64": None,
        "provider_used": "PyTorch Fail-safe Engine",
        "engine_status": "Backup Mode Active",
        "is_cached": False,
        "metrics": {"error": err_msg}
    }

# Type annotation marker for image analysis pipeline

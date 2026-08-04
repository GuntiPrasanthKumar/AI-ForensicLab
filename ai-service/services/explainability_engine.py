import io
import base64
from typing import Dict, Any, List
from PIL import Image

def generate_explainability_report(
    scoring_result: Dict[str, Any],
    metadata_result: Dict[str, Any],
    artifact_result: Dict[str, Any],
    cv_model_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Synthesizes observations from all forensic layers:
    1. Compiles specific bulleted reasons & detected artifacts
    2. Formulates detailed forensic reasoning narrative
    3. Converts ELA Heatmap PIL Image to Base64 Data URI
    """
    ai_prob = scoring_result["aiProbability"]
    confidence = scoring_result["confidence"]
    risk_level = scoring_result["risk_level"]
    model_name = cv_model_result.get("model_name", "PyTorch Vision Engine")

    # 1. Combine All Detected Artifacts
    combined_artifacts: List[str] = []

    # Model specific findings
    if cv_model_result.get("features"):
        feats = cv_model_result["features"]
        if feats.get("fft_high_ratio", 0) > 0.20:
            combined_artifacts.append(f"Model Feature: Elevated high-frequency spectrum ratio ({feats['fft_high_ratio']:.3f})")

    # Metadata findings
    combined_artifacts.extend(metadata_result.get("detected_metadata_artifacts", []))

    # Artifact findings
    combined_artifacts.extend(artifact_result.get("detected_artifacts", []))

    # Deduplicate while preserving order
    unique_artifacts = []
    for art in combined_artifacts:
        if art not in unique_artifacts:
            unique_artifacts.append(art)

    # 2. Formulate Structured Reasons & Explanation Narrative
    reasons = unique_artifacts[:6] # Top 6 specific bullet points

    if ai_prob >= 75.0:
        explanation = (
            f"Forensic Vision Engine ({model_name}): Image exhibits strong synthetic indicators. "
            f"AI probability is {ai_prob}% ({risk_level}, {confidence} Confidence). "
            f"Primary findings: {', '.join(reasons[:3]) if reasons else 'Deep feature anomaly detected'}."
        )
    elif ai_prob >= 40.0:
        explanation = (
            f"Forensic Vision Engine ({model_name}): Image shows mixed synthetic and authentic characteristics. "
            f"AI probability is {ai_prob}% ({risk_level}). "
            f"Key observations: {', '.join(reasons[:2]) if reasons else 'Inconsistent digital signatures'}."
        )
    else:
        explanation = (
            f"Forensic Vision Engine ({model_name}): Image displays authentic optical characteristics. "
            f"Human probability is {scoring_result['humanProbability']}% ({risk_level}, {confidence} Confidence). "
            f"Key observations: {', '.join(reasons[:2]) if reasons else 'Natural camera sensor signatures'}."
        )

    # 3. Convert ELA Heatmap to Base64 Data URI
    heatmap_base64 = None
    ela_pil = artifact_result.get("ela_heatmap_pil")
    if ela_pil:
        try:
            # Resize heatmap for lightweight payload
            heatmap_resized = ela_pil.resize((400, int(400 * ela_pil.height / max(1, ela_pil.width))))
            buf = io.BytesIO()
            heatmap_resized.save(buf, format="JPEG", quality=85)
            b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
            heatmap_base64 = f"data:image/jpeg;base64,{b64_str}"
        except Exception as e:
            print(f"[Explainability Engine] Heatmap base64 encoding error: {e}")

    return {
        "explanation": explanation,
        "reasons": reasons,
        "detectedArtifacts": unique_artifacts,
        "heatmap_base64": heatmap_base64
    }

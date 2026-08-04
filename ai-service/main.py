from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from services.cache_manager import global_cache
from services.ai_judge import ai_judge_score
from services.perplexity import calculate_perplexity
from services.features import (
    burstiness,
    lexical_diversity,
    repetition_score,
    shannon_entropy,
    sentence_length_variation_ratio,
)
from services.scorer import compute_ai_score
from services.explanation import generate_forensic_explanation
from services.image_analyzer import analyze_image_authenticity
from services.video_analyzer import analyze_video_authenticity

app = FastAPI(title="AI Forensic Lab API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextPayload(BaseModel):
    text: str

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "AI Microservice", "cache_status": "active"}

def process_text_analysis(text: str):
    if not text or len(text.split()) < 5:
        return {
            "aiProbability": 0,
            "humanProbability": 100,
            "confidence": "Text too short (min 5 words)",
            "explanation": "Analysis skipped: Provided text is too short for reliable linguistic breakdown.",
            "metrics": {},
            "reasons": [],
            "provider_used": "Pre-check Filter",
            "is_cached": False
        }

    text_sample = text[:3000]

    # 1. Check TTL Cache
    cached_res = global_cache.get("text", text_sample)
    if cached_res:
        print("[Cache] Text analysis cache hit!")
        return cached_res

    # 2. Compute Linguistic Features
    try: p = calculate_perplexity(text_sample)
    except: p = 50.0

    try: b = burstiness(text_sample)
    except: b = 50.0

    try: l = lexical_diversity(text_sample)
    except: l = 0.5

    try: r = repetition_score(text_sample)
    except: r = 0.1

    try: e = shannon_entropy(text_sample)
    except: e = 4.0

    try: sv = sentence_length_variation_ratio(text_sample)
    except: sv = 0.5

    # 3. Multi-Provider AI Judge
    try:
        ai_model_score, provider_used = ai_judge_score(text_sample)
    except Exception:
        ai_model_score, provider_used = 50.0, "Local Feature Engine"

    feature_score, _ = compute_ai_score(p, b, l, r, e, sv)

    # Hybrid Score Calculation (60% AI LLM Judge + 40% Algorithmic Features)
    ai_prob = (0.6 * ai_model_score) + (0.4 * feature_score)
    ai_prob = round(max(0.0, min(100.0, ai_prob)), 1)

    if ai_prob > 75:
        confidence = "High"
    elif ai_prob > 50:
        confidence = "Medium"
    else:
        confidence = "Low"

    reasons = []
    if p < 40: reasons.append("Low perplexity (highly predictable text patterns)")
    if b < 20: reasons.append("Low burstiness (uniform sentence structures)")
    if l < 0.4: reasons.append("Limited vocabulary variety (repetitive tokens)")
    if r > 0.15: reasons.append("Frequent token phrase repetition detected")
    if e < 4: reasons.append("Low information entropy")
    if sv < 0.3: reasons.append("Flat sentence length variation")

    metrics = {
        "perplexity": round(p, 2),
        "burstiness": round(b, 2),
        "lexical_diversity": round(l, 3),
        "repetition_score": round(r, 3),
        "entropy": round(e, 2),
        "sentence_variation": round(sv, 3),
        "ai_model_score": round(ai_model_score, 1),
    }

    # 4. Multi-Provider Forensic Explanation
    explanation = generate_forensic_explanation(text_sample, metrics, ai_prob)

    response_data = {
        "aiProbability": ai_prob,
        "humanProbability": round(100.0 - ai_prob, 1),
        "confidence": confidence,
        "metrics": metrics,
        "reasons": reasons,
        "explanation": explanation,
        "provider_used": provider_used,
        "is_cached": False
    }

    # 5. Store in TTL Cache
    global_cache.set("text", text_sample, response_data)
    return response_data

@app.post("/api/detect")
async def detect_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        return process_text_analysis(text)
    except Exception as e:
        return {"error": str(e), "message": "Failed to parse text file content"}

@app.post("/api/detect-text")
async def detect_text(payload: TextPayload):
    try:
        return process_text_analysis(payload.text)
    except Exception as e:
        return {"error": str(e), "message": "Text detection failed"}

@app.post("/api/detect-image")
async def detect_image(file: UploadFile = File(...)):
    try:
        content = await file.read()
        
        cached_res = global_cache.get("image", content)
        if cached_res:
            print("[Cache] Image analysis cache hit!")
            return cached_res

        res = analyze_image_authenticity(content)
        global_cache.set("image", content, res)
        return res
    except Exception as e:
        print(f"[Image Endpoint] Error: {e}")
        return {
            "aiProbability": 0.0,
            "humanProbability": 100.0,
            "morphProbability": 0.0,
            "isNatural": True,
            "confidence": "Low",
            "explanation": f"Image processing failed: {str(e)}",
            "detectedArtifacts": ["File processing error"],
            "provider_used": "Error Fallback",
            "is_cached": False
        }

@app.post("/api/detect-video")
async def detect_video(file: UploadFile = File(...)):
    try:
        content = await file.read()

        cached_res = global_cache.get("video", content)
        if cached_res:
            print("[Cache] Video analysis cache hit!")
            return cached_res

        res = analyze_video_authenticity(content)
        global_cache.set("video", content, res)
        return res
    except Exception as e:
        print(f"[Video Endpoint] Error: {e}")
        return {
            "aiProbability": 0.0,
            "humanProbability": 100.0,
            "morphProbability": 0.0,
            "isNatural": True,
            "confidence": "Low",
            "explanation": f"Video processing failed: {str(e)}",
            "detectedArtifacts": ["File processing error"],
            "provider_used": "Error Fallback",
            "is_cached": False
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
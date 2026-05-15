from fastapi import FastAPI, UploadFile, File, Body
from services.ai_judge import ai_judge_score
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_text_analysis(text: str):
    if not text or len(text.split()) < 5:
        return {
            "aiProbability": 0,
            "humanProbability": 0,
            "confidence": "Text too short",
        }

    text = text[:2000] # Increased limit
    print(f"Processing text (length: {len(text)})...")

    try: p = calculate_perplexity(text)
    except: p = 50

    try: b = burstiness(text)
    except: b = 50

    try: l = lexical_diversity(text)
    except: l = 0.5

    try: r = repetition_score(text)
    except: r = 0.1

    try: e = shannon_entropy(text)
    except: e = 4

    try: sv = sentence_length_variation_ratio(text)
    except: sv = 0.5

    try: ai_model_score = ai_judge_score(text)
    except: ai_model_score = 50

    feature_score, _ = compute_ai_score(p, b, l, r, e, sv)

    # Hybrid Score Calculation
    ai_prob = (0.6 * ai_model_score) + (0.4 * feature_score)

    if ai_prob > 75:
        confidence = "High"
    elif ai_prob > 55:
        confidence = "Medium"
    else:
        confidence = "Low"

    reasons = []
    if p < 40: reasons.append("Low perplexity (highly predictable patterns)")
    if b < 20: reasons.append("Low burstiness (uniform sentence structure)")
    if l < 0.4: reasons.append("Limited vocabulary variety")
    if r > 0.15: reasons.append("Repetitive word usage detected")
    if e < 4: reasons.append("Low information entropy")
    if sv < 0.3: reasons.append("Flat sentence length variation")

    metrics = {
        "perplexity": round(p, 2),
        "burstiness": round(b, 2),
        "lexical_diversity": round(l, 3),
        "repetition_score": round(r, 3),
        "entropy": round(e, 2),
        "sentence_variation": round(sv, 3),
        "ai_model_score": round(ai_model_score, 2),
    }

    explanation = generate_forensic_explanation(text, metrics, round(ai_prob, 2))

    return {
        "aiProbability": round(ai_prob, 2),
        "humanProbability": round(100 - ai_prob, 2),
        "confidence": confidence,
        "metrics": metrics,
        "reasons": reasons,
        "explanation": explanation,
    }

@app.post("/api/detect")
async def detect_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8")
        return process_text_analysis(text)
    except Exception as e:
        return {"error": str(e), "message": "Invalid text file"}

@app.post("/api/detect-image")
async def detect_image(file: UploadFile = File(...)):
    print(f"DEBUG: Received image upload: {file.filename}")
    try:
        content = await file.read()
        return analyze_image_authenticity(content)
    except Exception as e:
        return {"error": str(e), "message": "Image analysis failed"}

from services.video_analyzer import analyze_video_authenticity

@app.post("/api/detect-video")
async def detect_video(file: UploadFile = File(...)):
    print(f"DEBUG: Received video upload: {file.filename}")
    try:
        content = await file.read()
        return analyze_video_authenticity(content)
    except Exception as e:
        return {"error": str(e), "message": "Video analysis failed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
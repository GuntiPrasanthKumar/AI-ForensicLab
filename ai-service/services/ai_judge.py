from services.provider_manager import provider_manager

def ai_judge_score(text: str) -> tuple[float, str]:
    """
    Evaluates text using Multi-Provider LLM Judge (Gemini -> OpenAI -> Perplexity).
    Returns (ai_score, provider_name).
    Falls back gracefully to 50% baseline if all providers are unavailable.
    """
    prompt = (
        "You are an AI detection system. Return ONLY a single number between 0 and 100 "
        "indicating how likely the following text is AI-generated (0 = 100% Human, 100 = 100% AI):\n\n"
        f"{text[:1500]}"
    )

    try:
        raw_output, provider_used = provider_manager.generate_completion(prompt)
        import re
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', raw_output)
        if numbers:
            score = float(numbers[0])
            score = max(0.0, min(100.0, score))
            return score, provider_used
    except Exception as e:
        print(f"[AI Judge] Multi-provider LLM score failed ({e}). Using heuristic fallback.")

    return 50.0, "Local Feature Analysis"
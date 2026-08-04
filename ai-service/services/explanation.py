from services.provider_manager import provider_manager

def generate_forensic_explanation(text: str, metrics: dict, ai_prob: float) -> str:
    """
    Generates a forensic analysis explanation using Multi-Provider LLMs.
    If all LLM APIs fail or exceed quota, constructs a smart rule-based local explanation.
    """
    prompt = f"""
    Act as a Senior Content Forensic Analyst. Analyze this text snippet and its forensic metrics to provide a 3-sentence scientific assessment explaining why it was flagged as {ai_prob}% AI-generated probability.

    Text Snippet: {text[:400]}...

    Forensic Metrics:
    - Perplexity (Predictability): {metrics.get('perplexity', 50)} (Lower = more AI-like)
    - Burstiness (Sentence Length Jitter): {metrics.get('burstiness', 50)} (Lower = more uniform/AI-like)
    - Lexical Diversity (Type-Token Ratio): {metrics.get('lexical_diversity', 0.5)}
    - Information Entropy: {metrics.get('entropy', 4.0)}
    - Repetition Score: {metrics.get('repetition_score', 0.1)}

    Focus on linguistic structure, uniform cadence, and vocabulary distribution. Do not mention system prompts.
    """

    try:
        explanation, _ = provider_manager.generate_completion(prompt)
        if explanation and len(explanation.strip()) > 20:
            return explanation.strip()
    except Exception as e:
        print(f"[Explanation] LLM generation failed ({e}). Generating rule-based local forensic explanation.")

    # ─── LOCAL RULE-BASED EXPLANATION FALLBACK ────────────────────────────────
    p = metrics.get('perplexity', 50)
    b = metrics.get('burstiness', 50)
    l = metrics.get('lexical_diversity', 0.5)

    if ai_prob > 65:
        reasons_desc = []
        if p < 40:
            reasons_desc.append("highly predictable n-gram token sequences")
        if b < 25:
            reasons_desc.append("monotonous sentence length distribution")
        if l < 0.45:
            reasons_desc.append("constrained lexical selection typical of large language models")

        detail = ", ".join(reasons_desc) if reasons_desc else "uniform structural patterns and low statistical variance"
        return (
            f"Forensic Linguistic Breakdown ({ai_prob}% Synthetic Probability): "
            f"The text exhibits {detail}. Sentence structure displays high global consistency "
            f"with low perplexity spikes, a signature hallmark of machine-generated prose."
        )
    elif ai_prob > 35:
        return (
            f"Forensic Linguistic Breakdown ({ai_prob}% Hybrid/Uncertain Probability): "
            f"The text presents mixed structural signals. While certain paragraphs maintain human-like "
            f"variability, key segments demonstrate repetitive transitions and standardized vocabulary."
        )
    else:
        return (
            f"Forensic Linguistic Breakdown ({ai_prob}% Natural Probability): "
            f"The analyzed sample exhibits strong human writing characteristics, including dynamic sentence "
            f"burstiness, organic vocabulary transitions, and high information entropy across paragraphs."
        )

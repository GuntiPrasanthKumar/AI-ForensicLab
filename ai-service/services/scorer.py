def normalize(value, min_val, max_val):
    if max_val - min_val == 0:
        return 0
    return (value - min_val) / (max_val - min_val)


def compute_ai_score(perplexity, burstiness, lexical_div, repetition, entropy, sv):
    """
    Combines multiple metrics into a weighted AI probability score.
    """


    p_score = 1 - normalize(perplexity, 20, 100)          
    b_score = 1 - normalize(burstiness, 5, 200)           
    l_score = 1 - lexical_div                             
    r_score = repetition                                  
    e_score = 1 - normalize(entropy, 3, 8)   
    sv_score = sv             

    final_score = (
        0.35 * p_score +
        0.20 * b_score +
        0.15 * l_score +
        0.15 * r_score +
        0.15 * e_score +
        0.10 * sv_score
    )

    ai_probability = max(0, min(1, final_score)) * 100

    if ai_probability > 75:
        confidence = "High"
    elif ai_probability > 55:
        confidence = "Medium"
    else:
        confidence = "Low"

    return round(ai_probability, 2), confidence

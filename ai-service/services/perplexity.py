import math

def calculate_perplexity(text):
    # Free tier workaround: We cannot load the massive 500MB GPT-2 PyTorch model
    # into the Render 512MB RAM limit without crashing. 
    # We will simulate a baseline perplexity score, and rely on the Gemini AI 
    # and other lexical features to determine the AI probability.
    
    # Simple heuristic fallback: average word length and uniqueness
    words = text.split()
    if not words: return 50.0
    
    unique_words = len(set(words))
    lexical_richness = unique_words / len(words)
    
    # Simulate a perplexity curve (lower for repetitive/predictable text)
    simulated_perplexity = 20.0 + (lexical_richness * 60.0)
    
    return float(simulated_perplexity)

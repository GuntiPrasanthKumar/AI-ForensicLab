import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

def generate_forensic_explanation(text, metrics, ai_prob):
    try:
        prompt = f"""
        Act as an AI Content Forensic Expert. Analyze the following text and its forensic metrics to provide a detailed explanation of why it was flagged as {ai_prob}% AI-generated.
        
        Text Snippet: {text[:500]}...
        
        Metrics:
        - Perplexity: {metrics['perplexity']}
        - Burstiness: {metrics['burstiness']}
        - Lexical Diversity: {metrics['lexical_diversity']}
        - Repetition Score: {metrics['repetition_score']}
        - Information Entropy: {metrics['entropy']}
        
        Provide a concise 3-4 sentence explanation focusing on linguistic patterns, predictability, and structural consistency.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Explanation Error: {e}")
        return "Explanation currently unavailable due to API limitations."

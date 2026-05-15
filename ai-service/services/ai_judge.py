import google.generativeai as genai
import threading
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-pro")

def ai_judge_score(text):
    result = {"score": 50}

    def call_model():
        try:
            prompt = f"Return only a number (0-100) indicating how likely this text is AI-generated:\n{text}"
            response = model.generate_content(prompt)
            output = response.text.strip()
            result["score"] = float(output)
        except:
            result["score"] = 50

    thread = threading.Thread(target=call_model)
    thread.start()
    thread.join(timeout=3)

    return result["score"]
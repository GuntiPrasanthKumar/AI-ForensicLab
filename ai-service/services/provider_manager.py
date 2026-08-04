import os
import time
import random
import json
import re
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple, List
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

import google.generativeai as genai

class AIProviderManager:
    """
    Production-grade Multi-Provider AI Resilience Engine.
    Handles automatic provider failover: Gemini -> OpenAI -> Perplexity -> Local Fallback.
    Implements Exponential Backoff, Jitter, Timeout Protection, and Rate-Limit Handling.
    """
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")

        if self.gemini_api_key and "YOUR_GEMINI" not in self.gemini_api_key and len(self.gemini_api_key) > 10:
            try:
                genai.configure(api_key=self.gemini_api_key)
            except Exception as e:
                print(f"[ProviderManager] Warning configuring Gemini: {e}")

    def _should_retry_status(self, status_code: int) -> bool:
        """Determines if HTTP status code is retryable (429 rate limit, 5xx server errors)."""
        return status_code in (429, 500, 502, 503, 504)

    def _execute_with_retry(self, func, provider_name: str, max_retries: int = 2, base_delay: float = 1.0) -> Tuple[Optional[Any], Optional[str]]:
        """
        Executes a function with exponential backoff and random jitter.
        """
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                result = func()
                elapsed = time.time() - start_time
                print(f"[ProviderManager] [{provider_name}] Success in {round(elapsed, 2)}s")
                return result, None
            except Exception as err:
                err_str = str(err)
                print(f"[ProviderManager] [{provider_name}] Attempt {attempt + 1}/{max_retries + 1} failed: {err_str}")

                # Check if retryable
                is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower()
                is_timeout = "timeout" in err_str.lower() or "deadline" in err_str.lower()
                is_server_err = any(code in err_str for code in ["500", "502", "503", "504"])

                if not (is_rate_limit or is_timeout or is_server_err):
                    # Non-retryable error (e.g. 400 bad request, 401 invalid key)
                    return None, err_str

                if attempt < max_retries:
                    # Exponential backoff + random jitter
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0.1, 0.8)
                    print(f"[ProviderManager] Retrying [{provider_name}] in {round(delay, 2)}s...")
                    time.sleep(delay)
                else:
                    return None, err_str

        return None, "Max retries reached"

    # ─── PROVIDER 1: GEMINI ──────────────────────────────────────────────────
    def _call_gemini(self, prompt: str, image_bytes: Optional[bytes] = None) -> str:
        """Call Gemini API using gemini-1.5-flash / gemini-2.0-flash / gemini-1.5-pro."""
        if not self.gemini_api_key or "YOUR_GEMINI" in self.gemini_api_key or len(self.gemini_api_key) < 10:
            raise ValueError("Gemini API key missing or invalid")

        model_names = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-pro"]
        
        last_error = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                if image_bytes:
                    import io
                    import PIL.Image
                    img = PIL.Image.open(io.BytesIO(image_bytes))
                    if max(img.size) > 1024:
                        img.thumbnail((1024, 1024))
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_error = e
                print(f"[Gemini] Model {model_name} failed: {e}")
                continue
        
        raise last_error or RuntimeError("All Gemini models failed")

    # ─── PROVIDER 2: OPENAI ──────────────────────────────────────────────────
    def _call_openai(self, prompt: str, image_bytes: Optional[bytes] = None) -> str:
        """Call OpenAI API using gpt-4o-mini or gpt-3.5-turbo via HTTP."""
        if not self.openai_api_key or len(self.openai_api_key) < 10:
            raise ValueError("OpenAI API key missing")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }

        if image_bytes:
            b64_img = base64.b64encode(image_bytes).decode('utf-8')
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
                        }
                    ]
                }
            ]
            model_name = "gpt-4o-mini"
        else:
            messages = [{"role": "user", "content": prompt}]
            model_name = "gpt-4o-mini"

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 500
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data["choices"][0]["message"]["content"].strip()

    # ─── PROVIDER 3: PERPLEXITY ──────────────────────────────────────────────
    def _call_perplexity(self, prompt: str) -> str:
        """Call Perplexity API (sonar) via HTTP."""
        if not self.perplexity_api_key or len(self.perplexity_api_key) < 10:
            raise ValueError("Perplexity API key missing")

        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data["choices"][0]["message"]["content"].strip()

    # ─── PUBLIC MULTI-PROVIDER GENERATE METHOD ───────────────────────────────
    def generate_completion(self, prompt: str, image_bytes: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Attempts text/multimodal generation across available providers in order:
        1. Gemini -> 2. OpenAI -> 3. Perplexity -> Throws error for local fallback handling
        Returns: (response_text, provider_used)
        """
        # 1. Try Gemini
        res, err = self._execute_with_retry(lambda: self._call_gemini(prompt, image_bytes), "Gemini")
        if res:
            return res, "Google Gemini"

        # 2. Try OpenAI
        if self.openai_api_key:
            res, err = self._execute_with_retry(lambda: self._call_openai(prompt, image_bytes), "OpenAI")
            if res:
                return res, "OpenAI GPT-4o"

        # 3. Try Perplexity (text only)
        if self.perplexity_api_key and not image_bytes:
            res, err = self._execute_with_retry(lambda: self._call_perplexity(prompt), "Perplexity")
            if res:
                return res, "Perplexity AI"

        raise RuntimeError("All configured AI providers (Gemini, OpenAI, Perplexity) failed or exceeded quota.")

    def parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extracts and parses JSON safely from LLM output."""
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        raise ValueError("AI response did not contain valid JSON structure")

# Global Singleton Instance
provider_manager = AIProviderManager()

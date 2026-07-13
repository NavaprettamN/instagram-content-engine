import os
import time
import json
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

load_dotenv()

_client = None

# Groq is a free, no-card fallback (OpenAI-compatible, JSON mode, ~14.4k req/day).
# Used only when Gemini fails — chiefly its daily-quota 429, which retrying can't fix.
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _groq(prompt, system, json_response, temperature):
    """Fallback LLM call to Groq. Raises if no key or the request fails."""
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set — no fallback available.")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {"model": GROQ_MODEL, "messages": messages, "temperature": temperature}
    if json_response:
        body["response_format"] = {"type": "json_object"}  # prompts already say "Return JSON"
    r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {key}"}, json=body, timeout=60)
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    return json.loads(text) if json_response else text


def _image_part(image_path):
    """types.Part for a local image, or None if unreadable. Gemini 2.5 Flash is
    multimodal on the free tier, so vision input costs nothing."""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(image_path)[1].lower()
        mime = {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
        return types.Part.from_bytes(data=data, mime_type=mime)
    except Exception:
        return None


def generate_text(prompt, system=None, json_response=False, temperature=0.7,
                  image_path=None):
    """
    Gemini 2.5 Flash primary, with retry on 503 (high demand). On a 429
    (quota/rate) it falls straight to the free Groq fallback instead of retrying
    for minutes — retries can't beat a daily cap. Set json_response=True for a dict.

    `image_path` adds a local image as vision input (free on Flash). The Groq
    fallback is text-only, so it silently drops the image if Gemini is exhausted.
    """
    cfg = types.GenerateContentConfig(temperature=temperature)
    if json_response:
        cfg.response_mime_type = "application/json"
    if system:
        cfg.system_instruction = system

    contents = prompt
    if image_path:
        part = _image_part(image_path)
        if part is not None:
            contents = [part, prompt]

    delays = [10, 30, 60]  # transient-503 backoff only
    last_error = None
    for attempt, delay in enumerate([0] + delays, 1):
        if delay:
            print(f"Gemini busy — retrying in {delay}s (attempt {attempt}/{len(delays)+1})...")
            time.sleep(delay)
        try:
            response = _get_client().models.generate_content(
                model="gemini-2.5-flash", contents=contents, config=cfg,
            )
            return json.loads(response.text) if json_response else response.text
        except ServerError as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                last_error = e
                continue
            raise
        except ClientError as e:
            # 429 RESOURCE_EXHAUSTED — don't burn minutes retrying a daily cap; go
            # straight to the free fallback.
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("Gemini quota hit (429) — falling back to Groq.")
                return _groq(prompt, system, json_response, temperature)
            raise

    # Gemini stayed unavailable (503) through all retries — try the fallback too.
    try:
        print("Gemini unavailable after retries — falling back to Groq.")
        return _groq(prompt, system, json_response, temperature)
    except Exception:
        raise last_error

import os
import time
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError

load_dotenv()

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client

def generate_text(prompt, system=None, json_response=False, temperature=0.7):
    """
    Call Gemini 2.5 Flash with automatic retry on 503 (high demand).
    Set json_response=True to get a parsed dict/list back.
    """
    cfg = types.GenerateContentConfig(temperature=temperature)
    if json_response:
        cfg.response_mime_type = "application/json"
    if system:
        cfg.system_instruction = system

    delays = [10, 30, 60, 120]  # seconds between attempts
    last_error = None
    for attempt, delay in enumerate([0] + delays, 1):
        if delay:
            print(f"Gemini 503 — retrying in {delay}s (attempt {attempt}/{len(delays)+1})...")
            time.sleep(delay)
        try:
            response = _get_client().models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=cfg,
            )
            text = response.text
            return json.loads(text) if json_response else text
        except ServerError as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                last_error = e
                continue
            raise

    raise last_error

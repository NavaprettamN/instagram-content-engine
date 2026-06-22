import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client

def generate_text(prompt, system=None, json_response=False, temperature=0.7):
    """
    Call Gemini 2.5 Flash.
    Set json_response=True to get a parsed dict/list back.
    """
    client = _get_client()
    cfg = types.GenerateContentConfig(temperature=temperature)
    if json_response:
        cfg.response_mime_type = "application/json"
    if system:
        cfg.system_instruction = system

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=cfg,
    )
    text = response.text
    if json_response:
        return json.loads(text)
    return text

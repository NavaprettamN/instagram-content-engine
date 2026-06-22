import json
from agents._llm import generate_text


class ContentAgent:
    def __init__(self, config):
        self.brand_voice = config["brand_voice"]
        self.niche = config["niche"]

    def generate_carousel(self, idea):
        prompt = f"""Create a complete Instagram carousel post.

IDEA: {idea['hook']}
OUTLINE: {json.dumps(idea['outline']) if isinstance(idea['outline'], list) else idea['outline']}

BRAND VOICE: {self.brand_voice}

Generate exactly this JSON structure:
{{
  "slide_1_hook": "Bold headline, max 8 words, creates curiosity",
  "slide_1_subtext": "One line teaser, max 15 words",
  "slides": [
    {{
      "slide_number": 2,
      "headline": "Bold point, max 6 words",
      "body": "2-3 sentences explaining this point. Specific. Actionable.",
      "icon_suggestion": "emoji representing this point"
    }}
  ],
  "slide_final_cta": "Call to action text for last slide",
  "caption": "Full Instagram caption, 150-200 words. First line = hook. Include line breaks. End with a question.",
  "alt_text": "Accessibility description of the carousel content"
}}

Rules:
- Exactly 7-8 slides total (including hook and CTA)
- Every point must be SPECIFIC, not generic
- Use numbers and data where possible
- Write at 8th grade reading level
- No clichés like "game-changer" or "in today's world"
"""
        return generate_text(
            prompt,
            system=f"Expert Instagram content creator for the {self.niche} niche. Return only valid JSON.",
            json_response=True,
            temperature=0.7,
        )

    def generate_reel_script(self, idea):
        prompt = f"""Create a complete Instagram Reel script.

IDEA: {idea['hook']}
OUTLINE: {json.dumps(idea['outline']) if isinstance(idea['outline'], list) else idea['outline']}
BRAND VOICE: {self.brand_voice}

Generate exactly this JSON structure:
{{
  "duration_seconds": 30,
  "hook_text_overlay": "On-screen text for first 2 seconds (max 8 words)",
  "hook_voiceover": "What to say in first 2 seconds",
  "segments": [
    {{
      "timestamp": "3-10s",
      "text_overlay": "On-screen text",
      "voiceover": "What to say",
      "visual_suggestion": "What to show on screen"
    }}
  ],
  "cta_text": "Final on-screen text",
  "cta_voiceover": "Final spoken words",
  "caption": "Full caption for the reel, 100-150 words",
  "hashtags": ["list", "of", "8", "hashtags"]
}}
"""
        return generate_text(
            prompt,
            system=f"Expert reel scriptwriter for {self.niche}. Return valid JSON only.",
            json_response=True,
            temperature=0.7,
        )

    def generate_content(self, idea):
        if idea["content_type"] == "reel":
            return self.generate_reel_script(idea)
        return self.generate_carousel(idea)

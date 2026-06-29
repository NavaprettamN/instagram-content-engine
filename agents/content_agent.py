import json
from agents._llm import generate_text


class ContentAgent:
    def __init__(self, config):
        self.brand_voice = config["brand_voice"]
        self.niche = config["niche"]
        self.handle = config.get("instagram_handle", "")
        self.affiliate_tools = [t.get("name", "") for t in config.get("affiliate", {}).get("tools", [])]

    def generate_carousel(self, idea):
        affiliate = ""
        if self.affiliate_tools:
            affiliate = (
                f"\nMONETIZATION: If any of these tools we recommend is GENUINELY relevant to "
                f"this topic, mention it naturally in the content and add a soft CTA in the "
                f"caption like 'I use [tool] for this — link in bio 🔗'. Never force it. "
                f"Tools: {', '.join(self.affiliate_tools)}\n"
            )
        prompt = f"""Create a complete Instagram carousel post.

IDEA: {idea['hook']}
OUTLINE: {json.dumps(idea['outline']) if isinstance(idea['outline'], list) else idea['outline']}

BRAND VOICE: {self.brand_voice}
{affiliate}

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
  "caption": "Full Instagram caption, 150-200 words. Structure: (1) first line = a scroll-stopping hook, (2) the value/body with line breaks, (3) a save/share CTA like 'Save this for later 📌' or 'Send this to someone who needs it', (4) a follow CTA, (5) end with a question that invites comments.",
  "alt_text": "Accessibility description of the carousel content"
}}

Rules:
- Exactly 7-8 slides total (including hook and CTA)
- Every point must be SPECIFIC, not generic
- Use numbers and data where possible
- Write at 8th grade reading level
- No clichés like "game-changer" or "in today's world"
- Optimize for SAVES and SHARES (the strongest reach signals): make the content reference-worthy and worth sending to a friend
- In the follow CTA, use the EXACT handle {self.handle} — never a placeholder like "@[YourHandle]"
"""
        result = generate_text(
            prompt,
            system=f"Expert Instagram content creator for the {self.niche} niche. Return only valid JSON.",
            json_response=True,
            temperature=0.7,
        )
        # belt-and-suspenders: scrub any placeholder handle the model leaves behind
        if isinstance(result, dict) and result.get("caption") and self.handle:
            for ph in ("@[YourHandle]", "[YourHandle]", "@YourHandle", "[your handle]", "@[handle]"):
                result["caption"] = result["caption"].replace(ph, self.handle)
        return result

    def generate_voice_script(self, idea):
        """Original voiceover reel: {hook (top title), script (narration), caption}."""
        affiliate = ""
        if self.affiliate_tools:
            affiliate = (f"\nIf one of these tools we recommend is genuinely relevant, name it "
                         f"naturally in the script and add 'link in bio' to the caption (never force "
                         f"it): {', '.join(self.affiliate_tools)}\n")
        result = generate_text(
            f"""Create a 35-45 second Instagram REEL about {self.niche}.

IDEA: {idea['hook']}
OUTLINE: {json.dumps(idea['outline']) if isinstance(idea['outline'], list) else idea['outline']}
BRAND VOICE: {self.brand_voice}
{affiliate}
Return JSON:
{{
  "hook": "3-6 word on-screen title — punchy, scroll-stopping",
  "script": "The spoken narration as ONE flowing voiceover. HARD LIMIT 80 words (~30 seconds) — count them. First 3 seconds MUST be a pattern-interrupt hook. Specific, valuable, energetic, very short sentences. End with a verbal 'follow for more' CTA. NO emojis, NO hashtags, NO stage directions, NO markdown, NO quotes — only the words spoken aloud.",
  "b_roll_terms": ["4-6 CONCRETE stock-footage search phrases, in script order, that visually match the narration beats. Use filmable nouns + action, NOT abstract concepts. Good: 'person typing on laptop', 'glowing AI robot face', 'city street timelapse night', 'data charts on screen', 'hands using smartphone'. Bad: 'productivity', 'success', 'innovation'."],
  "caption": "Instagram caption: hook line, brief value, a save/share CTA, a question, and a follow CTA using {self.handle}."
}}
Rules: the script must sound natural read aloud; use numbers/specifics over fluff.""",
            system=f"Expert short-form video scriptwriter for {self.niche}. Return only valid JSON.",
            json_response=True, temperature=0.7,
        )
        if isinstance(result, dict) and result.get("caption") and self.handle:
            for ph in ("@[YourHandle]", "[YourHandle]", "@YourHandle", "[your handle]"):
                result["caption"] = result["caption"].replace(ph, self.handle)
        return result

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

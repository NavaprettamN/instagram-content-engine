# content_agent.py

class ContentAgent:
    def __init__(self, config):
        self.client = AzureOpenAI(
            api_key=config["azure_api_key"],
            api_version="2024-02-15-preview",
            azure_endpoint=config["azure_endpoint"]
        )
        self.brand_voice = config["brand_voice"]
        self.niche = config["niche"]
        self.db_path = config["db_path"]
    
    def generate_carousel(self, idea):
        """Generate full carousel content from an approved idea"""
        
        prompt = f"""Create a complete Instagram carousel post.

IDEA: {idea['hook']}
OUTLINE: {json.dumps(idea['outline'])}

BRAND VOICE: {self.brand_voice}

Generate exactly this structure:
{{
  "slide_1_hook": "Bold headline, max 8 words, creates curiosity",
  "slide_1_subtext": "One line teaser, max 15 words",
  "slides": [
    {{
      "slide_number": 2,
      "headline": "Bold point, max 6 words",
      "body": "2-3 sentences explaining this point. Specific. Actionable.",
      "icon_suggestion": "emoji that represents this point"
    }}
    // ... slides 2 through 7
  ],
  "slide_final_cta": "Call to action text for last slide",
  "caption": "Full Instagram caption, 150-200 words. 
              First line = hook. 
              Include line breaks. 
              End with a question. 
              Include 8 hashtags at the end.",
  "alt_text": "Accessibility description of the carousel content"
}}

Rules:
- Exactly 7-8 slides total (including hook and CTA)
- Every point must be SPECIFIC, not generic
- Use numbers and data where possible
- Write at 8th grade reading level
- No clichés like "game-changer" or "in today's world"
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an expert Instagram content creator for the {self.niche} niche. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        content = json.loads(response.choices[0].message.content)
        return content
    
    def generate_reel_script(self, idea):
        """Generate a complete reel script"""
        
        prompt = f"""Create a complete Instagram Reel script.

IDEA: {idea['hook']}
OUTLINE: {json.dumps(idea['outline'])}
BRAND VOICE: {self.brand_voice}

Generate exactly this structure:
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
  "suggested_audio_style": "trending audio type suggestion",
  "hashtags": ["list", "of", "8", "hashtags"]
}}
"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Expert reel scriptwriter for {self.niche}. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def generate_content(self, idea):
        """Route to the right generator based on content type"""
        if idea["content_type"] == "carousel":
            return self.generate_carousel(idea)
        elif idea["content_type"] == "reel":
            return self.generate_reel_script(idea)
        else:
            return self.generate_carousel(idea)  # Default to carousel
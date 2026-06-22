import json
from agents._llm import generate_text


class HashtagAgent:
    def __init__(self, config):
        self.niche = config["niche"]

    def generate_hashtag_sets(self, content_topic, num_sets=3):
        prompt = f"""Generate {num_sets} different hashtag sets for an Instagram post about "{content_topic}" in the {self.niche} niche.

Each set should have exactly 8 hashtags:
- 2 high-volume (500K+ posts — broad discovery)
- 3 medium-volume (50K-500K — niche relevant)
- 3 low-volume (5K-50K — specific, less competition)

Rules:
- Never include banned or restricted hashtags
- Never include #followforfollow or similar spam hashtags
- Every hashtag must be directly relevant to the content

Return as JSON:
{{
  "sets": [
    {{
      "set_id": 1,
      "hashtags": ["#tag1", "#tag2"],
      "volume_breakdown": "2 high / 3 mid / 3 low"
    }}
  ]
}}"""

        return generate_text(
            prompt,
            system="Instagram hashtag strategist. Return valid JSON.",
            json_response=True,
            temperature=0.6,
        )

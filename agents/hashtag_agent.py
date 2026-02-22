# hashtag_agent.py

class HashtagAgent:
    def __init__(self, config):
        self.client = AzureOpenAI(
            api_key=config["azure_api_key"],
            api_version="2024-02-15-preview",
            azure_endpoint=config["azure_endpoint"]
        )
        self.niche = config["niche"]
        self.db_path = config["db_path"]
    
    def generate_hashtag_sets(self, content_topic, num_sets=3):
        """Generate rotating hashtag sets for a topic"""
        
        prompt = f"""Generate {num_sets} different hashtag sets for an 
Instagram post about "{content_topic}" in the {self.niche} niche.

Each set should have exactly 8 hashtags:
- 2 high-volume (500K+ posts — broad discovery)
- 3 medium-volume (50K-500K — niche relevant)
- 3 low-volume (5K-50K — specific, less competition)

Rules:
- Never include banned or restricted hashtags
- Never include #followforfollow or similar spam hashtags
- Every hashtag must be directly relevant to the content
- Mix English hashtags (if audience is English-speaking)

Return as JSON:
{{
  "sets": [
    {{
      "set_id": 1,
      "hashtags": ["#tag1", "#tag2", ...],
      "volume_breakdown": "2 high / 3 mid / 3 low"
    }}
  ]
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Instagram hashtag strategist. Return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
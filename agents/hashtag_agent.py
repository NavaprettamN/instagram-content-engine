import json
from agents._llm import generate_text


def pick_hashtags(stored, rotation=0):
    """Flat list of hashtags from a stored value, handling both shapes:
    the 3-set JSON from generate_hashtag_sets, or research's flat list (fallback)."""
    if isinstance(stored, str):
        try:
            stored = json.loads(stored)
        except (ValueError, TypeError):
            return []
    if isinstance(stored, dict) and stored.get("sets"):
        sets = stored["sets"]
        return sets[rotation % len(sets)].get("hashtags", [])
    if isinstance(stored, list):
        return stored
    return []


def compose_caption(post, rotation=0):
    """caption_draft + a rotated hashtag set appended. Rotation (e.g. published count)
    varies the set per post so Instagram doesn't flag a repeated hashtag block."""
    caption = (post.get("caption_draft") or "").strip()
    tags = pick_hashtags(post.get("hashtags"), rotation)
    return f"{caption}\n\n{' '.join(tags)}".strip() if tags else caption


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


if __name__ == "__main__":
    # self-check for the shape-handling + rotation logic (no API calls)
    sets = {"sets": [{"hashtags": ["#a"]}, {"hashtags": ["#b"]}, {"hashtags": ["#c"]}]}
    assert pick_hashtags(sets, 0) == ["#a"]
    assert pick_hashtags(sets, 4) == ["#b"]           # rotation wraps (4 % 3 = 1)
    assert pick_hashtags(json.dumps(sets), 2) == ["#c"]  # JSON string shape
    assert pick_hashtags(["#x", "#y"]) == ["#x", "#y"]   # flat-list fallback
    assert pick_hashtags(None) == [] and pick_hashtags("not json") == []
    assert compose_caption({"caption_draft": "hi", "hashtags": sets}, 0) == "hi\n\n#a"
    assert compose_caption({"caption_draft": "hi", "hashtags": None}, 0) == "hi"
    print("hashtag_agent self-check OK")

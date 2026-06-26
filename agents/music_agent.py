"""Pick a mood-matching, copyright-safe instrumental for a reel and bake it in.

Uses the Jamendo API (free client_id, Creative-Commons catalog). Instrumental
tracks only — they sit under text/voiceover without clashing. Returns the track
plus a credit string (CC licenses need attribution; we append it to the caption).

Degrades to None (silent reel) if JAMENDO_CLIENT_ID is unset, no track matches,
or the API fails — music is an enhancement, never a hard dependency.

Note: this is NOT Instagram's in-app trending audio (API-impossible). It's
licensed music embedded in the MP4 — copyright-safe and won't get muted.
"""
import os
import requests
from agents._llm import generate_text

BASE = "https://api.jamendo.com/v3.0/tracks/"
# Jamendo ANDs multiple tags, so we query ONE mood tag at a time. These are all
# real, well-populated Jamendo mood tags — keeps the LLM from inventing misses.
MOODS = ["upbeat", "energetic", "happy", "inspiring", "motivational",
         "corporate", "calm", "relaxing", "epic", "uplifting", "chill"]


class MusicAgent:
    def __init__(self, config):
        self.client_id = os.environ.get("JAMENDO_CLIENT_ID")
        self.default_tag = config.get("reel_music_tags", "upbeat").split(",")[0].strip()

    def _mood_tag(self, hook):
        """One cheap LLM call -> a single mood tag from MOODS; fall back to default."""
        try:
            raw = generate_text(
                f'Pick the ONE best-fitting instrumental-music mood for an Instagram '
                f'reel titled: "{hook}". Choose from exactly this list: {", ".join(MOODS)}. '
                f'Return only the single word.',
                temperature=0.3,
            ).strip().lower()
            return raw if raw in MOODS else self.default_tag
        except Exception:
            return self.default_tag

    def _query(self, tags):
        """Return the top downloadable instrumental for a tag, or None."""
        params = {"client_id": self.client_id, "format": "json", "limit": 1,
                  "audioformat": "mp32", "vocalinstrumental": "instrumental",
                  "order": "popularity_total", "audiodownload_allowed": "true"}
        if tags:
            params["tags"] = tags
        r = requests.get(BASE, params=params, timeout=20)
        r.raise_for_status()
        results = r.json().get("results", [])
        return results[0] if results else None

    def pick_track(self, hook, out_path):
        """Download a mood-matching CC instrumental. Returns {'path','credit'} or None."""
        if not self.client_id:
            return None
        try:
            # progressively relax: LLM mood -> default mood -> any instrumental
            for tags in (self._mood_tag(hook), self.default_tag, ""):
                t = self._query(tags)
                if t:
                    break
            audio_url = t.get("audiodownload") or t.get("audio") if t else None
            if not audio_url:
                return None
            data = requests.get(audio_url, timeout=60).content
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(data)
            credit = f"🎵 {t.get('name')} by {t.get('artist_name')} (Jamendo, CC)"
            return {"path": out_path, "credit": credit}
        except Exception as e:
            print(f"MusicAgent: {e}")
            return None


if __name__ == "__main__":
    import yaml
    config = yaml.safe_load(open("config.yaml"))
    agent = MusicAgent(config)
    if not agent.client_id:
        # no-key contract: must return None, never raise
        assert agent.pick_track("Test reel", "/tmp/should_not_exist.mp3") is None
        assert not os.path.exists("/tmp/should_not_exist.mp3")
        print("music_agent self-check OK (no JAMENDO_CLIENT_ID -> silent reel)")
    else:
        res = agent.pick_track("5 AI tools to work smarter", "/tmp/music_selfcheck.mp3")
        assert res and os.path.getsize(res["path"]) > 50_000, res
        print(f"music_agent self-check OK -> {res['credit']} ({os.path.getsize(res['path'])} bytes)")

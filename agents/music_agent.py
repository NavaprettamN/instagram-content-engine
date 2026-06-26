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


class MusicAgent:
    def __init__(self, config):
        self.client_id = os.environ.get("JAMENDO_CLIENT_ID")
        self.default_tags = config.get("reel_music_tags", "upbeat,corporate")

    def _mood_tags(self, hook):
        """One cheap LLM call -> 2 Jamendo mood tags; fall back to config default."""
        try:
            raw = generate_text(
                f'Pick exactly 2 instrumental-music mood tags (comma-separated, '
                f'lowercase single words such as upbeat, calm, inspiring, corporate, '
                f'energetic) that fit an Instagram reel titled: "{hook}". '
                f'Return ONLY the two tags.',
                temperature=0.3,
            )
            tags = ",".join(t.strip().lower() for t in raw.replace("\n", " ").split(",")[:2] if t.strip())
            return tags or self.default_tags
        except Exception:
            return self.default_tags

    def pick_track(self, hook, out_path):
        """Download a mood-matching CC instrumental. Returns {'path','credit'} or None."""
        if not self.client_id:
            return None
        try:
            r = requests.get(BASE, params={
                "client_id": self.client_id, "format": "json", "limit": 1,
                "tags": self._mood_tags(hook), "audioformat": "mp32",
                "vocalinstrumental": "instrumental", "order": "popularity_total",
                "audiodownload_allowed": "true",
            }, timeout=20)
            r.raise_for_status()
            results = r.json().get("results", [])
            if not results:
                return None
            t = results[0]
            audio_url = t.get("audiodownload") or t.get("audio")
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

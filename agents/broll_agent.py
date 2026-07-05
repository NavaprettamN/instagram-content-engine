"""Free stock footage for reels via the Pexels Video API (free key, no card).

fetch_clips(terms) downloads one portrait-ish MP4 per search term so voice_reel
can lay them behind the captions. Everything is best-effort: no key, a failed
search, or a failed download just yields fewer/zero clips and the caller falls
back to a solid background. Clips are cached by (term, quality) to spare the API
and Actions bandwidth.
"""
import os
import re
import requests

PEXELS_VIDEO_SEARCH = "https://api.pexels.com/videos/search"


class BRollAgent:
    def __init__(self, config=None):
        self.key = os.environ.get("PEXELS_API_KEY")
        cache = (config or {}).get("output_dir", "./generated_content")
        self.cache_dir = os.path.join(cache, "broll_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    @property
    def enabled(self):
        return bool(self.key)

    def _slug(self, term):
        return re.sub(r"[^a-z0-9]+", "_", term.lower()).strip("_")[:40]

    def _best_portrait_file(self, video):
        """Pick the smallest video file that is >=1080 wide (portrait preferred)."""
        files = video.get("video_files", [])
        portrait = [f for f in files if (f.get("height") or 0) >= (f.get("width") or 0)]
        pool = portrait or files
        # prefer ~1080p, ascending by area so downloads stay small
        pool = [f for f in pool if (f.get("width") or 0) >= 1080] or pool
        pool.sort(key=lambda f: (f.get("width") or 0) * (f.get("height") or 0))
        return pool[0]["link"] if pool else None

    def fetch_one(self, term, min_seconds=4, variant=0):
        """Download a single clip for `term`. Returns a local path or None.

        `variant` rotates which search result gets used, so the same term on a
        different idea yields different footage instead of Pexels' #1 forever.
        """
        if not self.enabled:
            return None
        dest = os.path.join(self.cache_dir, f"{self._slug(term)}_{variant % 10}.mp4")
        if os.path.exists(dest) and os.path.getsize(dest) > 10_000:
            return dest
        try:
            r = requests.get(
                PEXELS_VIDEO_SEARCH,
                headers={"Authorization": self.key},
                params={"query": term, "orientation": "portrait",
                        "per_page": 10, "size": "medium"},
                timeout=20,
            )
            r.raise_for_status()
            vids = [v for v in r.json().get("videos", [])
                    if (v.get("duration") or 0) >= min_seconds]
            if vids:  # rotate start point; keep the rest as fallback order
                i = variant % len(vids)
                vids = vids[i:] + vids[:i]
            for v in vids:
                link = self._best_portrait_file(v)
                if not link:
                    continue
                vr = requests.get(link, timeout=60)
                vr.raise_for_status()
                with open(dest, "wb") as f:
                    f.write(vr.content)
                return dest
        except Exception as e:  # best-effort: never break the reel run
            print(f"BRollAgent: '{term}' failed ({e})")
        return None

    def fetch_clips(self, terms, limit=6, variant=0):
        """Return downloaded clip paths for the given search terms (in order)."""
        paths = []
        for t in (terms or [])[:limit]:
            p = self.fetch_one(t, variant=variant)
            if p:
                paths.append(p)
        return paths


if __name__ == "__main__":
    # ponytail: smoke check — needs PEXELS_API_KEY to actually fetch; without it,
    # asserts the graceful no-key path so CI/local without the key still passes.
    a = BRollAgent({"output_dir": "/tmp/broll_demo"})
    if a.enabled:
        clips = a.fetch_clips(["person typing on laptop", "city timelapse night"])
        print("fetched", clips)
        assert clips, "expected at least one clip with a valid key"
    else:
        assert a.fetch_clips(["anything"]) == [], "no key must yield no clips"
        print("no PEXELS_API_KEY — graceful empty path OK")

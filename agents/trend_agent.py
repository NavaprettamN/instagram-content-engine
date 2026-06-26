"""Pull what's trending across platforms to feed the research agent.

Every source is wrapped so a failure (quota, rate-limit, blocked scrape) returns
[] instead of breaking the run — trends are a bonus signal, never a hard dep.
YouTube uses the official Data API (free, 10k units/day). Google Trends uses
pytrends (unofficial, often 429s). TikTok has no free official API, so it's a
best-effort scrape that is usually empty in CI — that's expected.
"""
import os
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()


class TrendAgent:
    def __init__(self, config):
        self.config = config
        self.keywords = config.get("keywords", [])
        self.region = config.get("trend_region", "US")
        self.yt_key = os.environ.get("YOUTUBE_API_KEY")

    def youtube_trending(self, per_keyword=5):
        """Top recently-popular video titles for the niche keywords."""
        if not self.yt_key:
            return []
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        titles = []
        for kw in self.keywords[:5]:
            try:
                r = requests.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "key": self.yt_key, "part": "snippet", "q": kw,
                        "type": "video", "order": "viewCount", "publishedAfter": since,
                        "maxResults": per_keyword, "regionCode": self.region,
                        "relevanceLanguage": "en",
                    }, timeout=15,
                )
                r.raise_for_status()
                titles += [it["snippet"]["title"] for it in r.json().get("items", [])]
            except Exception as e:
                print(f"TrendAgent youtube '{kw}': {e}")
        return titles

    def google_trends(self):
        """Rising related queries for the niche keywords (pytrends)."""
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl="en-US", tz=0)
            pytrends.build_payload(self.keywords[:5], timeframe="now 7-d")
            rising = []
            for kw, data in (pytrends.related_queries() or {}).items():
                top = (data or {}).get("rising")
                if top is not None:
                    rising += top["query"].head(5).tolist()
            return rising
        except Exception as e:
            print(f"TrendAgent google_trends: {e}")
            return []

    def tiktok_trending(self):
        """Best-effort TikTok signal. No free official API — usually [] in CI."""
        try:
            tag = (self.keywords[0] if self.keywords else "ai").replace(" ", "")
            r = requests.get(
                f"https://www.tiktok.com/api/challenge/detail/?challengeName={tag}",
                headers={"User-Agent": "Mozilla/5.0"}, timeout=10,
            )
            if r.ok and r.text.strip():
                title = r.json().get("challengeInfo", {}).get("challenge", {}).get("title")
                return [f"#{title}"] if title else []
        except Exception as e:
            print(f"TrendAgent tiktok (best-effort): {e}")
        return []

    def gather_trends(self):
        """{source: [titles/queries]} — each list is [] if that source failed."""
        return {
            "youtube_trending": self.youtube_trending(),
            "google_trends_rising": self.google_trends(),
            "tiktok_trending": self.tiktok_trending(),
        }


if __name__ == "__main__":
    import yaml
    config = yaml.safe_load(open("config.yaml"))
    trends = TrendAgent(config).gather_trends()
    # contract: always a dict of lists, never raises, even with no key/network
    assert isinstance(trends, dict)
    assert all(isinstance(v, list) for v in trends.values()), trends
    for src, items in trends.items():
        print(f"{src}: {len(items)}")
        for t in items[:3]:
            print(f"   - {t}")
    print("trend_agent self-check OK")

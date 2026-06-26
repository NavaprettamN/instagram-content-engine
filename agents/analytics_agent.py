import os
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict
from agents._llm import generate_text
from agents._db import save_analytics, set_config

load_dotenv()


class AnalyticsAgent:
    def __init__(self, config):
        self.access_token = os.environ["META_ACCESS_TOKEN"]
        self.ig_user_id = os.environ["INSTAGRAM_USER_ID"]
        # Instagram API with Instagram Login. Note: insights metric names differ
        # from the old Graph API — adjust get_*_insights if those calls error.
        self.base_url = "https://graph.instagram.com/v21.0"

    def get_account_insights(self, period="day", days=7):
        metrics = "impressions,reach,follower_count,profile_views"
        resp = requests.get(
            f"{self.base_url}/{self.ig_user_id}/insights",
            params={
                "metric": metrics,
                "period": period,
                "since": int(time.time()) - (days * 86400),
                "until": int(time.time()),
                "access_token": self.access_token,
            },
        )
        return resp.json()

    def get_post_insights(self, media_id):
        metrics = "impressions,reach,engagement,saved,shares"
        resp = requests.get(
            f"{self.base_url}/{media_id}/insights",
            params={"metric": metrics, "access_token": self.access_token},
        )
        return resp.json()

    def get_recent_posts(self, limit=25):
        resp = requests.get(
            f"{self.base_url}/{self.ig_user_id}/media",
            params={
                "fields": "id,caption,timestamp,like_count,comments_count,media_type,permalink",
                "limit": limit,
                "access_token": self.access_token,
            },
        )
        return resp.json()

    def best_posting_hours(self, top_n=3, min_posts=20):
        """Top UTC hours by avg engagement, rounded to even hours (publish.yml's
        2h cadence). Returns [] until min_posts exist — too little data is noise."""
        posts = self.get_recent_posts(limit=50)
        data = posts.get("data", []) if isinstance(posts, dict) else (posts or [])
        eng = defaultdict(list)
        for p in data:
            ts = p.get("timestamp")
            if not ts:
                continue
            try:
                hour = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").hour
            except ValueError:
                continue
            eng[hour].append((p.get("like_count") or 0) + (p.get("comments_count") or 0))
        if sum(len(v) for v in eng.values()) < min_posts:
            return []
        ranked = sorted(eng, key=lambda h: sum(eng[h]) / len(eng[h]), reverse=True)
        even = []
        for h in ranked:
            eh = h - (h % 2)  # map to even hour for the 2h cron
            if eh not in even:
                even.append(eh)
            if len(even) >= top_n:
                break
        return even

    def generate_weekly_analysis(self, insights_data, posts_data):
        prompt = f"""Analyze this Instagram account's weekly performance:

ACCOUNT INSIGHTS:
{json.dumps(insights_data, indent=2)}

RECENT POSTS PERFORMANCE:
{json.dumps(posts_data, indent=2)}

Provide:
1. Top 3 performing posts and WHY they worked (format, topic, timing)
2. Bottom 3 performing posts and WHY they underperformed
3. Engagement rate trend (improving/declining/stable)
4. 5 specific, actionable recommendations for next week
5. Content types to double down on
6. Best posting times based on this data

Be specific. Use numbers. No vague advice."""

        return generate_text(
            prompt,
            system="Instagram analytics expert. Be data-driven and specific.",
            temperature=0.3,
        )

    def run(self):
        print("Analytics Agent: Pulling metrics...")
        insights = self.get_account_insights()
        posts = self.get_recent_posts()

        print("Analytics Agent: Generating analysis...")
        analysis = self.generate_weekly_analysis(insights, posts)

        save_analytics({
            "date": datetime.utcnow().date().isoformat(),
            "analysis": analysis,
        })

        # Best-time optimizer: store top hours for publish.yml's adaptive gate.
        hours = self.best_posting_hours()
        if hours:
            set_config("best_hours", json.dumps(hours))
            print(f"Analytics Agent: best posting hours (UTC) -> {hours}")
        else:
            print("Analytics Agent: not enough post data yet for best-hours (using fallback slots)")

        print("Analytics Agent: Done.")
        return analysis

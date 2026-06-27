import os
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict
from agents._llm import generate_text
from agents._db import save_analytics, set_config, get_config

# Valid media-insight metrics on graph.instagram.com (Instagram-Login API).
# The old Graph API names (impressions, engagement) are rejected here.
POST_METRICS = "reach,likes,comments,saved,shares,total_interactions"

load_dotenv()


class AnalyticsAgent:
    def __init__(self, config):
        self.access_token = os.environ["META_ACCESS_TOKEN"]
        self.ig_user_id = os.environ["INSTAGRAM_USER_ID"]
        # Instagram API with Instagram Login. Note: insights metric names differ
        # from the old Graph API — adjust get_*_insights if those calls error.
        self.base_url = "https://graph.instagram.com/v21.0"

    def account_summary(self):
        """Followers + media count (the reliable account-level fields)."""
        r = requests.get(
            f"{self.base_url}/{self.ig_user_id}",
            params={"fields": "followers_count,media_count", "access_token": self.access_token},
            timeout=15,
        )
        return r.json()

    def get_post_insights(self, media_id):
        """{metric: value} for one post, or {} on error."""
        r = requests.get(
            f"{self.base_url}/{media_id}/insights",
            params={"metric": POST_METRICS, "access_token": self.access_token}, timeout=15,
        )
        data = r.json().get("data", [])
        return {d["name"]: (d.get("values", [{}])[0].get("value") or 0) for d in data}

    def post_performance(self, limit=30):
        """Per published post: metadata + insights + engagement rate + a reach-
        weighted score (saves/shares/comments matter most). Newest first."""
        posts = self.get_recent_posts(limit=limit)
        data = posts.get("data", []) if isinstance(posts, dict) else (posts or [])
        out = []
        for p in data:
            ins = self.get_post_insights(p["id"])
            reach = ins.get("reach", 0) or 0
            inter = ins.get("total_interactions", 0) or 0
            saved, shares = ins.get("saved", 0), ins.get("shares", 0)
            comments, likes = ins.get("comments", 0), ins.get("likes", 0)
            out.append({
                "id": p["id"], "permalink": p.get("permalink"),
                "caption": (p.get("caption") or "").split("\n")[0][:70],
                "type": p.get("media_type", ""), "timestamp": p.get("timestamp", ""),
                "reach": reach, "likes": likes, "comments": comments,
                "saved": saved, "shares": shares, "interactions": inter,
                "eng_rate": round(100 * inter / reach, 1) if reach else 0.0,
                # reach signals weighted: saves & shares > comments > likes
                "score": saved * 3 + shares * 3 + comments * 2 + likes,
            })
        return out

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
        summary = self.account_summary()
        perf = self.post_performance()
        today = datetime.utcnow().date().isoformat()

        print("Analytics Agent: Generating analysis...")
        analysis = self.generate_weekly_analysis(summary, perf)
        save_analytics({"date": today, "analysis": analysis})

        # Feed concrete winners back into research (#7): the top-scoring posts.
        top = sorted(perf, key=lambda p: p["score"], reverse=True)[:3]
        if any(t["score"] for t in top):
            set_config("top_performers", json.dumps(
                [{"hook": t["caption"], "type": t["type"], "score": t["score"],
                  "saved": t["saved"], "shares": t["shares"]} for t in top]))

        # Follower-growth trend (config history — no schema change).
        fc = summary.get("followers_count")
        if fc is not None:
            hist = json.loads(get_config("follower_history") or "[]")
            if not hist or hist[-1].get("date") != today:
                hist.append({"date": today, "count": fc})
                set_config("follower_history", json.dumps(hist[-90:]))
            print(f"Analytics Agent: followers = {fc}")

        # Best-time optimizer: store top hours for publish.yml's adaptive gate.
        hours = self.best_posting_hours()
        if hours:
            set_config("best_hours", json.dumps(hours))
            print(f"Analytics Agent: best posting hours (UTC) -> {hours}")
        else:
            print("Analytics Agent: not enough post data yet for best-hours (using fallback slots)")

        print("Analytics Agent: Done.")
        return analysis

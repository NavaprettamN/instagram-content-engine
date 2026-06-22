import os
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from agents._llm import generate_text
from agents._db import save_analytics

load_dotenv()


class AnalyticsAgent:
    def __init__(self, config):
        self.access_token = os.environ["META_ACCESS_TOKEN"]
        self.ig_user_id = os.environ["INSTAGRAM_USER_ID"]
        self.base_url = "https://graph.facebook.com/v19.0"

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
        print("Analytics Agent: Done.")
        return analysis

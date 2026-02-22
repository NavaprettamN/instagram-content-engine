# analytics_agent.py

class AnalyticsAgent:
    def __init__(self, config):
        self.access_token = config["meta_access_token"]
        self.ig_user_id = config["instagram_user_id"]
        self.client = AzureOpenAI(
            api_key=config["azure_api_key"],
            api_version="2024-02-15-preview",
            azure_endpoint=config["azure_endpoint"]
        )
        self.base_url = "https://graph.facebook.com/v19.0"
    
    def get_account_insights(self, period="day", days=7):
        """Pull account-level metrics"""
        metrics = "impressions,reach,follower_count,profile_views"
        resp = requests.get(
            f"{self.base_url}/{self.ig_user_id}/insights",
            params={
                "metric": metrics,
                "period": period,
                "since": int(time.time()) - (days * 86400),
                "until": int(time.time()),
                "access_token": self.access_token
            }
        )
        return resp.json()
    
    def get_post_insights(self, media_id):
        """Pull post-level metrics"""
        metrics = "impressions,reach,engagement,saved,shares"
        resp = requests.get(
            f"{self.base_url}/{media_id}/insights",
            params={
                "metric": metrics,
                "access_token": self.access_token
            }
        )
        return resp.json()
    
    def get_recent_posts(self, limit=25):
        """Get recent posts with their metrics"""
        resp = requests.get(
            f"{self.base_url}/{self.ig_user_id}/media",
            params={
                "fields": "id,caption,timestamp,like_count,comments_count,"
                          "media_type,permalink",
                "limit": limit,
                "access_token": self.access_token
            }
        )
        return resp.json()
    
    def generate_weekly_analysis(self, insights_data, posts_data):
        """Use AI to analyze performance and suggest improvements"""
        
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
6. Content types to stop or change
7. Best posting times based on this data
8. Predicted follower growth for next week

Be specific. Use numbers. No vague advice."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an Instagram analytics expert. Be data-driven and specific."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
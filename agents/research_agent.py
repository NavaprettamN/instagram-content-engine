# research_agent.py

import feedparser
import requests
from datetime import datetime
from openai import AzureOpenAI
import json
import sqlite3

class ResearchAgent:
    def __init__(self, config):
        self.client = AzureOpenAI(
            api_key=config["azure_api_key"],
            api_version="2024-02-15-preview",
            azure_endpoint=config["azure_endpoint"]
        )
        self.niche = config["niche"]
        self.keywords = config["keywords"]
        self.rss_feeds = config["rss_feeds"]
        self.db_path = config["db_path"]
    
    def gather_trends(self):
        """Pull trending content from RSS feeds and news sources"""
        all_articles = []
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    all_articles.append({
                        "title": entry.title,
                        "summary": entry.get("summary", "")[:500],
                        "link": entry.link,
                        "published": entry.get("published", ""),
                        "source": feed_url
                    })
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
        return all_articles
    
    def gather_reddit_ideas(self):
        """Pull top posts from niche subreddits (no auth needed for .json)"""
        ideas = []
        subreddits = self.config.get("subreddits", [])
        for sub in subreddits:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
                headers = {"User-Agent": "ContentResearchBot/1.0"}
                resp = requests.get(url, headers=headers)
                data = resp.json()
                for post in data["data"]["children"]:
                    p = post["data"]
                    if p["score"] > 50:  # Only popular posts
                        ideas.append({
                            "title": p["title"],
                            "score": p["score"],
                            "num_comments": p["num_comments"],
                            "subreddit": sub,
                            "url": f"https://reddit.com{p['permalink']}"
                        })
            except Exception as e:
                print(f"Error fetching r/{sub}: {e}")
        return ideas
    
    def generate_content_ideas(self, trends, reddit_ideas):
        """Use Azure OpenAI to turn raw research into content ideas"""
        
        research_summary = json.dumps({
            "trending_articles": trends[:10],
            "popular_reddit_posts": reddit_ideas[:10]
        }, indent=2)
        
        prompt = f"""You are a content strategist for an Instagram page 
about {self.niche}.

Here is today's research from trending articles and Reddit:

{research_summary}

Based on this research AND your own knowledge, generate exactly 5 
Instagram content ideas. For each idea provide:

1. content_type: "carousel" or "reel" or "static_image"
2. hook: The first line/headline (max 10 words, must stop scrollers)
3. outline: 3-5 bullet points of what the content covers
4. caption_draft: A full Instagram caption (150-200 words)
5. why_now: Why this topic is timely or relevant today
6. estimated_engagement: "high" / "medium" / "low" with reasoning
7. hashtags: 8 relevant hashtags

Return as a JSON array. Prioritize ideas with HIGH engagement potential.
Avoid generic advice. Every tip must be specific and actionable."""

        response = self.client.chat.completions.create(
            model="gpt-4o",  # or your deployed model name
            messages=[
                {"role": "system", "content": "You are an expert Instagram content strategist. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        
        ideas = json.loads(response.choices[0].message.content)
        return ideas
    
    def save_ideas_to_db(self, ideas):
        """Save generated ideas to SQLite for the dashboard to display"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for idea in ideas.get("ideas", ideas):
            cursor.execute("""
                INSERT INTO content_ideas 
                (content_type, hook, outline, caption_draft, hashtags, 
                 status, created_at, engagement_estimate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                idea["content_type"],
                idea["hook"],
                json.dumps(idea["outline"]),
                idea["caption_draft"],
                json.dumps(idea["hashtags"]),
                "pending_review",  # Human must approve
                datetime.now().isoformat(),
                idea.get("estimated_engagement", "medium")
            ))
        
        conn.commit()
        conn.close()
    
    def run(self):
        """Execute the full research pipeline"""
        print("🔍 Research Agent: Gathering trends...")
        trends = self.gather_trends()
        reddit = self.gather_reddit_ideas()
        
        print("🧠 Research Agent: Generating content ideas...")
        ideas = self.generate_content_ideas(trends, reddit)
        
        print("💾 Research Agent: Saving to database...")
        self.save_ideas_to_db(ideas)
        
        print(f"✅ Research Agent: {len(ideas)} new ideas added to review queue")
        return ideas
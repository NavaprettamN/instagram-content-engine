import feedparser
import requests
import json
from datetime import datetime
from agents._llm import generate_text
from agents._db import save_idea


class ResearchAgent:
    def __init__(self, config):
        self.config = config
        self.niche = config["niche"]
        self.keywords = config["keywords"]
        self.rss_feeds = config["rss_feeds"]

    def gather_trends(self):
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
                        "source": feed_url,
                    })
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
        return all_articles

    def gather_reddit_ideas(self):
        ideas = []
        for sub in self.config.get("subreddits", []):
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
                resp = requests.get(url, headers={"User-Agent": "ContentResearchBot/1.0"}, timeout=10)
                if not resp.ok or not resp.text.strip():
                    continue
                for post in resp.json()["data"]["children"]:
                    p = post["data"]
                    if p["score"] > 50:
                        ideas.append({
                            "title": p["title"],
                            "score": p["score"],
                            "num_comments": p["num_comments"],
                            "subreddit": sub,
                        })
            except Exception as e:
                print(f"Error fetching r/{sub}: {e}")
        return ideas

    def generate_content_ideas(self, trends, reddit_ideas):
        research_summary = json.dumps({
            "trending_articles": trends[:10],
            "popular_reddit_posts": reddit_ideas[:10],
        }, indent=2)

        prompt = f"""You are a content strategist for an Instagram page about {self.niche}.

Here is today's research from trending articles and Reddit:

{research_summary}

Based on this research AND your own knowledge, generate exactly 5 Instagram content ideas.
For each idea provide:
1. content_type: "carousel" or "reel" or "static_image"
2. hook: The first line/headline (max 10 words, must stop scrollers)
3. outline: 3-5 bullet points of what the content covers
4. caption_draft: A full Instagram caption (150-200 words)
5. estimated_engagement: "high" / "medium" / "low" with reasoning
6. hashtags: 8 relevant hashtags

Return ONLY content_type "carousel". No reels. No static_image.
Return as JSON: {{"ideas": [...]}}
Prioritize HIGH engagement potential. Avoid generic advice. Every tip must be specific and actionable."""

        return generate_text(
            prompt,
            system="Expert Instagram content strategist. Return only valid JSON.",
            json_response=True,
            temperature=0.8,
        )

    def save_ideas_to_db(self, ideas):
        saved = []
        for idea in ideas.get("ideas", ideas):
            new_id = save_idea({
                "content_type": idea["content_type"],
                "hook": idea["hook"],
                "outline": json.dumps(idea["outline"]),
                "caption_draft": idea["caption_draft"],
                "hashtags": json.dumps(idea["hashtags"]),
                "status": "pending_review",
                "created_at": datetime.utcnow().isoformat(),
                "engagement_estimate": idea.get("estimated_engagement", "medium"),
            })
            saved.append(new_id)
        return saved

    def run(self):
        print("Research Agent: Gathering trends...")
        trends = self.gather_trends()
        reddit = self.gather_reddit_ideas()

        print("Research Agent: Generating content ideas...")
        ideas = self.generate_content_ideas(trends, reddit)

        print("Research Agent: Saving to database...")
        saved_ids = self.save_ideas_to_db(ideas)

        print(f"Research Agent: {len(saved_ids)} new ideas added to review queue")
        return ideas

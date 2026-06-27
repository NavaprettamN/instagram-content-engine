import feedparser
import requests
import json
from datetime import datetime
from agents._llm import generate_text
from agents._db import save_idea, get_analytics, get_config
from agents.trend_agent import TrendAgent


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

    def generate_content_ideas(self, trends, reddit_ideas, platform_trends=None):
        research_summary = json.dumps({
            "trending_articles": trends[:10],
            "popular_reddit_posts": reddit_ideas[:10],
            "platform_trends": platform_trends or {},
        }, indent=2)

        # Close the feedback loop: feed last week's AI analysis into idea generation.
        snaps = get_analytics(limit=1)
        learnings = ""
        if snaps and snaps[0].get("analysis"):
            learnings = (
                "\nWHAT WORKED LAST WEEK (lean into these patterns, avoid what underperformed):\n"
                f"{snaps[0]['analysis']}\n"
            )
        # Concrete winners (#7): our actual top-scoring posts by saves/shares.
        top = get_config("top_performers")
        if top:
            learnings += (
                "\nOUR BEST-PERFORMING POSTS SO FAR (create more ideas in this vein — "
                "same angle/format/topic that earned the most saves & shares):\n"
                f"{top}\n"
            )

        prompt = f"""You are a content strategist for an Instagram page about {self.niche}.

Here is today's research — trending articles, Reddit, and live platform trends
(what's getting views/searches RIGHT NOW on YouTube, Google, and TikTok):

{research_summary}
{learnings}
Based on this research AND your own knowledge, generate exactly 5 Instagram content ideas.
Lean into the "platform_trends" — riding a currently-surging topic is the single
biggest reach multiplier. Tie ideas to those trends wherever it's genuinely relevant.
For each idea provide:
1. content_type: "carousel" or "reel" or "static_image"
2. hook: The first line/headline (max 8 words). Use a curiosity gap, a bold claim, or a number — it must stop the scroll and make people NEED the rest.
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
        # ponytail: auto-approve the best 3 ideas (matches the 3-posts/day cadence) so
        # the pipeline runs hands-off; the rest stay pending_review as a backlog/override.
        items = list(ideas.get("ideas", ideas))
        rank = {"high": 0, "medium": 1, "low": 2}
        items.sort(key=lambda i: rank.get(
            str(i.get("estimated_engagement", i.get("engagement_estimate", "medium"))).lower().split()[0]
            if (i.get("estimated_engagement") or i.get("engagement_estimate")) else "medium", 1))
        saved = []
        for n, idea in enumerate(items):
            new_id = save_idea({
                "content_type": idea.get("content_type", "carousel"),
                "hook": idea.get("hook", ""),
                "outline": json.dumps(idea.get("outline", [])),
                "caption_draft": idea.get("caption_draft", ""),
                "hashtags": json.dumps(idea.get("hashtags", [])),
                "status": "approved" if n < 3 else "pending_review",
                "created_at": datetime.utcnow().isoformat(),
                "engagement_estimate": idea.get("estimated_engagement", idea.get("engagement_estimate", "medium")),
            })
            saved.append(new_id)
        return saved

    def run(self):
        print("Research Agent: Gathering trends...")
        trends = self.gather_trends()
        reddit = self.gather_reddit_ideas()
        platform_trends = TrendAgent(self.config).gather_trends()
        print(f"Research Agent: platform trends "
              f"{ {k: len(v) for k, v in platform_trends.items()} }")

        print("Research Agent: Generating content ideas...")
        ideas = self.generate_content_ideas(trends, reddit, platform_trends)

        print("Research Agent: Saving to database...")
        saved_ids = self.save_ideas_to_db(ideas)

        print(f"Research Agent: {len(saved_ids)} new ideas added to review queue")
        return ideas

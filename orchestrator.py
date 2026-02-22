# orchestrator.py
# This is the brain that coordinates all agents

import schedule
import time
import yaml
import logging
from datetime import datetime

from research_agent import ResearchAgent
from content_agent import ContentAgent
from design_agent import DesignAgent
from publishing_agent import PublishingAgent
from analytics_agent import AnalyticsAgent
from hashtag_agent import HashtagAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

class Orchestrator:
    def __init__(self):
        self.config = load_config()
        self.research = ResearchAgent(self.config)
        self.content = ContentAgent(self.config)
        self.design = DesignAgent(self.config)
        self.publisher = PublishingAgent(self.config)
        self.analytics = AnalyticsAgent(self.config)
        self.hashtags = HashtagAgent(self.config)
    
    def morning_research(self):
        """Run every morning at 7 AM — generate fresh ideas"""
        logger.info("🌅 Morning research cycle starting...")
        try:
            self.research.run()
            logger.info("✅ Research complete — check approval queue")
        except Exception as e:
            logger.error(f"❌ Research failed: {e}")
    
    def auto_generate_approved(self):
        """Run every 2 hours — generate content for approved ideas"""
        logger.info("🎨 Checking for approved ideas needing content...")
        conn = sqlite3.connect(self.config.get("db_path", "content_engine.db"))
        conn.row_factory = sqlite3.Row
        
        approved = conn.execute("""
            SELECT * FROM content_ideas 
            WHERE status='approved' AND generated_content IS NULL
        """).fetchall()
        
        for item in approved:
            try:
                idea = dict(item)
                content = self.content.generate_content(idea)
                
                # Add hashtags
                hashtag_data = self.hashtags.generate_hashtag_sets(
                    idea["hook"]
                )
                
                if idea["content_type"] == "carousel":
                    paths = self.design.generate_carousel_images(
                        content, idea["id"]
                    )
                else:
                    paths = []
                
                conn.execute("""
                    UPDATE content_ideas 
                    SET generated_content=?, image_paths=?, 
                        hashtags=?, status='designed'
                    WHERE id=?
                """, (
                    json.dumps(content),
                    json.dumps(paths),
                    json.dumps(hashtag_data),
                    idea["id"]
                ))
                conn.commit()
                logger.info(f"✅ Generated content for: {idea['hook']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate for {item['id']}: {e}")
        
        conn.close()
    
    def scheduled_publish(self):
        """
        Run at configured posting times.
        Only publishes content with status='designed' (already approved + generated)
        This is the ONLY fully automatic action — but only because 
        YOU already approved it earlier.
        """
        logger.info("📤 Checking for content to publish...")
        conn = sqlite3.connect(self.config.get("db_path", "content_engine.db"))
        conn.row_factory = sqlite3.Row
        
        next_post = conn.execute("""
            SELECT * FROM content_ideas 
            WHERE status='designed'
            ORDER BY created_at ASC
            LIMIT 1
        """).fetchone()
        
        if next_post:
            post = dict(next_post)
            try:
                if post["content_type"] == "carousel":
                    paths = json.loads(post["image_paths"])
                    result = self.publisher.publish_carousel(
                        paths, post["caption_draft"]
                    )
                else:
                    paths = json.loads(post["image_paths"])
                    result = self.publisher.publish_single_image(
                        paths[0], post["caption_draft"]
                    )
                
                conn.execute("""
                    UPDATE content_ideas 
                    SET status='published', published_at=?, post_id=?
                    WHERE id=?
                """, (datetime.now().isoformat(), 
                      result.get("id"), post["id"]))
                conn.commit()
                logger.info(f"📤 Published: {post['hook']}")
                
            except Exception as e:
                logger.error(f"❌ Publishing failed: {e}")
        else:
            logger.info("No content ready to publish")
        
        conn.close()
    
    def weekly_analytics(self):
        """Run every Sunday — full performance analysis"""
        logger.info("📊 Running weekly analytics...")
        try:
            insights = self.analytics.get_account_insights(days=7)
            posts = self.analytics.get_recent_posts()
            analysis = self.analytics.generate_weekly_analysis(
                insights, posts
            )
            
            conn = sqlite3.connect(
                self.config.get("db_path", "content_engine.db")
            )
            conn.execute("""
                INSERT INTO analytics_snapshots (date, analysis) 
                VALUES (?, ?)
            """, (datetime.now().isoformat(), analysis))
            conn.commit()
            conn.close()
            
            logger.info("✅ Weekly analysis saved")
        except Exception as e:
            logger.error(f"❌ Analytics failed: {e}")
    
    def run(self):
        """Start the orchestrator with scheduled tasks"""
        logger.info("🚀 Orchestrator starting...")
        
        # Schedule tasks
        schedule.every().day.at("07:00").do(self.morning_research)
        schedule.every(2).hours.do(self.auto_generate_approved)
        schedule.every().day.at("10:00").do(self.scheduled_publish)
        schedule.every().day.at("18:00").do(self.scheduled_publish)
        schedule.every().sunday.at("20:00").do(self.weekly_analytics)
        
        logger.info("📅 Schedule configured:")
        logger.info("  07:00 daily — Research Agent")
        logger.info("  Every 2h    — Auto-generate approved content")
        logger.info("  10:00 daily — Publish post #1")
        logger.info("  18:00 daily — Publish post #2")
        logger.info("  Sunday 20:00 — Weekly analytics")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
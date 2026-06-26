"""Run the whole pipeline once: research -> generate+design -> publish ONE post.

A manual end-to-end smoke test so you can watch the full chain run without
waiting for the daily crons. Posts a single real post to Instagram.

    python -m scripts.autopilot
"""
import json
import yaml
from datetime import datetime, timezone

from agents.research_agent import ResearchAgent
from agents.content_agent import ContentAgent
from agents.design_agent import DesignAgent
from agents.publishing_agent import PublishingAgent
from agents.hashtag_agent import HashtagAgent, compose_caption
from agents._db import get_ideas, update_idea, count_ideas


def main():
    config = yaml.safe_load(open("config.yaml"))

    print("== Research ==")
    ResearchAgent(config).run()  # auto-approves the top ideas

    approved = [i for i in get_ideas(status="approved") if not i.get("generated_content")]
    if not approved:
        print("No fresh approved idea to run. Stopping.")
        return
    idea = approved[0]  # newest-first
    print(f"== Generate: {idea['hook']} ==")

    content = ContentAgent(config).generate_content(idea)
    local_paths = DesignAgent(config).generate_carousel_images(content, idea["id"])
    pa = PublishingAgent(config)
    hosted = [pa.upload_image_to_hosting(p) for p in local_paths]
    hashtag_sets = HashtagAgent(config).generate_hashtag_sets(idea["hook"])
    update_idea(idea["id"], generated_content=json.dumps(content),
                image_paths=json.dumps(hosted),
                hashtags=json.dumps(hashtag_sets), status="designed")
    idea["hashtags"] = hashtag_sets  # so compose_caption sees the fresh sets
    caption = compose_caption(idea, count_ideas("published"))

    print(f"== Publish ({len(hosted)} slides) ==")
    result = (pa.publish_carousel(hosted, caption) if len(hosted) > 1
              else pa.publish_single_image(hosted[0], caption))
    if "error" in result:
        raise RuntimeError(f"Publish failed: {result['error']}")
    update_idea(idea["id"], status="published",
                published_at=datetime.now(timezone.utc).isoformat(),
                post_id=result.get("id"))
    print(f"Done. IG post ID: {result.get('id')}")


if __name__ == "__main__":
    main()

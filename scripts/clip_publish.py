"""Find a CC YouTube video, clip it to a captioned reel, and QUEUE it.

The clip is saved as a `designed` reel in the content queue (not posted directly),
so publish.yml posts it in the normal 3/day rotation, mixed with carousels and
spaced out. Clips are the primary reel source. Runs daily (clip.yml).

CLIP_DRY_RUN=1 renders + hosts but doesn't queue — prints a preview URL.

    python -m scripts.clip_publish
"""
import os
import json
import yaml
from datetime import datetime, timezone
from agents.clip_agent import ClipAgent
from agents.publishing_agent import PublishingAgent
from agents.hashtag_agent import HashtagAgent
from agents._db import save_idea


def main():
    config = yaml.safe_load(open("config.yaml"))
    result = ClipAgent(config).run()
    if not result:
        print("clip_publish: nothing to clip.")
        return
    pa = PublishingAgent(config)
    url = pa.upload_video_to_hosting(result["path"])
    print("hosted:", url)
    if os.environ.get("CLIP_DRY_RUN"):
        print(f"DRY RUN — not queuing. Preview the captioned clip:\n{url}")
        print(f"hook: {result['hook']}\ncaption:\n{result['caption']}")
        return
    sets = HashtagAgent(config).generate_hashtag_sets(result["hook"])
    new_id = save_idea({
        "content_type": "reel",
        "hook": result["hook"],
        "caption_draft": result["caption"],
        "image_paths": json.dumps([url]),
        "hashtags": json.dumps(sets),
        "generated_content": json.dumps({"source": "youtube_clip"}),
        "status": "designed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "engagement_estimate": "high",
    })
    print(f"Queued clip reel (idea {new_id}) — publish.yml will post it: {result['hook']}")


if __name__ == "__main__":
    main()

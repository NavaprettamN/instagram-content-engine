"""Find a CC YouTube video, clip it to a captioned reel, and publish it.

Manual/weekly. Separate from the carousel/reel pipeline — clips don't go through
research/approval (the source is licensed third-party video, made transformative).

    python -m scripts.clip_publish
"""
import os
import yaml
from agents.clip_agent import ClipAgent
from agents.publishing_agent import PublishingAgent


def main():
    config = yaml.safe_load(open("config.yaml"))
    result = ClipAgent(config).run()
    if not result:
        print("clip_publish: nothing to publish.")
        return
    pa = PublishingAgent(config)
    url = pa.upload_video_to_hosting(result["path"])
    print("hosted:", url)
    if os.environ.get("CLIP_DRY_RUN"):
        # render + host but DON'T post — open the URL to review captions/framing
        print(f"DRY RUN — not publishing. Preview the captioned clip:\n{url}")
        print(f"hook: {result['hook']}\ncaption:\n{result['caption']}")
        return
    res = pa.publish_reel(url, result["caption"])
    if "error" in res:
        raise RuntimeError(f"publish failed: {res['error']}")
    print(f"Published clip reel: {res.get('id')} — {result['hook']}")


if __name__ == "__main__":
    main()

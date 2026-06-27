"""Repost the latest image post to Stories (keeps Stories active, drives profile
visits). One per post — tracked in config.last_story_post so it won't repeat.

API can't add link/poll/quiz stickers, so this is a plain image story.

    python -m scripts.post_story
"""
import json
import yaml
from agents.publishing_agent import PublishingAgent
from agents._db import get_ideas, get_config, set_config


def first_image(post):
    raw = post.get("image_paths") or "[]"
    paths = json.loads(raw) if isinstance(raw, str) else (raw or [])
    return next((p for p in paths
                 if isinstance(p, str) and p.startswith("http") and not p.endswith(".mp4")), None)


def main():
    config = yaml.safe_load(open("config.yaml"))
    post = next((p for p in get_ideas(status="published") if first_image(p)), None)
    if not post:
        print("post_story: no image post to promote.")
        return
    if get_config("last_story_post") == str(post["id"]):
        print("post_story: latest already promoted; skipping.")
        return
    res = PublishingAgent(config).publish_story(first_image(post))
    if "id" in res:
        set_config("last_story_post", str(post["id"]))
        print(f"post_story: story posted ({res['id']}) for '{post['hook']}'")
    else:
        print(f"post_story: failed -> {res}")


if __name__ == "__main__":
    main()

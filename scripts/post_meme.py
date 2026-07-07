"""Build a meme-dump reel and auto-publish it to Instagram (Phase F2).

Fetches fresh memes (skipping ones already used), builds the reel with an
embedded CC music bed, hosts it on Supabase, and publishes it via the Instagram
API — fully hands-off, same path as the value reels. (Native trending audio
can't be attached via the API; that's the deliberate trade for zero manual work.)

Run:  python -m scripts.post_meme
"""
import yaml

from agents.meme_agent import MemeAgent
from agents.music_agent import MusicAgent
from agents.publishing_agent import PublishingAgent
from agents._db import get_config, set_config, upload_video
from agents import notify

SEEN_KEY = "seen_memes"
SEEN_CAP = 300


def main():
    config = yaml.safe_load(open("config.yaml"))
    agent = MemeAgent(config)

    seen = [s for s in (get_config(SEEN_KEY) or "").split(",") if s]
    memes = agent.fetch_memes(limit=config.get("memes_per_reel", 4), seen=seen)
    if not memes:
        print("No fresh memes found (all seen or fetch failed).")
        return

    base = config["output_dir"]
    # upbeat CC music bed (seed by first meme id so consecutive reels differ)
    music = MusicAgent(config).pick_track("funny memes", f"{base}/meme_music.mp3",
                                          seed=abs(hash(memes[0]["id"])) % 997)
    reel = agent.build_reel(memes, f"{base}/meme_reel.mp4",
                            music_path=(music["path"] if music else None))
    url = upload_video(reel)
    caption = agent.caption(memes)
    if music:
        caption = f"{caption}\n\n{music['credit']}"  # CC attribution
    print(f"Meme reel hosted: {url}")

    # persist seen ids before publishing so a publish retry can't double-use memes
    new_seen = [m["id"] for m in memes] + seen
    set_config(SEEN_KEY, ",".join(dict.fromkeys(new_seen))[:SEEN_CAP * 12])

    result = PublishingAgent(config).publish_reel(url, caption)
    if not result.get("id"):
        print(f"Publish FAILED: {result}")
        raise SystemExit(1)
    print(f"Published meme reel! IG post ID: {result['id']}")
    notify.send("New meme reel posted 😂",
                f"{len(memes)} memes auto-posted.",
                url="https://www.instagram.com/" + config.get("instagram_handle", "").lstrip("@"))


if __name__ == "__main__":
    main()

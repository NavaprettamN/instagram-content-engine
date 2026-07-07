"""Build a meme-dump reel and notification-publish it (Phase F2).

Fetches fresh memes (skipping ones already used), builds the reel, hosts it on
Supabase (public URL), then pings your phone via notify.send() with the video
URL + caption. It intentionally does NOT call the Instagram publish API — you
open Instagram on your phone, add native trending audio, and post (~20s). That's
the only way to get trending audio (the API can't attach it).

Run:  python -m scripts.post_meme
"""
import yaml

from agents.meme_agent import MemeAgent
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

    out = f'{config["output_dir"]}/meme_reel.mp4'
    reel = agent.build_reel(memes, out)
    url = upload_video(reel)
    caption = agent.caption(memes)
    print(f"Meme reel hosted: {url}")

    # persist seen ids (most-recent-first, capped)
    new_seen = [m["id"] for m in memes] + seen
    set_config(SEEN_KEY, ",".join(dict.fromkeys(new_seen))[:SEEN_CAP * 12])

    sent = notify.send(
        "Meme reel ready — add trending audio + post 🎵",
        f"{len(memes)} memes. Download, open Instagram, add a trending sound, "
        f"paste caption, share.\n\nVideo: {url}\n\nCaption:\n{caption}",
        url=url,
    )
    if sent:
        print("Notification sent — post it from your phone with trending audio.")
    else:
        print("No notification channel set (NTFY_TOPIC/DISCORD_WEBHOOK/SLACK_WEBHOOK).")
        print(f"Manual: download {url}\nCaption:\n{caption}")


if __name__ == "__main__":
    main()

"""Build a meme reel and auto-publish it to Instagram (Phase F2; videos Phase H).

Alternates between two formats per run (odd/even persistent counter):
- Reddit VIDEO memes (original audio kept — that's the joke), re-framed to 9:16.
- Image meme reels with an embedded CC music bed. (Native trending audio can't
  be attached via the API; that's the deliberate trade for zero manual work.)

Video runs fall back to images when no fresh video is found (or Reddit blocks
the runner). After publishing, the same reel is reposted to Stories
(best-effort) to keep Stories active and drive profile visits.

MEME_FORMAT=video|images overrides the alternation (meme.yml dispatch input).

Run:  python -m scripts.post_meme
"""
import os

import yaml

from agents.meme_agent import MemeAgent
from agents.music_agent import MusicAgent
from agents.publishing_agent import PublishingAgent
from agents._db import get_config, set_config, upload_video
from agents import notify

SEEN_KEY = "seen_memes"
SEEN_CAP = 300
# Rotate BOTH genre and track by the persistent counter so meme music stays
# varied and upbeat (the mood tags' all-time-popular pool is classical piano —
# wrong vibe for memes; these genres on popularity_month are energetic).
MUSIC_GENRES = ["pop", "electronic", "funk", "dance", "happy"]


def _pick_meme_music(config, base, seed):
    """A CC music bed for a meme reel, or None. Genre+track rotate by the seed."""
    return MusicAgent(config).pick_track(
        "meme", f"{base}/meme_music.mp3", seed=seed,
        tags=MUSIC_GENRES[seed % len(MUSIC_GENRES)], order="popularity_month")


def build_video(agent, config, seen, seed):
    """Fresh Reddit video -> (path, caption, used_ids) or None.

    Video memes keep their original Reddit audio (usually the joke). But many
    v.redd.it clips are silent — for those, add a CC music bed like image reels
    do, so a video reel never ships soundless."""
    videos = agent.fetch_videos(limit=1, seen=seen)
    if not videos:
        print("No fresh Reddit video found — falling back to image memes.")
        return None
    v = videos[0]
    base = config["output_dir"]
    reel = agent.build_video_reel(v, f"{base}/meme_reel.mp4")
    caption = agent.caption([v])
    if not agent.has_audio(reel):
        print("Source clip is silent — adding a CC music bed.")
        music = _pick_meme_music(config, base, seed)
        if music:
            reel = agent.add_music_bed(reel, music["path"], f"{base}/meme_reel_music.mp4")
            caption = f"{caption}\n\n{music['credit']}"  # CC attribution
        else:
            print("No music available — video reel will be silent.")
    print(f"Built video reel from r/ post by u/{v['author']}: {v['title'][:60]}")
    return reel, caption, [v["id"]]


def build_images(agent, config, seen, seed):
    """Image meme reel with a CC music bed -> (path, caption, used_ids) or None."""
    memes = agent.fetch_memes(limit=config.get("memes_per_reel", 4), seen=seen)
    if not memes:
        return None
    base = config["output_dir"]
    music = _pick_meme_music(config, base, seed)
    reel = agent.build_reel(memes, f"{base}/meme_reel.mp4",
                            music_path=(music["path"] if music else None))
    caption = agent.caption(memes)
    if music:
        caption = f"{caption}\n\n{music['credit']}"  # CC attribution
    return reel, caption, [m["id"] for m in memes]


def main():
    config = yaml.safe_load(open("config.yaml"))
    agent = MemeAgent(config)

    seen = [s for s in (get_config(SEEN_KEY) or "").split(",") if s]
    # persistent counter: rotates music AND alternates video/image format
    seed = int(get_config("meme_music_seed") or 0)
    set_config("meme_music_seed", seed + 1)

    fmt = os.environ.get("MEME_FORMAT") or ("video" if seed % 2 else "images")
    built = build_video(agent, config, seen, seed) if fmt == "video" else None
    if built is None:
        built = build_images(agent, config, seen, seed)
    if built is None:
        print("No fresh memes found (all seen or fetch failed).")
        return
    reel, caption, used_ids = built

    url = upload_video(reel)
    print(f"Meme reel hosted: {url}")

    # persist seen ids before publishing so a publish retry can't double-use memes.
    # Cap by id COUNT (not chars) so truncation can't splice a partial id.
    kept = list(dict.fromkeys(used_ids + seen))[:SEEN_CAP]
    set_config(SEEN_KEY, ",".join(kept))

    publisher = PublishingAgent(config)
    result = publisher.publish_reel(url, caption)
    if not result.get("id"):
        print(f"Publish FAILED: {result}")
        raise SystemExit(1)
    print(f"Published meme reel! IG post ID: {result['id']}")

    # repost the same reel to Stories (best-effort; the post is already live)
    try:
        story = publisher.publish_story(url, is_video=True)
        print(f"Story: {story.get('id') or story}")
    except Exception as e:
        print(f"Story repost failed (non-fatal): {e}")

    notify.send("New meme reel posted 😂",
                f"{fmt} reel auto-posted (+story).",
                url="https://www.instagram.com/" + config.get("instagram_handle", "").lstrip("@"))


if __name__ == "__main__":
    main()

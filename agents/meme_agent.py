"""Meme-dump reels from Reddit (Phase F1).

Fetches top image posts from meme subreddits, composes each onto a 1080x1920
frame (blurred cover background + centered meme + `via u/author` credit), and
stitches N of them into a fast-cut reel with a CC music bed. The music is only a
placeholder — these reels go out via notification-publish (meme.yml) so you swap
in native Instagram trending audio at post time.

Best-effort throughout: a failed fetch/download/compose just yields fewer memes;
build raises only if it ends up with zero.
"""
import os
import subprocess

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
# Reddit blocks unauthenticated JSON (403) from most IPs now; meme-api.com is a
# free, keyless proxy that returns top image posts from a subreddit as JSON.
MEME_API = "https://meme-api.com/gimme"


class MemeAgent:
    def __init__(self, config):
        self.config = config or {}
        self.subreddits = self.config.get("meme_subreddits",
                                          ["memes", "wholesomememes", "MemeEconomy"])
        self.min_score = self.config.get("meme_min_score", 2000)
        self.seconds_each = self.config.get("meme_seconds_each", 6)
        self.cache = os.path.join(self.config.get("output_dir", "./generated_content"), "memes")
        os.makedirs(self.cache, exist_ok=True)
        self.font = self.config.get("font_bold", "./fonts/Inter-Bold.ttf")

    def _font(self, size):
        try:
            return ImageFont.truetype(self.font, size)
        except Exception:
            return ImageFont.load_default(size=size)

    def _meme_id(self, m):
        # image filename (e.g. i.redd.it/<id>.png) is a stable per-post key
        return os.path.splitext(os.path.basename(m.get("url", "")))[0] or (m.get("postLink") or "")

    def fetch_memes(self, limit=4, seen=None):
        """Return [{'path','title','author','permalink','id'}] top image memes
        via meme-api.com (keyless Reddit proxy)."""
        seen = set(seen or [])
        out = []
        for sub in self.subreddits:
            if len(out) >= limit:
                break
            try:
                r = requests.get(f"{MEME_API}/{sub}/20", timeout=20,
                                 headers={"User-Agent": "Mozilla/5.0"})
                if not r.ok:
                    continue
                for m in r.json().get("memes", []):
                    url = m.get("url", "")
                    mid = self._meme_id(m)
                    # meme-api's `ups` is unreliable (random hot sample), so scoring
                    # isn't gated here — YOU are the quality gate at notification-
                    # publish time. Just skip NSFW/spoiler/dupes/non-images.
                    if (m.get("nsfw") or m.get("spoiler")
                            or mid in seen
                            or not url.lower().endswith(IMG_EXT)):
                        continue
                    dest = os.path.join(self.cache, f"{mid}{os.path.splitext(url)[1][:5]}")
                    try:
                        img = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
                        img.raise_for_status()
                        if len(img.content) < 5_000:
                            continue
                        with open(dest, "wb") as f:
                            f.write(img.content)
                    except Exception:
                        continue
                    out.append({"path": dest, "title": m.get("title", ""),
                                "author": m.get("author", ""), "id": mid,
                                "permalink": m.get("postLink", "")})
                    seen.add(mid)
                    if len(out) >= limit:
                        break
            except Exception as e:
                print(f"MemeAgent: r/{sub} failed ({str(e)[:80]})")
        return out

    def _compose_frame(self, meme, dest):
        """Blurred cover bg + centered meme + credit -> 1080x1920 PNG."""
        try:
            src = Image.open(meme["path"]).convert("RGB")
        except Exception as e:
            print(f"MemeAgent: bad image {meme['id']} ({str(e)[:60]})")
            return None
        # blurred, darkened cover background
        bg = src.copy()
        scale = max(W / bg.width, H / bg.height)
        bg = bg.resize((int(bg.width * scale), int(bg.height * scale)))
        bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2,
                      (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
        bg = bg.filter(ImageFilter.GaussianBlur(40))
        bg = Image.blend(bg, Image.new("RGB", (W, H), (10, 10, 20)), 0.45)
        # centered meme, fit to ~92% width, capped height
        mw = int(W * 0.92)
        mh = int(src.height * (mw / src.width))
        if mh > int(H * 0.74):
            mh = int(H * 0.74)
            mw = int(src.width * (mh / src.height))
        meme_img = src.resize((mw, mh))
        bg.paste(meme_img, ((W - mw) // 2, (H - mh) // 2))
        # credit line (repost hygiene)
        d = ImageDraw.Draw(bg)
        credit = f"via u/{meme['author']}" if meme.get("author") else "via reddit"
        f = self._font(34)
        tw = d.textlength(credit, font=f)
        d.text(((W - tw) // 2, H - 90), credit, font=f, fill=(200, 200, 210))
        bg.save(dest)
        return dest

    def build_reel(self, memes, out_path, music_path=None):
        """Compose memes into a slideshow reel. Returns out_path or raises."""
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        frames = []
        for i, m in enumerate(memes):
            fp = os.path.join(self.cache, f"frame_{m['id']}.png")
            if self._compose_frame(m, fp):
                frames.append(fp)
        if not frames:
            raise RuntimeError("no meme frames composed")

        # ffmpeg concat of stills, each held self.seconds_each, + optional music bed
        listfile = os.path.join(self.cache, "frames.txt")
        with open(listfile, "w") as f:
            for fp in frames:
                f.write(f"file '{os.path.abspath(fp)}'\nduration {self.seconds_each}\n")
            f.write(f"file '{os.path.abspath(frames[-1])}'\n")  # concat demuxer needs last repeated
        total = self.seconds_each * len(frames)

        vfilter = ("scale=1080:1920:force_original_aspect_ratio=increase,"
                   "crop=1080:1920,setsar=1,fps=30,format=yuv420p")
        # all inputs first (0 = frame slideshow, 1 = audio bed), then output opts
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile]
        if music_path:
            cmd += ["-stream_loop", "-1", "-i", music_path]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        cmd += ["-vf", vfilter, "-map", "0:v", "-map", "1:a",
                "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.2f}",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", out_path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"meme reel ffmpeg failed:\n{r.stderr[-1200:]}")
        return out_path

    def caption(self, memes):
        """A light caption; credits sources (repost hygiene) + save/follow CTA."""
        handle = self.config.get("instagram_handle", "")
        srcs = ", ".join(dict.fromkeys(f"u/{m['author']}" for m in memes if m.get("author")))
        cta = f"Follow {handle} for daily memes 😂 · Save & send to a friend"
        credit = f"\n\nCredit: {srcs} (via Reddit)" if srcs else ""
        return f"{cta}{credit}"


if __name__ == "__main__":
    # ponytail: real self-check — needs network + ffmpeg. Builds one meme reel.
    import yaml
    cfg = yaml.safe_load(open("config.yaml"))
    cfg["output_dir"] = "/tmp/meme_check"
    a = MemeAgent(cfg)
    memes = a.fetch_memes(limit=4)
    assert memes, "no memes fetched (subreddit/network issue)"
    print("fetched", [m["id"] for m in memes])
    p = a.build_reel(memes, "/tmp/meme_check/reel.mp4")
    assert os.path.getsize(p) > 100_000, p
    print("meme_agent self-check OK:", p, "| caption:", a.caption(memes)[:60])

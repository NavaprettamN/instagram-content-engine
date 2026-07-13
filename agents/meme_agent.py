"""Meme reels from Reddit (Phase F1; videos added Phase H).

Two formats:
- Image memes: top image posts from meme subreddits via meme-api.com, each
  composed onto a 1080x1920 frame (blurred cover background + centered meme +
  `via u/author` credit) and stitched into a reel with a CC music bed.
- Video memes: top v.redd.it posts from video subreddits via Reddit's RSS feed
  (the JSON API 403s unauthenticated, RSS doesn't), pulled through the public
  HLS playlist with ffmpeg and re-framed to 9:16 with a blurred background.
  Original audio is kept — that's usually the joke.

Best-effort throughout: a failed fetch/download/compose just yields fewer memes;
build raises only if it ends up with zero.
"""
import html
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
# Reddit blocks unauthenticated JSON (403) from most IPs now; meme-api.com is a
# free, keyless proxy that returns top image posts from a subreddit as JSON.
MEME_API = "https://meme-api.com/gimme"
ATOM = {"a": "http://www.w3.org/2005/Atom"}


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
        self.video_subreddits = self.config.get(
            "meme_video_subreddits",
            ["Unexpected", "funny", "ContagiousLaughter", "AnimalsBeingDerps"])
        self.video_max_seconds = self.config.get("meme_video_max_seconds", 45)
        self.video_min_seconds = self.config.get("meme_video_min_seconds", 3)
        self.niche = self.config.get("niche", "memes & relatable humor")
        self.brand_voice = self.config.get("brand_voice", "")
        # LLM-written {hook, caption} cached per meme set so build_reel (hook) and
        # caption() (caption) don't each trigger a separate call.
        self._copy_cache = {}

    def _font(self, size):
        try:
            return ImageFont.truetype(self.font, size)
        except Exception:
            return ImageFont.load_default(size=size)

    def _wrap(self, draw, text, font, max_w):
        """Greedy word-wrap `text` to lines that fit within max_w pixels."""
        lines, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if draw.textlength(trial, font=font) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def _share_copy(self, memes):
        """LLM-written {'hook','caption'} for the LEAD meme (memes[0] — the one
        the hook sits on), engineered for DM shares (the #1 2026 reach signal).
        Sends the actual meme image to Gemini (free vision) so the copy matches
        the real joke, not the often-useless Reddit title. Best-effort + cached:
        returns None on any failure so callers fall back to static copy."""
        if not memes:
            return None
        key = tuple(m.get("id", "") for m in memes)
        if key in self._copy_cache:
            return self._copy_cache[key]

        lead = memes[0]
        result = None
        try:
            from agents._llm import generate_text
            system = (
                "You are the editor of a viral Instagram meme page. In 2026, DM "
                "sends are the #1 reach signal, so your only job is to make someone "
                "instantly think of a specific friend and send them THIS meme. "
                f"Niche: {self.niche}. Voice: {self.brand_voice or 'casual, funny, meme-fluent, never corporate'}. "
                "If the meme touches a sensitive or serious topic (race, politics, "
                "tragedy, religion), keep the copy warm and respectful — never "
                "flippant. The hook and caption must fit THIS specific meme."
            )
            prompt = (
                f"The meme image is attached. (Reddit title for context: "
                f"\"{lead.get('title', '')}\".)\n\n"
                "Read what's actually happening in the meme, then return JSON with "
                "exactly two string fields:\n"
                '- "hook": a 3-6 word on-screen text hook shown on this frame that '
                "stops the scroll (relatable / curiosity / POV style), matching the "
                "meme. Max 38 characters. No hashtags, no quotes.\n"
                '- "caption": a 1-2 line Instagram caption about this meme that ENDS '
                "in a 'tag someone who…' or 'send this to the friend who…' CTA. "
                "Under 140 characters. At most one emoji. No hashtags.\n\n"
                "Return ONLY the JSON."
            )
            data = generate_text(prompt, system=system, json_response=True,
                                 temperature=0.9, image_path=lead.get("path"))
            hook = str((data or {}).get("hook", "")).strip().strip('"')
            cap = str((data or {}).get("caption", "")).strip().strip('"')
            if cap:
                result = {"hook": hook[:60], "caption": cap[:280]}
        except Exception as e:
            print(f"MemeAgent: share-copy LLM failed ({str(e)[:90]}) — static fallback.")

        self._copy_cache[key] = result
        return result

    def _meme_id(self, m):
        # image filename (e.g. i.redd.it/<id>.png) is a stable per-post key
        return os.path.splitext(os.path.basename(m.get("url", "")))[0] or (m.get("postLink") or "")

    def fetch_memes(self, limit=4, seen=None):
        """Return the top image memes by upvotes: [{'path','title','author',
        'permalink','id','score'}].

        meme-api.com returns a *random* sample from a sub's hot listing, but each
        post's `ups` is the real Reddit score — so we over-fetch a big pool across
        all subs, rank by upvotes, keep only those clearing `meme_min_score`, and
        download the top `limit`. This makes selection favour already-proven memes
        instead of whatever happened to come back first. Falls back to the best
        available if too few clear the floor (best-effort: never post nothing)."""
        seen = set(seen or [])
        # 1) Build a candidate pool across subs WITHOUT downloading yet.
        best = {}  # mid -> (ups, meme_json) keeping the highest-scored dupe
        for sub in self.subreddits:
            try:
                r = requests.get(f"{MEME_API}/{sub}/50", timeout=20,
                                 headers={"User-Agent": "Mozilla/5.0"})
                if not r.ok:
                    continue
                for m in r.json().get("memes", []):
                    url = m.get("url", "")
                    mid = self._meme_id(m)
                    if (m.get("nsfw") or m.get("spoiler")
                            or mid in seen
                            or not url.lower().endswith(IMG_EXT)):
                        continue
                    ups = int(m.get("ups") or 0)
                    if mid not in best or ups > best[mid][0]:
                        best[mid] = (ups, m)
            except Exception as e:
                print(f"MemeAgent: r/{sub} failed ({str(e)[:80]})")

        # 2) Rank by upvotes; prefer above the floor, fall back to best available.
        ranked = sorted(best.values(), key=lambda t: t[0], reverse=True)
        above = [t for t in ranked if t[0] >= self.min_score]
        chosen = above if len(above) >= limit else ranked
        print(f"MemeAgent: {len(ranked)} candidates, {len(above)} over "
              f"min_score={self.min_score}; picking top {limit} by upvotes")

        # 3) Download the top picks in score order (skip any that fail to fetch).
        out = []
        for ups, m in chosen:
            if len(out) >= limit:
                break
            url = m.get("url", "")
            mid = self._meme_id(m)
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
                        "permalink": m.get("postLink", ""), "score": ups})
            seen.add(mid)
        return out

    def _draw_hook(self, draw, hook):
        """Bold, outlined hook banner in the top band (the 1.5s scroll-stopper).
        The meme is centered at ≤74% height, so the top ~250px band is free."""
        f = self._font(58)
        lines = self._wrap(draw, hook, f, int(W * 0.9))
        if len(lines) > 2:  # too long at 58 — shrink and re-wrap, cap at 2 lines
            f = self._font(46)
            lines = self._wrap(draw, hook, f, int(W * 0.9))[:2]
        y = 56
        for line in lines:
            tw = draw.textlength(line, font=f)
            x = (W - tw) // 2
            for dx, dy in ((-3, -3), (3, -3), (-3, 3), (3, 3), (0, 3), (0, -3)):
                draw.text((x + dx, y + dy), line, font=f, fill=(0, 0, 0))
            draw.text((x, y), line, font=f, fill=(255, 255, 255))
            y += f.size + 8

    def _compose_frame(self, meme, dest, hook=None):
        """Blurred cover bg + centered meme + credit -> 1080x1920 PNG.
        `hook` (first frame only) draws a scroll-stopping banner up top."""
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
        if hook:
            self._draw_hook(d, hook)
        bg.save(dest)
        return dest

    def build_reel(self, memes, out_path, music_path=None):
        """Compose memes into a slideshow reel. Returns out_path or raises."""
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        hook = (self._share_copy(memes) or {}).get("hook")  # first frame only
        frames = []
        for i, m in enumerate(memes):
            fp = os.path.join(self.cache, f"frame_{m['id']}.png")
            if self._compose_frame(m, fp, hook=hook if i == 0 else None):
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

    # ── Reddit videos (Phase H) ──────────────────────────────────

    def _rss(self, sub):
        """One subreddit's top-of-day Atom feed. Reddit rate-limits bursts and
        then returns an empty 200 body, so retry with backoff."""
        url = f"https://www.reddit.com/r/{sub}/top/.rss?t=day&limit=25"
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=20,
                                 headers={"User-Agent": "meme-engine/1.0 (personal project)"})
                if r.ok and len(r.text) > 1000:
                    return ET.fromstring(r.text)
            except Exception:
                pass
            time.sleep(8 * (attempt + 1))
        return None

    def _video_duration(self, vid):
        """Seconds from the public DASH manifest, or None."""
        try:
            r = requests.get(f"https://v.redd.it/{vid}/DASHPlaylist.mpd", timeout=20,
                             headers={"User-Agent": "Mozilla/5.0"})
            m = re.search(r'mediaPresentationDuration="PT(?:(\d+)M)?([\d.]+)S"', r.text)
            if m:
                return int(m.group(1) or 0) * 60 + float(m.group(2))
        except Exception:
            pass
        return None

    def fetch_videos(self, limit=1, seen=None):
        """Top fresh v.redd.it posts: [{'id','title','author','permalink','hls'}].
        The RSS entry content links video posts to v.redd.it — the JSON API
        would 403, the feed doesn't."""
        seen = set(seen or [])
        out = []
        for sub in self.video_subreddits:
            if len(out) >= limit:
                break
            feed = self._rss(sub)
            if feed is None:
                print(f"MemeAgent: r/{sub} RSS failed")
                continue
            for e in feed.findall("a:entry", ATOM):
                content = html.unescape(e.findtext("a:content", "", ATOM))
                m = re.search(r"https://v\.redd\.it/([a-z0-9]+)", content)
                if not m or m.group(1) in seen:
                    continue
                vid = m.group(1)
                dur = self._video_duration(vid)
                if not dur or not (self.video_min_seconds <= dur <= self.video_max_seconds):
                    continue
                author = (e.findtext("a:author/a:name", "", ATOM) or "").lstrip("/u/")
                link = e.find("a:link", ATOM)
                out.append({"id": vid, "title": e.findtext("a:title", "", ATOM),
                            "author": author,
                            "permalink": link.get("href", "") if link is not None else "",
                            "hls": f"https://v.redd.it/{vid}/HLSPlaylist.m3u8"})
                seen.add(vid)
                if len(out) >= limit:
                    break
        return out

    def _credit_overlay(self, credit):
        """Transparent 1080x1920 PNG with the credit line (ffmpeg drawtext isn't
        in every build; a PIL overlay works with any ffmpeg)."""
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        f = self._font(34)
        tw = d.textlength(credit, font=f)
        d.text(((W - tw) // 2, H - 90), credit, font=f, fill=(200, 200, 210, 255))
        p = os.path.join(self.cache, "credit.png")
        img.save(p)
        return p

    def build_video_reel(self, video, out_path):
        """Re-frame a v.redd.it video to 1080x1920 (blurred cover bg + centered
        video + credit line), keeping the original audio. Returns out_path."""
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        credit = f"via u/{video['author']}" if video.get("author") else "via reddit"
        vf = (
            "[0:v]split[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,gblur=sigma=30,eq=brightness=-0.15[bgb];"
            "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fgs];"
            "[bgb][fgs]overlay=(W-w)/2:(H-h)/2[base];"
            "[base][1:v]overlay=0:0,fps=30,format=yuv420p[v]"
        )
        cmd = ["ffmpeg", "-y", "-user_agent", "Mozilla/5.0", "-i", video["hls"],
               "-i", self._credit_overlay(credit),
               "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
               "-t", str(self.video_max_seconds),
               "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"video reel ffmpeg failed:\n{r.stderr[-1200:]}")
        return out_path

    def caption(self, memes):
        """Share-optimized caption. Prefers an LLM-written hook + 'send to a
        friend' CTA (targets DM sends, the #1 2026 reach signal); falls back to
        a static CTA if the LLM is unavailable. Always credits sources + follow."""
        handle = self.config.get("instagram_handle", "")
        srcs = ", ".join(dict.fromkeys(f"u/{m['author']}" for m in memes if m.get("author")))
        copy = self._share_copy(memes)
        if copy and copy.get("caption"):
            body = copy["caption"]
            follow = f"\n\nFollow {handle} for daily memes 😂" if handle else ""
        else:
            body = f"Follow {handle} for daily memes 😂 · Save & send to a friend"
            follow = ""
        credit = f"\n\nCredit: {srcs} (via Reddit)" if srcs else ""
        return f"{body}{follow}{credit}"


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

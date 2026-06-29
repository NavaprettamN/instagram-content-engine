"""Turn a Creative-Commons YouTube video into a captioned vertical reel.

Pipeline: find CC video (YouTube Data API, videoLicense=creativeCommon) -> download
(yt-dlp) -> transcribe (faster-whisper, $0 on CPU) -> Gemini picks the best 20-40s
segment -> ffmpeg cut + 9:16 reframe + burned captions -> publish_reel.

Compliance: the creativeCommon filter covers copyright; CC-BY attribution is
appended to the caption (returned as 'credit'); reframing + captioning + segment
selection make it transformative (avoids Meta's unoriginal-content demotion).

Heavy deps (yt-dlp, faster-whisper) and the Whisper CPU cost mean this runs
sparingly (weekly clip.yml), capped to short-ish source videos.
"""
import os
import sys
import subprocess
import requests
from agents._llm import generate_text

SEARCH = "https://www.googleapis.com/youtube/v3/search"


class ClipAgent:
    def __init__(self, config):
        self.yt_key = os.environ.get("YOUTUBE_API_KEY")
        self.vimeo_token = os.environ.get("VIMEO_TOKEN")
        self.source = config.get("clip_source", "vimeo")  # vimeo (CI-friendly) or youtube
        self.keywords = config.get("keywords", [])
        self.niche = config.get("niche", "")
        self.output_dir = config.get("output_dir", "./generated_content")

    # ── source ──────────────────────────────────────────────────────
    def find_video(self):
        """Dispatch to the configured source. Vimeo is cookie-free + CI-friendly;
        YouTube is bigger but bot-blocks datacenter IPs (needs residential/proxy)."""
        return self.find_vimeo_cc() if self.source == "vimeo" else self.find_cc_video()

    # cheap first-pass safety: never clip anything whose title/description hits these
    BLOCKLIST = ("porn", "nsfw", "sex", "nude", "naked", "xxx", "erotic", "onlyfans",
                 "gambling", "casino", "crypto pump", "music video", "short film")

    def find_vimeo_cc(self):
        """A safe, on-topic Creative-Commons Vimeo video not clipped before, or None.
        Vets with a blocklist + an LLM relevance/safety check — never auto-clip junk."""
        if not self.vimeo_token:
            print("ClipAgent: VIMEO_TOKEN not set")
            return None
        import json
        from agents._db import get_config
        clipped = set(json.loads(get_config("clipped_videos") or "[]"))
        kws = list(self.keywords) or ["AI tools"]
        candidates = []
        for kw in kws[:5]:
            try:
                r = requests.get(
                    "https://api.vimeo.com/videos",
                    headers={"Authorization": f"bearer {self.vimeo_token}"},
                    params={"query": kw, "filter": "CC", "per_page": 12, "sort": "relevant",
                            "fields": "uri,name,link,duration,description,user.name"},
                    timeout=15,
                )
                for v in r.json().get("data", []):
                    vid = v["uri"].split("/")[-1]
                    dur = v.get("duration", 0)
                    blob = f"{v.get('name','')} {v.get('description','') or ''}".lower()
                    if (vid in clipped or dur < 60 or dur > 1800
                            or any(c["id"] == vid for c in candidates)
                            or any(b in blob for b in self.BLOCKLIST)):
                        continue
                    candidates.append({"id": vid, "title": v.get("name", ""),
                                       "channel": v.get("user", {}).get("name", "Vimeo"),
                                       "url": v.get("link"),
                                       "desc": (v.get("description") or "")[:100]})
            except Exception as e:
                print(f"ClipAgent vimeo '{kw}': {e}")
        return self._vet(candidates)

    def _vet(self, candidates):
        """LLM picks the single best on-topic, educational, SFW video — or None."""
        if not candidates:
            return None
        listing = "\n".join(f"{i}: {c['title']} — {c['desc']}" for i, c in enumerate(candidates))
        try:
            pick = generate_text(
                f"From these Creative-Commons videos, pick the ONE best to clip into a short "
                f"Instagram reel about {self.niche}. It MUST be a real person TEACHING, EXPLAINING, "
                f"or DEMONSTRATING something concretely useful — a tutorial/tips/how-to. "
                f"REJECT: brand promos, product trailers, marketing montages, stock-footage reels, "
                f"art films, music videos, hours-long webinars, anything NSFW. Be strict — reply NONE "
                f"if nothing is a genuine value-packed explainer. Reply with ONLY the number or NONE.\n\n{listing}",
                temperature=0,
            ).strip()
            idx = int("".join(ch for ch in pick if ch.isdigit()))
            return candidates[idx] if 0 <= idx < len(candidates) and "NONE" not in pick.upper() else None
        except Exception as e:
            print(f"ClipAgent vet: {e}")
            return None
    def find_cc_video(self):
        """A Creative-Commons niche video not clipped before. Dedups, varies the
        keyword + pick (so it's not the same video every time), and prefers
        English-ish titles."""
        if not self.yt_key:
            return None
        import json
        import random
        from agents._db import get_config
        clipped = set(json.loads(get_config("clipped_videos") or "[]"))
        keywords = list(self.keywords) or ["AI tools"]
        random.shuffle(keywords)
        candidates = []
        for kw in keywords[:5]:
            try:
                r = requests.get(SEARCH, params={
                    "key": self.yt_key, "part": "snippet", "q": kw, "type": "video",
                    "videoLicense": "creativeCommon", "videoDuration": "medium",
                    "order": "viewCount", "maxResults": 10, "relevanceLanguage": "en",
                }, timeout=15)
                for it in r.json().get("items", []):
                    vid = it["id"]["videoId"]
                    if vid in clipped or any(c["id"] == vid for c in candidates):
                        continue
                    t = it["snippet"]["title"]
                    candidates.append({"id": vid, "title": t,
                                       "channel": it["snippet"]["channelTitle"],
                                       "url": f"https://www.youtube.com/watch?v={vid}",
                                       "_en": sum(ord(c) < 128 for c in t) / max(len(t), 1)})
            except Exception as e:
                print(f"ClipAgent search '{kw}': {e}")
        if not candidates:
            return None
        candidates.sort(key=lambda c: c["_en"], reverse=True)  # English-ish titles first
        return random.choice(candidates[:8])  # variety among the best

    def download(self, url, out_base):
        out = f"{out_base}.mp4"
        # `python -m yt_dlp` (not the console script) so it works regardless of PATH.
        # Two mutually-exclusive paths: the android client downloads without a JS
        # runtime or PO token but does NOT support cookies; cookies (needed to get
        # past YouTube's datacenter-IP bot block in CI) require the default
        # cookie-supporting clients. So: cookies -> default clients; else android.
        cmd = [sys.executable, "-m", "yt_dlp",
               "-f", "best[ext=mp4][height<=720]/best[height<=720]/best",
               "--no-playlist"]
        if "vimeo.com" in url:
            # Vimeo doesn't bot-block datacenter IPs — plain download, no auth tricks.
            cmd += ["-o", out, url]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"yt-dlp (vimeo) failed:\n{e.stderr[-1200:]}") from e
            return out
        cookies = os.environ.get("YT_COOKIES_FILE")
        # Priority: PO-token provider (cookie-free, no maintenance) > cookies > android.
        # YT_POT means the bgutil provider is running — yt-dlp's plugin auto-fetches
        # the PO token, so the default web client gets past the bot check. EJS/deno
        # solves the "n" signature challenge in both web paths.
        if os.environ.get("YT_POT"):
            cmd += ["--remote-components", "ejs:github"]
        elif cookies and os.path.exists(cookies):
            cmd += ["--cookies", cookies, "--remote-components", "ejs:github"]
        else:
            cmd += ["--extractor-args", "youtube:player_client=android"]
        cmd += ["-o", out, url]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"yt-dlp failed (YouTube may be blocking this IP — "
                               f"set YT_COOKIES_FILE):\n{e.stderr[-1500:]}") from e
        return out

    # ── transcribe ──────────────────────────────────────────────────
    def transcribe(self, video_path):
        """[{start,end,word}] via faster-whisper. task='translate' forces ENGLISH
        output regardless of the video's spoken language (English in -> English out)."""
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(video_path, task="translate", word_timestamps=True)
        words = []
        for seg in segments:
            if seg.words:
                words += [{"start": w.start, "end": w.end, "word": w.word} for w in seg.words]
            else:  # translate sometimes lacks word timings — fall back to the segment
                words.append({"start": seg.start, "end": seg.end, "word": " " + seg.text.strip()})
        return words

    # ── pick the moment ─────────────────────────────────────────────
    def pick_segment(self, words, title):
        """Gemini -> {start,end,hook,caption} for the best 20-40s clip."""
        lines, chunk, t0 = [], [], None
        for w in words:
            if t0 is None:
                t0 = w["start"]
            chunk.append(w["word"])
            if len(chunk) >= 12:
                lines.append(f"[{t0:.0f}] {''.join(chunk).strip()}")
                chunk, t0 = [], None
        if chunk:
            lines.append(f"[{t0:.0f}] {''.join(chunk).strip()}")
        transcript = "\n".join(lines)[:7000]

        seg = generate_text(
            f'Video "{title}" about {self.niche}. Each line below starts with its '
            f'timestamp in seconds. Pick the single most VALUABLE 20-40 second segment — '
            f'one concrete tip, insight, or how-to that stands alone. AVOID intros, '
            f'outros, branding, sponsor reads, and promotional taglines. Return JSON: '
            f'{{"start": <sec>, "end": <sec>, "hook": "<=8 words", "caption": "reel caption with a save/share CTA"}}.\n\n'
            f'{transcript}',
            system="Short-form video editor. Return only valid JSON.",
            json_response=True, temperature=0.4,
        )
        start = max(0.0, float(seg["start"]))
        end = float(seg["end"])
        end = min(end, start + 60)            # hard cap
        if end - start < 10:                  # too short -> pad
            end = start + 30
        seg["start"], seg["end"] = start, end
        return seg

    # ── cut + reframe + captions ────────────────────────────────────
    # ASS style: big bold white text, thick black outline, MIDDLE-centered
    # (Alignment=5). Styling lives in the file, so no fragile ffmpeg force_style.
    ASS_HEADER = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,DejaVu Sans,82,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,"
        "-1,0,0,0,100,100,0,0,1,5,2,5,80,80,80,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    @staticmethod
    def _ass_time(sec):
        sec = max(0.0, sec)
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h):d}:{int(m):02d}:{s:05.2f}"

    def _write_ass(self, words, start, end, ass_path):
        """Punchy ~3-word centered cues within [start,end], rebased to clip start."""
        cues = [w for w in words if w["end"] > start and w["start"] < end]
        lines, i = [], 0
        while i < len(cues):
            group = cues[i:i + 3]
            a = max(0.0, group[0]["start"] - start)
            b = max(a + 0.4, group[-1]["end"] - start)
            text = "".join(w["word"] for w in group).strip().replace("\n", " ").upper()
            if text:
                lines.append(f"Dialogue: 0,{self._ass_time(a)},{self._ass_time(b)},Default,,0,0,0,,{text}")
            i += 3
        with open(ass_path, "w") as f:
            f.write(self.ASS_HEADER + "\n".join(lines) + "\n")
        return ass_path

    def make_clip(self, video_path, words, seg, out_path):
        """Cut [start,end], crop/scale to 1080x1920, burn styled middle captions.
        Falls back to an uncaptioned (but valid) clip if ffmpeg lacks libass."""
        start, dur = seg["start"], seg["end"] - seg["start"]
        ass_path = os.path.splitext(out_path)[0] + ".ass"
        self._write_ass(words, start, seg["end"], ass_path)
        reframe = "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1080:1920,setsar=1"
        tail = "fps=30,format=yuv420p"
        # ass= carries its own styling — no force_style escaping needed
        attempts = [f"{reframe},ass={ass_path},{tail}", f"{reframe},{tail}"]
        last = None
        for vf in attempts:
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(dur),
                     "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                     "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_path],
                    check=True, capture_output=True, text=True,
                )
                if "ass=" not in vf:
                    print("ClipAgent: captions skipped (ffmpeg has no libass)")
                return out_path
            except subprocess.CalledProcessError as e:
                last = e
        raise RuntimeError(f"ffmpeg make_clip failed:\n{last.stderr[-1200:]}")

    # ── orchestration ───────────────────────────────────────────────
    def run(self):
        """Find -> download -> transcribe -> pick -> clip. Returns dict or None."""
        vid = self.find_video()
        if not vid:
            print("ClipAgent: no CC video found")
            return None
        print(f"ClipAgent: {vid['title']} ({vid['url']})")
        base = os.path.join(self.output_dir, f"clip_{vid['id']}")
        os.makedirs(self.output_dir, exist_ok=True)
        src = self.download(vid["url"], base)
        words = self.transcribe(src)
        if not words:
            print("ClipAgent: empty transcript")
            return None
        seg = self.pick_segment(words, vid["title"])
        clip = self.make_clip(src, words, seg, f"{base}_reel.mp4")
        # remember this video so we never clip it again (dedup)
        import json
        from agents._db import get_config, set_config
        clipped = json.loads(get_config("clipped_videos") or "[]")
        clipped.append(vid["id"])
        set_config("clipped_videos", json.dumps(clipped[-200:]))
        credit = f"\n\n🎬 Clip from \"{vid['title']}\" by {vid['channel']} (CC BY, via YouTube)"
        return {"path": clip, "hook": seg["hook"],
                "caption": (seg["caption"] + credit).strip()}


if __name__ == "__main__":
    # source step is testable without the heavy deps; full run needs yt-dlp + whisper
    import yaml
    config = yaml.safe_load(open("config.yaml"))
    vid = ClipAgent(config).find_video()
    assert vid is None or {"id", "title", "channel", "url"} <= vid.keys(), vid
    print("clip_agent self-check OK ->", vid["title"] if vid else "no key/result")

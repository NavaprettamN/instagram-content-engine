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
        self.keywords = config.get("keywords", [])
        self.niche = config.get("niche", "")
        self.output_dir = config.get("output_dir", "./generated_content")

    # ── source ──────────────────────────────────────────────────────
    def find_cc_video(self):
        """Top Creative-Commons, medium-length niche video, or None."""
        if not self.yt_key:
            return None
        for kw in self.keywords[:3]:
            r = requests.get(SEARCH, params={
                "key": self.yt_key, "part": "snippet", "q": kw, "type": "video",
                "videoLicense": "creativeCommon", "videoDuration": "medium",  # 4-20 min
                "order": "viewCount", "maxResults": 5, "relevanceLanguage": "en",
            }, timeout=15)
            for it in r.json().get("items", []):
                vid = it["id"]["videoId"]
                return {"id": vid, "title": it["snippet"]["title"],
                        "channel": it["snippet"]["channelTitle"],
                        "url": f"https://www.youtube.com/watch?v={vid}"}
        return None

    def download(self, url, out_base):
        out = f"{out_base}.mp4"
        # `python -m yt_dlp` (not the console script) so it works regardless of PATH.
        # android player_client downloads without a JS runtime or PO token.
        # YouTube bot-blocks datacenter IPs (e.g. CI); set YT_COOKIES_FILE to a
        # Netscape cookies.txt from a logged-in session to get past it there.
        cmd = [sys.executable, "-m", "yt_dlp",
               "--extractor-args", "youtube:player_client=android",
               "-f", "best[ext=mp4][height<=720]/best[height<=720]/best",
               "--no-playlist"]
        cookies = os.environ.get("YT_COOKIES_FILE")
        if cookies and os.path.exists(cookies):
            cmd += ["--cookies", cookies]
        cmd += ["-o", out, url]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"yt-dlp failed (YouTube may be blocking this IP — "
                               f"set YT_COOKIES_FILE):\n{e.stderr[-1500:]}") from e
        return out

    # ── transcribe ──────────────────────────────────────────────────
    def transcribe(self, video_path):
        """[{start,end,word}] via faster-whisper base (CPU, int8)."""
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(video_path, word_timestamps=True)
        return [{"start": w.start, "end": w.end, "word": w.word}
                for seg in segments for w in (seg.words or [])]

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
            f'timestamp in seconds. Pick the single most compelling 20-40 second '
            f'segment to clip as an Instagram reel. Return JSON: '
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
    @staticmethod
    def _ts(sec):
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"

    def _write_srt(self, words, start, end, srt_path):
        """Caption lines (~6 words) within [start,end], times rebased to clip start."""
        seg = [w for w in words if w["end"] > start and w["start"] < end]
        out, idx, i = [], 1, 0
        while i < len(seg):
            group = seg[i:i + 6]
            a = max(0.0, group[0]["start"] - start)
            b = max(a + 0.4, group[-1]["end"] - start)
            text = "".join(w["word"] for w in group).strip()
            out.append(f"{idx}\n{self._ts(a)} --> {self._ts(b)}\n{text}\n")
            idx += 1
            i += 6
        with open(srt_path, "w") as f:
            f.write("\n".join(out))
        return srt_path

    def make_clip(self, video_path, words, seg, out_path):
        """Cut [start,end], crop/scale to 1080x1920, burn captions.
        Falls back to an uncaptioned (but valid) clip if ffmpeg lacks libass."""
        start, dur = seg["start"], seg["end"] - seg["start"]
        srt_path = os.path.splitext(out_path)[0] + ".srt"
        self._write_srt(words, start, seg["end"], srt_path)
        reframe = "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1080:1920,setsar=1"
        tail = "fps=30,format=yuv420p"
        # plain subtitles= (default style) avoids the force_style comma-escaping trap
        attempts = [f"{reframe},subtitles={srt_path},{tail}", f"{reframe},{tail}"]
        last = None
        for vf in attempts:
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(dur),
                     "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                     "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_path],
                    check=True, capture_output=True, text=True,
                )
                if "subtitles" not in vf:
                    print("ClipAgent: captions skipped (ffmpeg has no libass)")
                return out_path
            except subprocess.CalledProcessError as e:
                last = e
        raise RuntimeError(f"ffmpeg make_clip failed:\n{last.stderr[-1200:]}")

    # ── orchestration ───────────────────────────────────────────────
    def run(self):
        """Find -> download -> transcribe -> pick -> clip. Returns dict or None."""
        vid = self.find_cc_video()
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
        credit = f"\n\n🎬 Clip from \"{vid['title']}\" by {vid['channel']} (CC BY, via YouTube)"
        return {"path": clip, "hook": seg["hook"],
                "caption": (seg["caption"] + credit).strip()}


if __name__ == "__main__":
    # source step is testable without the heavy deps; full run needs yt-dlp + whisper
    import yaml
    config = yaml.safe_load(open("config.yaml"))
    vid = ClipAgent(config).find_cc_video()
    assert vid is None or {"id", "title", "channel", "url"} <= vid.keys(), vid
    print("clip_agent self-check OK ->", vid["title"] if vid else "no key/result")

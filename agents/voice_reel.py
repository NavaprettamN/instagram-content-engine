"""Original AI reel: script -> free neural voiceover -> synced middle captions
-> branded vertical video. No YouTube, no cookies, fully original ($0).

Voice = edge-tts (free Microsoft neural voices, no key). Captions are synced
from edge-tts SentenceBoundary timings (word-level isn't emitted in 7.x, so words
are distributed evenly within each sentence). Background is the brand colour with
the hook as a top banner; music is ducked under the voice.
"""
import os
import asyncio
import subprocess
from agents._captions import write_ass


class VoiceReelAgent:
    def __init__(self, config):
        c = config.get("brand_colors", {})
        self.bg = c.get("background", "#1a1a2e").replace("#", "0x")
        self.accent = c.get("accent", "#e94560").replace("#", "0x")
        self.voice = config.get("reel_voice", "en-US-AriaNeural")
        self.rate = config.get("reel_voice_rate", "+12%")  # energetic + shorter

    def _motion_overlays(self, dur):
        """ffmpeg motion-graphic elements (reliable, no deps): a title underline
        that wipes in over the first 0.5s, and a progress bar that fills over the
        whole reel. Commas inside expressions are escaped for the filtergraph."""
        ul = (f"drawbox=x='540-160*min(t/0.5\\,1)':y=235:w='320*min(t/0.5\\,1)':"
              f"h=9:color={self.accent}@0.95:t=fill")
        bar = (f"drawbox=x=0:y=ih-14:w='iw*min(t/{dur:.2f}\\,1)':h=14:"
               f"color={self.accent}@0.85:t=fill")
        return f",{ul},{bar}"

    def _tts(self, text, mp3_path):
        """Synthesize voiceover; return word cues from sentence-level timings."""
        import edge_tts

        async def go():
            comm = edge_tts.Communicate(text, self.voice, rate=self.rate)
            sents = []
            with open(mp3_path, "wb") as f:
                async for ch in comm.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
                    elif ch["type"] == "SentenceBoundary":
                        sents.append((ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]))
            return sents

        sents = asyncio.run(go())
        words = []
        for start, dur, txt in sents:
            toks = txt.split()
            per = dur / max(len(toks), 1)
            for i, w in enumerate(toks):
                words.append({"start": start + i * per, "end": start + (i + 1) * per, "word": " " + w})
        return words

    def build(self, hook, script, out_path, music_path=None, broll_paths=None):
        """script -> voiceover + captions over moving b-roll (or branded solid bg
        if no b-roll) + ducked music -> mp4."""
        base = os.path.splitext(out_path)[0]
        voice_mp3 = base + "_voice.mp3"
        # safety cap: reels must stay short even if the model overshoots
        script = " ".join(script.split()[:70])
        words = self._tts(script, voice_mp3)
        dur = (words[-1]["end"] if words else 30.0) + 0.8
        ass = write_ass(words, base + ".ass", title=hook)

        broll_paths = broll_paths or []
        # video inputs first, then voice, then (optional) music — track indices
        vid_in, n = [], len(broll_paths)
        for p in broll_paths:
            vid_in += ["-i", p]
        if not broll_paths:
            vid_in = ["-f", "lavfi", "-i", f"color=c={self.bg}:s=1080x1920:d={dur:.2f}:r=30"]
            n = 1
        voice_idx = n
        base_in = [*vid_in, "-i", voice_mp3]
        if music_path:
            base_in += ["-stream_loop", "-1", "-i", music_path]
            afilter = f"[{voice_idx+1}:a]volume=0.16[m];[{voice_idx}:a][m]amix=inputs=2:duration=first[a]"
        else:
            afilter = f"[{voice_idx}:a]anull[a]"

        # build the moving background from b-roll: each clip cropped to 1080x1920,
        # trimmed to its slice of the voice duration, concatenated, last frame
        # cloned to cover any shortfall, then darkened for caption legibility.
        if broll_paths:
            seg = dur / n + 1.0
            parts = []
            for i in range(n):
                parts.append(
                    f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                    f"crop=1080:1920,setsar=1,trim=duration={seg:.2f},"
                    f"setpts=PTS-STARTPTS[v{i}]")
            cat = "".join(f"[v{i}]" for i in range(n))
            parts.append(f"{cat}concat=n={n}:v=1:a=0[cat]")
            # fps=30 forces constant frame rate — concat of mixed-fps stock clips
            # is otherwise VFR, which Instagram rejects with a container ERROR.
            bg_chain = ("[cat]tpad=stop_mode=clone:stop_duration=6,"
                        f"trim=duration={dur:.2f},setpts=PTS-STARTPTS,fps=30,"
                        "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.4:t=fill")
            pre = ";".join(parts) + ";"
        else:
            bg_chain = "[0:v]"
            pre = ""
        bg_chain += self._motion_overlays(dur)  # title underline wipe + progress bar

        # try with captions; fall back to no-captions if ffmpeg lacks libass
        last = None
        for cap in (f",ass={ass},format=yuv420p[v]", ",format=yuv420p[v]"):
            vfilter = f"{pre}{bg_chain}{cap}"
            cmd = ["ffmpeg", "-y", *base_in,
                   "-filter_complex", f"{vfilter};{afilter}", "-map", "[v]", "-map", "[a]",
                   "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out_path]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                if "ass=" not in cap:
                    print("VoiceReelAgent: captions skipped (ffmpeg has no libass)")
                return out_path
            except subprocess.CalledProcessError as e:
                last = e
        raise RuntimeError(f"voice_reel ffmpeg failed:\n{last.stderr[-1500:]}")

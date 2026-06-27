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
        self.voice = config.get("reel_voice", "en-US-AriaNeural")
        self.rate = config.get("reel_voice_rate", "+12%")  # energetic + shorter

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

    def build(self, hook, script, out_path, music_path=None):
        """script -> voiceover + captions over a branded bg + ducked music -> mp4."""
        base = os.path.splitext(out_path)[0]
        voice_mp3 = base + "_voice.mp3"
        # safety cap: reels must stay short even if the model overshoots
        script = " ".join(script.split()[:70])
        words = self._tts(script, voice_mp3)
        dur = (words[-1]["end"] if words else 30.0) + 0.8
        ass = write_ass(words, base + ".ass", title=hook)

        base_in = ["-f", "lavfi", "-i", f"color=c={self.bg}:s=1080x1920:d={dur:.2f}:r=30",
                   "-i", voice_mp3]
        if music_path:
            base_in += ["-stream_loop", "-1", "-i", music_path]
            afilter = "[2:a]volume=0.16[m];[1:a][m]amix=inputs=2:duration=first[a]"
        else:
            afilter = "[1:a]anull[a]"
        # try with captions; fall back to no-captions if ffmpeg lacks libass
        last = None
        for vfilter in (f"[0:v]ass={ass},format=yuv420p[v]", "[0:v]format=yuv420p[v]"):
            cmd = ["ffmpeg", "-y", *base_in,
                   "-filter_complex", f"{vfilter};{afilter}", "-map", "[v]", "-map", "[a]",
                   "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out_path]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                if "ass=" not in vfilter:
                    print("VoiceReelAgent: captions skipped (ffmpeg has no libass)")
                return out_path
            except subprocess.CalledProcessError as e:
                last = e
        raise RuntimeError(f"voice_reel ffmpeg failed:\n{last.stderr[-1500:]}")

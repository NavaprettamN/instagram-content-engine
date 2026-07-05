"""Ad-style scene reel (E5): voiceover-paced scene cuts rendered with Remotion.

script -> edge-tts (sentence timings) -> LLM scene plan (headline + image prompt
per sentence) -> visuals (Pollinations free AI image, alternating with Pexels
b-roll video; gradient as last resort) -> Remotion `Scenes` render -> ffmpeg mux
of voice + ducked music + whoosh SFX on every cut.

Everything visual is best-effort with fallbacks; a total failure raises so the
generate.yml caller can fall back to the plain b-roll voice reel.
"""
import asyncio
import json
import os
import re
import shutil
import subprocess
import time
import urllib.parse
import uuid

import requests

from agents._llm import generate_text
from agents.design_agent import PALETTES

REMOTION_DIR = os.path.join(os.path.dirname(__file__), "..", "remotion")
SFX_WHOOSH = os.path.join(os.path.dirname(__file__), "..", "assets", "sfx", "whoosh.wav")
POLLINATIONS = "https://image.pollinations.ai/prompt/"
FPS = 30


class SceneReelAgent:
    def __init__(self, config):
        self.config = config or {}
        self.handle = self.config.get("instagram_handle", "")
        self.voice = self.config.get("reel_voice", "en-US-AriaNeural")
        self.rate = self.config.get("reel_voice_rate", "+12%")

    # ── voice ──────────────────────────────────────────────────────
    def _tts_sentences(self, text, mp3_path):
        """Synthesize the voiceover; return [(start_s, dur_s, sentence)]."""
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
        # merge blips: a scene under ~1.4s can't register — fold into the previous
        merged = []
        for s in sents:
            if merged and s[1] < 1.4:
                p = merged[-1]
                merged[-1] = (p[0], (s[0] + s[1]) - p[0], p[2] + " " + s[2])
            else:
                merged.append(s)
        return merged

    # ── scene plan ─────────────────────────────────────────────────
    def _scene_plan(self, sentences):
        """One LLM call: per sentence, an on-screen headline + a cinematic image
        prompt + a stock-video search term."""
        numbered = "\n".join(f"{i+1}. {s}" for i, (_, _, s) in enumerate(sentences))
        plan = generate_text(
            f"""You are art-directing a fast-cut vertical video ad. For EACH narration
line below, design its full-screen scene.

NARRATION LINES:
{numbered}

Return JSON: {{"scenes": [{{
  "headline": "3-5 word on-screen text distilling the line — punchy, no ending period",
  "image_prompt": "one cinematic photo prompt matching the line: concrete subject + setting + mood + lighting, photorealistic, vertical 9:16, NO text in image",
  "video_term": "2-4 word stock-footage search phrase for the same beat"
}}, ...]}}
Exactly {len(sentences)} scenes, in order. Vary subjects/settings between scenes.""",
            system="Expert short-form video art director. Return only valid JSON.",
            json_response=True, temperature=0.7,
        )
        scenes = plan.get("scenes", []) if isinstance(plan, dict) else []
        # pad/trim defensively so zip never drops a sentence
        while len(scenes) < len(sentences):
            scenes.append({})
        return scenes[:len(sentences)]

    # ── visuals ────────────────────────────────────────────────────
    def _ai_image(self, prompt, dest, style):
        """Pollinations (free, keyless). Returns dest or None."""
        url = POLLINATIONS + urllib.parse.quote(f"{prompt}, {style}")
        try:
            r = requests.get(url, params={"width": 1080, "height": 1920, "nologo": "true",
                                          "model": "flux"}, timeout=90)
            r.raise_for_status()
            if len(r.content) > 10_000:
                with open(dest, "wb") as f:
                    f.write(r.content)
                return dest
        except Exception as e:
            print(f"SceneReel: image gen failed ({str(e)[:100]})")
        return None

    # ── build ──────────────────────────────────────────────────────
    def build(self, content, out_path, idea_id=0, music_path=None, broll=None):
        top, bottom, accent, text, text2 = PALETTES[idea_id % len(PALETTES)]
        colors = {"bgTop": top, "bgBottom": bottom, "accent": accent, "text": text, "text2": text2}
        style = (f"cinematic photo, moody dramatic lighting with {accent} accent tones, "
                 f"shallow depth of field, high contrast, photorealistic")

        base = os.path.splitext(out_path)[0]
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        script = " ".join(str(content.get("script", "")).split()[:70])
        if not script:
            raise ValueError("scene reel needs content['script']")
        voice_mp3 = base + "_voice.mp3"
        sentences = self._tts_sentences(script, voice_mp3)
        if not sentences:
            raise RuntimeError("TTS produced no sentence timings")
        plan = self._scene_plan(sentences)

        # stage assets where the remotion dev server can see them
        uid = uuid.uuid4().hex[:8]
        pub = os.path.join(REMOTION_DIR, "public", "gen", uid)
        os.makedirs(pub, exist_ok=True)
        try:
            scenes = []
            for i, ((start, dur, sent), sc) in enumerate(zip(sentences, plan)):
                kind, src = "none", ""
                # alternate AI image / b-roll video; each falls back to the other
                want_video = (i % 2 == 1) and broll is not None
                if want_video:
                    clip = broll.fetch_one(sc.get("video_term") or sent[:40], variant=idea_id + i)
                    if clip:
                        kind, src = "video", f"gen/{uid}/{os.path.basename(clip)}"
                        shutil.copy(clip, os.path.join(pub, os.path.basename(clip)))
                if kind == "none" and sc.get("image_prompt"):
                    dest = os.path.join(pub, f"scene{i}.jpg")
                    if self._ai_image(sc["image_prompt"], dest, style):
                        kind, src = "image", f"gen/{uid}/scene{i}.jpg"
                    time.sleep(3)  # be polite to the free API
                if kind == "none" and broll is not None:  # image failed -> try video anyway
                    clip = broll.fetch_one(sc.get("video_term") or sent[:40], variant=idea_id + i)
                    if clip:
                        kind, src = "video", f"gen/{uid}/{os.path.basename(clip)}"
                        shutil.copy(clip, os.path.join(pub, os.path.basename(clip)))
                headline = sc.get("headline") or " ".join(sent.split()[:5])
                headline = re.sub(r"[.!]+$", "", headline.strip())
                scenes.append({"src": src, "kind": kind, "headline": headline,
                               "from": round(start * FPS), "dur": round(dur * FPS)})
            scenes[-1]["dur"] += round(1.2 * FPS)  # breathing room for the outro CTA

            props_path = os.path.abspath(base + "_props.json")
            with open(props_path, "w") as f:
                json.dump({"scenes": scenes, "handle": self.handle, "colors": colors}, f)
            silent = os.path.abspath(base + "_anim.mp4")
            r = subprocess.run(
                ["npx", "remotion", "render", "src/index.ts", "Scenes", silent,
                 f"--props={props_path}", "--log=error", "--timeout=120000"],
                cwd=REMOTION_DIR, capture_output=True, text=True,
            )
            if r.returncode != 0:
                raise RuntimeError(f"remotion render failed:\n{(r.stderr or r.stdout)[-1500:]}")
        finally:
            shutil.rmtree(pub, ignore_errors=True)

        # mux: voice + ducked music + a whoosh on every cut (scene 2..n)
        inputs, n_in = ["-i", silent, "-i", voice_mp3], 2
        labels, filters = ["[voice]"], ["[1:a]anull[voice]"]
        if music_path:
            inputs += ["-stream_loop", "-1", "-i", music_path]
            filters.append(f"[{n_in}:a]volume=0.13[m]")
            labels.append("[m]")
            n_in += 1
        if os.path.exists(SFX_WHOOSH):
            for j, s in enumerate(scenes[1:]):
                inputs += ["-i", SFX_WHOOSH]
                ms = max(int(s["from"] / FPS * 1000) - 150, 0)  # lead the cut slightly
                filters.append(f"[{n_in}:a]adelay={ms}|{ms},volume=0.35[s{j}]")
                labels.append(f"[s{j}]")
                n_in += 1
        filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0[a]")
        r = subprocess.run(
            ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", out_path],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"scene mux ffmpeg failed:\n{r.stderr[-1200:]}")
        return out_path


if __name__ == "__main__":
    # ponytail: real end-to-end self-check (needs node, ffmpeg, network + LLM key).
    import yaml
    from agents.broll_agent import BRollAgent
    cfg = yaml.safe_load(open("config.yaml"))
    a = SceneReelAgent(cfg)
    content = {"script": ("You are wasting two hours every single day. AI can write your "
                          "emails in seconds. It can plan your whole week in one tap. "
                          "Start with just one tool today. Follow for more.")}
    from agents.music_agent import MusicAgent
    music = MusicAgent(cfg).pick_track("test", "/tmp/scene_check/music.mp3", seed=3)
    p = a.build(content, "/tmp/scene_check/reel.mp4", idea_id=3,
                music_path=(music["path"] if music else None),
                broll=BRollAgent({"output_dir": "/tmp/scene_check"}))
    assert os.path.getsize(p) > 200_000, p
    print("scene_reel self-check OK:", p)

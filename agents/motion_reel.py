"""Animated-insight reels rendered with Remotion (remotion/ Node project).

Takes the motion content JSON from ContentAgent.generate_motion() and renders
the matching template (KineticList or BigStat) at 1080x1920/30fps, reusing the
carousel palette rotation so reels and carousels share the brand look. Music
(or a silent AAC track — Instagram rejects audio-less containers) is muxed in
with ffmpeg afterwards.

Raises on failure; the generate.yml caller falls back to a b-roll voice reel,
so a broken Node setup can never block the daily mix.
"""
import json
import os
import subprocess
from agents.design_agent import PALETTES

REMOTION_DIR = os.path.join(os.path.dirname(__file__), "..", "remotion")


class MotionReelAgent:
    def __init__(self, config):
        self.handle = config.get("instagram_handle", "")

    def _props(self, content, idea_id):
        top, bottom, accent, text, text2 = PALETTES[idea_id % len(PALETTES)]
        colors = {"bgTop": top, "bgBottom": bottom, "accent": accent, "text": text, "text2": text2}
        if content.get("template") == "stat" and content.get("stat") is not None:
            return "BigStat", {
                "stat": int(content["stat"]),
                "suffix": str(content.get("suffix") or ""),
                "label": content.get("label") or content.get("hook", ""),
                "lines": [str(x) for x in (content.get("lines") or [])][:3],
                "handle": self.handle, "colors": colors,
            }
        return "KineticList", {
            "title": content.get("hook", ""),
            "items": [str(x) for x in (content.get("items") or [])][:5],
            "handle": self.handle, "colors": colors,
        }

    def build(self, content, out_path, idea_id=0, music_path=None):
        """Render the animation and mux music. Returns out_path or raises."""
        base = os.path.splitext(out_path)[0]
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        template, props = self._props(content, idea_id)
        props_path = os.path.abspath(base + "_props.json")
        with open(props_path, "w") as f:
            json.dump(props, f)

        silent = os.path.abspath(base + "_anim.mp4")
        r = subprocess.run(
            ["npx", "remotion", "render", "src/index.ts", template, silent,
             f"--props={props_path}", "--log=error"],
            cwd=REMOTION_DIR, capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise RuntimeError(f"remotion render failed:\n{(r.stderr or r.stdout)[-1500:]}")

        if music_path:
            audio_in = ["-stream_loop", "-1", "-i", music_path]
            afilter = ["-filter_complex", "[1:a]volume=0.35[a]", "-map", "0:v", "-map", "[a]"]
        else:
            audio_in = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
            afilter = ["-map", "0:v", "-map", "1:a"]
        subprocess.run(
            ["ffmpeg", "-y", "-i", silent, *audio_in, *afilter,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
             "-movflags", "+faststart", out_path],
            check=True, capture_output=True, text=True,
        )
        return out_path


if __name__ == "__main__":
    # ponytail: self-check renders both templates for real (needs node + ffmpeg).
    a = MotionReelAgent({"instagram_handle": "@contentengine2"})
    p1 = a.build({"template": "list", "hook": "5 AI tools that save hours",
                  "items": ["Draft emails in seconds", "Summarize any meeting",
                            "Auto-organize your notes", "Plan your week in 1 tap"]},
                 "/tmp/motion_check/list.mp4", idea_id=1)
    p2 = a.build({"template": "stat", "stat": 87, "suffix": "%",
                  "label": "of tasks can be automated",
                  "lines": ["Most people automate none", "Start with your inbox"]},
                 "/tmp/motion_check/stat.mp4", idea_id=2)
    for p in (p1, p2):
        assert os.path.getsize(p) > 100_000, p
    print("motion_reel self-check OK:", p1, p2)

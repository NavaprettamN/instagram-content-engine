"""Render carousel slides into a vertical Reel MP4 — $0, ffmpeg only.

ponytail: raw ffmpeg via subprocess (preinstalled on the Actions runner) instead
of moviepy — moviepy is heavy and flaky. Hard cuts, no crossfade: a slideshow
reel is plenty for IG and far more robust across ffmpeg versions. Uses
`-loop 1 -t` per image + the concat *filter* (the concat *demuxer*'s `duration`
directive is unreliable for timed stills).

Note: the IG content-publishing API cannot attach Instagram's trending audio —
only audio baked into this MP4. Pass audio_path for royalty-free music, else the
reel gets a silent track (so the file always has an audio stream).
"""
import os
import subprocess

REEL_W, REEL_H = 1080, 1920  # 9:16 vertical


class VideoAgent:
    def __init__(self, config):
        self.output_dir = config.get("output_dir", "./generated_content")
        self.seconds_per_slide = config.get("reel_seconds_per_slide", 2.5)
        self.bg = config.get("brand_colors", {}).get("background", "#1a1a2e").replace("#", "0x")

    def slides_to_reel(self, image_paths, out_path=None, audio_path=None, fps=30):
        """Ordered slide PNGs -> 1080x1920 MP4. Returns out_path. Raises on ffmpeg error."""
        if not image_paths:
            raise ValueError("slides_to_reel: no image_paths given")
        out_path = out_path or os.path.join(self.output_dir, "reel.mp4")
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        dur = self.seconds_per_slide
        n = len(image_paths)

        cmd = ["ffmpeg", "-y"]
        for p in image_paths:
            cmd += ["-loop", "1", "-t", str(dur), "-i", os.path.abspath(p)]
        if audio_path:
            # loop the track so a short song can't truncate the slideshow;
            # -shortest below then trims audio to the (finite) video length.
            cmd += ["-stream_loop", "-1", "-i", os.path.abspath(audio_path)]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

        # scale+letterbox each square slide onto 9:16 with the brand bg, then concat
        per = (f"scale={REEL_W}:-2,pad={REEL_W}:{REEL_H}:(ow-iw)/2:(oh-ih)/2:"
               f"color={self.bg},setsar=1,fps={fps},format=yuv420p")
        chains = "".join(f"[{i}:v]{per}[v{i}];" for i in range(n))
        concat = "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
        filter_complex = chains + concat

        cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", f"{n}:a",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out_path]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg failed:\n{e.stderr[-1500:]}") from e
        return out_path


if __name__ == "__main__":
    # self-check: render the first existing carousel folder and verify the MP4 is
    # real (non-empty + has a video stream). Needs ffmpeg + at least one carousel.
    import glob
    import yaml
    config = yaml.safe_load(open("config.yaml"))
    folders = sorted(glob.glob(os.path.join(config.get("output_dir", "./generated_content"), "carousel_*")))
    assert folders, "no carousel_* folders to test with"
    slides = sorted(glob.glob(os.path.join(folders[-1], "*.png")))
    assert slides, f"no slides in {folders[-1]}"
    va = VideoAgent(config)
    out = va.slides_to_reel(slides, out_path="/tmp/reel_selfcheck.mp4")
    assert os.path.getsize(out) > 10_000, "reel suspiciously small"
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,codec_name", "-of", "csv=p=0", out],
        capture_output=True, text=True,
    ).stdout.strip()
    assert "1080,1920" in probe, f"unexpected video stream: {probe}"
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
    expected = len(slides) * va.seconds_per_slide
    assert abs(dur - expected) < 1.0, f"duration {dur:.1f}s != expected {expected:.1f}s"
    print(f"video_agent self-check OK -> {out} ({probe}, {dur:.1f}s for {len(slides)} slides)")

"""Shared ASS subtitle builder: big bold MIDDLE-centered word captions, plus an
optional top title banner. Styling lives in the file so ffmpeg needs no fragile
force_style escaping. Used by both the YouTube clipper and the voice-reel agent."""

_HEADER = (
    "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
    "[V4+ Styles]\n"
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
    "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
    "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    # captions: white, thick black outline, dead-center (Alignment 5)
    "Style: Default,DejaVu Sans,84,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,"
    "-1,0,0,0,100,100,0,0,1,5,2,5,80,80,80,1\n"
    # title: white on a translucent box, top-center (Alignment 8)
    "Style: Title,DejaVu Sans,58,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,"
    "-1,0,0,0,100,100,0,0,3,6,0,8,70,70,150,1\n\n"
    "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
)


def _t(sec):
    sec = max(0.0, sec)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):d}:{int(m):02d}:{s:05.2f}"


def write_ass(words, ass_path, offset=0.0, words_per_cue=3, title=None):
    """words: [{start,end,word}] (seconds). offset is subtracted (clip rebasing).
    title: optional hook shown as a top banner for the whole clip."""
    lines = []
    if title:
        end = (words[-1]["end"] - offset) if words else 30.0
        lines.append(f"Dialogue: 0,{_t(0)},{_t(end)},Title,,0,0,0,,{title.replace(chr(10),' ').strip()}")
    i = 0
    while i < len(words):
        g = words[i:i + words_per_cue]
        a = max(0.0, g[0]["start"] - offset)
        b = max(a + 0.4, g[-1]["end"] - offset)
        text = "".join(w["word"] for w in g).strip().replace("\n", " ").upper()
        if text:
            lines.append(f"Dialogue: 0,{_t(a)},{_t(b)},Default,,0,0,0,,{text}")
        i += words_per_cue
    with open(ass_path, "w") as f:
        f.write(_HEADER + "\n".join(lines) + "\n")
    return ass_path

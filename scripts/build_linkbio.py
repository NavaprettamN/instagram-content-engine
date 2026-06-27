"""Build the link-in-bio landing page (static HTML) for GitHub Pages.

Renders config.link_in_bio into _site/index.html using the brand colors. The
"Latest Post" link auto-fills with the newest IG permalink (best-effort via the
Meta API); links with no URL yet (affiliate/lead-magnet/product placeholders)
are skipped until you fill them in config.yaml.

    python -m scripts.build_linkbio
"""
import os
import html
import requests
import yaml
from dotenv import load_dotenv

load_dotenv()

OUT_DIR = "_site"


def latest_permalink():
    """Newest IG media permalink, or None (best-effort — never blocks the build)."""
    tok = os.environ.get("META_ACCESS_TOKEN")
    uid = os.environ.get("INSTAGRAM_USER_ID")
    if not (tok and uid):
        return None
    try:
        r = requests.get(f"https://graph.instagram.com/v21.0/{uid}/media",
                         params={"fields": "permalink", "limit": 1, "access_token": tok}, timeout=15)
        data = r.json().get("data", [])
        return data[0]["permalink"] if data else None
    except Exception as e:
        print(f"build_linkbio: permalink fetch failed ({e})")
        return None


def render(cfg):
    bio = cfg.get("link_in_bio", {})
    colors = cfg.get("brand_colors", {})
    bg = colors.get("background", "#1a1a2e")
    card = colors.get("secondary_bg", "#16213e")
    accent = colors.get("accent", "#e94560")
    text = colors.get("text_primary", "#ffffff")
    latest = latest_permalink() or bio.get("profile_url", "#")

    buttons = []
    for link in bio.get("links", []):
        url = link.get("url") or ""
        if not url and "latest" in link.get("label", "").lower():
            url = latest
        if not url:
            continue  # placeholder not ready yet
        label = html.escape(f'{link.get("emoji","")} {link.get("label","")}'.strip())
        buttons.append(
            f'<a class="btn" href="{html.escape(url)}" target="_blank" rel="noopener">{label}</a>'
        )

    title = html.escape(bio.get("title", ""))
    tagline = html.escape(bio.get("tagline", ""))
    profile = html.escape(bio.get("profile_url", "#"))
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background:{bg}; color:{text}; font-family:-apple-system,Segoe UI,Roboto,sans-serif;
         min-height:100vh; display:flex; justify-content:center; padding:48px 20px; }}
  .wrap {{ width:100%; max-width:480px; text-align:center; }}
  h1 {{ font-size:1.6rem; margin-bottom:8px; }}
  p.tag {{ color:#a0a0a0; margin-bottom:32px; font-size:1rem; }}
  .btn {{ display:block; background:{card}; color:{text}; text-decoration:none;
         padding:18px; margin:14px 0; border-radius:14px; font-size:1.05rem; font-weight:600;
         border:1px solid rgba(255,255,255,.06); transition:transform .08s, background .2s; }}
  .btn:hover {{ background:{accent}; transform:translateY(-2px); }}
  footer {{ margin-top:36px; }}
  footer a {{ color:{accent}; text-decoration:none; font-weight:600; }}
</style></head>
<body><div class="wrap">
  <h1>{title}</h1>
  <p class="tag">{tagline}</p>
  {chr(10).join("  " + b for b in buttons)}
  <footer><a href="{profile}" target="_blank" rel="noopener">@ Follow on Instagram</a></footer>
</div></body></html>
"""


def main():
    cfg = yaml.safe_load(open("config.yaml"))
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "index.html")
    with open(out, "w") as f:
        f.write(render(cfg))
    print(f"build_linkbio: wrote {out}")


if __name__ == "__main__":
    main()

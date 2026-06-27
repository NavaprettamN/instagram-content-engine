"""Build the link-in-bio funnel (static HTML) for GitHub Pages.

Writes _site/index.html (the bio links) and, if affiliate tools are configured,
_site/tools.html (the "AI Tools I Recommend" page). The bio's "Latest Post" link
auto-fills with the newest IG permalink; its affiliate slot auto-links to
tools.html. Affiliate URLs get UTM tags for click visibility. Empty-URL bio
links (unfilled placeholders) are skipped.

    python -m scripts.build_linkbio
"""
import os
import json
import html
import requests
import yaml

try:  # local convenience; in CI the env vars are passed directly
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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


def add_utm(url, aff):
    if not url:
        return url
    sep = "&" if "?" in url else "?"
    return (f"{url}{sep}utm_source={aff.get('utm_source','instagram')}"
            f"&utm_medium=affiliate&utm_campaign={aff.get('utm_campaign','bio')}")


def _shell(colors, title, tagline, inner_html, footer_html):
    bg = colors.get("background", "#1a1a2e")
    card = colors.get("secondary_bg", "#16213e")
    accent = colors.get("accent", "#e94560")
    text = colors.get("text_primary", "#ffffff")
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
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
  .btn small {{ display:block; font-weight:400; font-size:.82rem; color:#a0a0a0; margin-top:5px; }}
  .disclosure {{ color:#777; font-size:.75rem; margin:18px 4px 0; line-height:1.4; }}
  footer {{ margin-top:34px; }}
  footer a {{ color:{accent}; text-decoration:none; font-weight:600; }}
</style></head>
<body><div class="wrap">
  <h1>{html.escape(title)}</h1>
  <p class="tag">{html.escape(tagline)}</p>
{inner_html}
  <footer>{footer_html}</footer>
</div></body></html>
"""


def load_lead_magnet():
    try:
        with open("data/lead_magnet.json") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return []


def render_bio(cfg, has_tools, has_guide):
    bio = cfg.get("link_in_bio", {})
    latest = latest_permalink() or bio.get("profile_url", "#")
    buttons = []
    for link in bio.get("links", []):
        url = link.get("url") or ""
        label_l = link.get("label", "").lower()
        if not url and "latest" in label_l:
            url = latest
        elif not url and has_tools and "recommend" in label_l:
            url = "tools.html"  # auto-link the affiliate slot
        elif not url and has_guide and "free" in label_l:
            url = "guide.html"  # auto-link the lead-magnet slot
        if not url:
            continue
        label = html.escape(f'{link.get("emoji","")} {link.get("label","")}'.strip())
        ext = "" if url in ("tools.html", "guide.html") else ' target="_blank" rel="noopener"'
        buttons.append(f'  <a class="btn" href="{html.escape(url)}"{ext}>{label}</a>')
    profile = html.escape(bio.get("profile_url", "#"))
    footer = f'<a href="{profile}" target="_blank" rel="noopener">@ Follow on Instagram</a>'
    return _shell(cfg.get("brand_colors", {}), bio.get("title", ""),
                  bio.get("tagline", ""), "\n".join(buttons), footer)


def render_tools(cfg):
    aff = cfg.get("affiliate", {})
    cards = []
    for t in aff.get("tools", []):
        url = html.escape(add_utm(t.get("url", ""), aff))
        name = html.escape(f'{t.get("emoji","")} {t.get("name","")}'.strip())
        blurb = html.escape(t.get("blurb", ""))
        cards.append(f'  <a class="btn" href="{url}" target="_blank" rel="noopener sponsored">'
                     f'{name}<small>{blurb}</small></a>')
    cards.append('  <p class="disclosure">Some links above are affiliate links — '
                 'I may earn a small commission at no extra cost to you. I only '
                 'recommend tools I actually use.</p>')
    footer = '<a href="index.html">&larr; Back</a>'
    return _shell(cfg.get("brand_colors", {}), "AI Tools I Recommend",
                  "The tools I actually use, daily 👇", "\n".join(cards), footer)


def render_guide(cfg, tools):
    lm = cfg.get("lead_magnet", {})
    cats = {}
    for t in tools:
        cats.setdefault(t.get("category", "Other"), []).append(t)
    blocks = []
    for cat, items in cats.items():
        rows = "".join(
            f'<div class="row"><b>{html.escape(i.get("name",""))}</b>'
            f'<span>{html.escape(i.get("blurb",""))}</span></div>' for i in items)
        blocks.append(f'<div class="cat"><h3>{html.escape(cat)}</h3>{rows}</div>')
    extra = """
  .cat {{ text-align:left; margin:18px 0; }}
  .cat h3 {{ color:{accent}; font-size:.95rem; text-transform:uppercase; letter-spacing:.5px; margin-bottom:8px; }}
  .row {{ background:{card}; border-radius:12px; padding:13px 15px; margin:8px 0;
         border:1px solid rgba(255,255,255,.06); }}
  .row b {{ display:block; }}
  .row span {{ color:#a0a0a0; font-size:.85rem; }}
""".format(accent=cfg.get("brand_colors", {}).get("accent", "#e94560"),
           card=cfg.get("brand_colors", {}).get("secondary_bg", "#16213e"))
    body = "\n".join("  " + b for b in blocks)
    # Optional email-capture form (ESP embed pasted in config) above the list.
    embed = lm.get("signup_embed") or ""
    if embed.strip():
        body = (f'  <div class="signup">{embed}</div>\n'
                f'  <p class="tag">⬇️ The full list</p>\n{body}')
    footer = ('<a href="tools.html">🛠️ The exact tools I pay for &rarr;</a>'
              if cfg.get("affiliate", {}).get("tools") else '<a href="index.html">&larr; Back</a>')
    page = _shell(cfg.get("brand_colors", {}), lm.get("title", "AI Tools Guide"),
                  lm.get("tagline", ""), body, footer)
    return page.replace("</style>", extra + "</style>")  # inject guide-only CSS


def main():
    cfg = yaml.safe_load(open("config.yaml"))
    os.makedirs(OUT_DIR, exist_ok=True)
    has_tools = bool(cfg.get("affiliate", {}).get("tools"))
    guide_tools = load_lead_magnet()
    has_guide = bool(guide_tools)

    with open(os.path.join(OUT_DIR, "index.html"), "w") as f:
        f.write(render_bio(cfg, has_tools, has_guide))
    print(f"build_linkbio: wrote {OUT_DIR}/index.html")
    if has_tools:
        with open(os.path.join(OUT_DIR, "tools.html"), "w") as f:
            f.write(render_tools(cfg))
        print(f"build_linkbio: wrote {OUT_DIR}/tools.html")
    if has_guide:
        with open(os.path.join(OUT_DIR, "guide.html"), "w") as f:
            f.write(render_guide(cfg, guide_tools))
        print(f"build_linkbio: wrote {OUT_DIR}/guide.html ({len(guide_tools)} tools)")


if __name__ == "__main__":
    main()

"""Identify old AI-themed posts for removal (Phase F cleanup).

IMPORTANT: the Instagram *Login* API this project uses (graph.instagram.com +
IGAA token) CANNOT delete media — verified: a DELETE on a real, existing post
returns "Unsupported delete request ... does not support this operation".
Deleting via API needs the Facebook-login Instagram API (link a FB Page + Page
token), which this project deliberately avoids.

So this script does the tedious half: it scans the whole post history, scores
each caption for AI themes, and writes a checklist (newest first) with a direct
link to each flagged post. You open each link and delete it in the app (the
"..." menu -> Delete) — the only irreversible step, kept in your hands.

Run:  python -m scripts.cleanup_old_posts
      python -m scripts.cleanup_old_posts --before 2026-07-07   # only pre-pivot posts
"""
import argparse
import os
import re
import sys

import requests

GRAPH = "https://graph.instagram.com/v21.0"

# Word-boundary AI signals; weighted so obvious ones (ChatGPT) rank a post above
# a single incidental "ai". A post needs total weight >= THRESHOLD to be flagged.
AI_TERMS = {
    r"chatgpt": 3, r"\bgpt[- ]?\d?\b": 3, r"\bopenai\b": 3, r"\banthropic\b": 3,
    r"\bclaude\b": 3, r"\bgemini\b": 3, r"\bllm(s)?\b": 3, r"midjourney": 3,
    r"dall[- ]?e": 3, r"copilot": 2, r"\ba\.?i\.?\b": 2, r"artificial intelligence": 3,
    r"machine learning": 3, r"\bneural\b": 2, r"\bprompt(s|ing)?\b": 2,
    r"\bautomat(e|ion|ed)\b": 1, r"\bchatbot(s)?\b": 2, r"\bagent(s)?\b": 1,
}
THRESHOLD = 3


def score_caption(caption: str):
    """Return (total_weight, [matched_terms]) for a caption's AI-theme strength."""
    text = (caption or "").lower()
    hits, total = [], 0
    for pattern, w in AI_TERMS.items():
        if re.search(pattern, text):
            total += w
            hits.append(pattern.strip(r"\b").replace(r"\d?", "").replace("(s)?", ""))
    return total, hits


def fetch_all_media(ig_user_id, token):
    """Yield every media item (paginated) with caption/type/timestamp/permalink."""
    url = f"{GRAPH}/{ig_user_id}/media"
    params = {"fields": "id,caption,media_type,timestamp,permalink", "limit": 50,
              "access_token": token}
    while url:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        for m in data.get("data", []):
            yield m
        url = data.get("paging", {}).get("next")
        params = None  # `next` is a full URL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", help="Only flag posts before this date (YYYY-MM-DD)")
    ap.add_argument("--out", default="ai_posts_to_delete.md", help="Checklist output file")
    args = ap.parse_args()

    token = os.environ.get("META_ACCESS_TOKEN")
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
    if not token or not ig_user_id:
        sys.exit("META_ACCESS_TOKEN / INSTAGRAM_USER_ID not set")

    flagged, total_posts = [], 0
    for m in fetch_all_media(ig_user_id, token):
        total_posts += 1
        ts = m.get("timestamp", "")
        if args.before and ts[:10] >= args.before:
            continue
        weight, hits = score_caption(m.get("caption", ""))
        if weight >= THRESHOLD:
            flagged.append((weight, m, hits))

    flagged.sort(key=lambda x: (x[1].get("timestamp", ""), x[0]), reverse=True)

    lines = [f"# AI posts to delete ({len(flagged)} of {total_posts} posts)",
             "",
             "IG API can't delete these — open each link and delete in the app "
             "(**...** menu → Delete). Newest first.", ""]
    for weight, m, hits in flagged:
        cap = re.sub(r"\s+", " ", (m.get("caption") or "")).strip()[:90]
        lines.append(f"- [ ] {m.get('timestamp','')[:10]} · {m.get('media_type','')} · "
                     f"{m.get('permalink','')}\n      _{cap}_  (ai-score {weight})")
    report = "\n".join(lines) + "\n"

    with open(args.out, "w") as f:
        f.write(report)
    print(report)
    print(f"→ {len(flagged)} AI posts flagged out of {total_posts}. Checklist written to {args.out}.")
    print("Note: delete each manually — the Instagram Login API cannot delete posts.")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        # ponytail: classifier sanity — AI captions flag, human ones don't.
        assert score_caption("5 ChatGPT prompts to 10x your workflow")[0] >= THRESHOLD
        assert score_caption("GPT-5 vs Claude: which AI wins?")[0] >= THRESHOLD
        assert score_caption("3 habits that build unstoppable discipline")[0] < THRESHOLD
        assert score_caption("Why your brain procrastinates (psychology)")[0] < THRESHOLD
        print("cleanup classifier self-check OK")
    else:
        main()

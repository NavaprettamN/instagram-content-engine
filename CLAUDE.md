# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit dashboard (local dev)
streamlit run dashboard.py

# One-shot full pipeline (research → generate → publish ONE post)
python -m scripts.autopilot

# Manually run any individual agent
python -c "import yaml; from agents.research_agent import ResearchAgent; ResearchAgent(yaml.safe_load(open('config.yaml'))).run()"

# Refresh the IGAA token and print to stdout (used by refresh_token.yml)
python -m scripts.refresh_token
```

## Architecture

Fully automated Instagram content pipeline. No persistent server — all scheduling is GitHub Actions cron.

### Pipeline (fully hands-off)

```
research.yml (07:00 UTC daily)
  RSS + Reddit + TrendAgent (YouTube Data API + Google Trends + best-effort TikTok)
  → Gemini 2.5 Flash → 5 ideas (told to ride surging platform trends)
  → Top 3 auto-approved (by estimated_engagement), rest → pending_review
  → Supabase: content_ideas

generate.yml (every 2h)
  approved ideas without generated_content
  → ContentAgent (Gemini JSON) + DesignAgent (Pillow PNGs, 1080×1080)
  → reels: id%4==1 → Remotion motion-graphics reel (remotion/ + agents/motion_reel.py,
    music-only kinetic text; falls back to b-roll voice reel on any failure)
  → PublishingAgent.upload_image_to_hosting() → imgbb public URLs
  → Supabase: status=designed, image_paths=[imgbb URLs]

publish.yml (08:00 / 14:00 / 20:00 UTC)
  oldest designed post
  → PublishingAgent.publish_carousel() → Instagram API
  → Supabase: status=published, post_id

comment_reply.yml (every 2h, :30)
  poll recent media comments → Gemini drafts on-brand replies (SKIP spam/negative)
  → POST /{comment}/replies. Replied ids tracked in config.replied_comments.

analytics.yml (Sunday 20:00 UTC)
  Meta media insights → Gemini weekly analysis → Supabase: analytics_snapshots
  → ResearchAgent reads this on next run to close the feedback loop
  → AnalyticsAgent.best_posting_hours() → config.best_hours (publish.yml gate)

clip.yml (Sunday 16:00 UTC, weekly — heaviest job)
  YouTube CC search (videoLicense=creativeCommon) → yt-dlp download
  → faster-whisper transcript → Gemini picks a 20-40s segment
  → ffmpeg cut + 9:16 reframe + burned captions → publish_reel
  CC-BY attribution appended to caption. apt-installs ffmpeg for libass.
```

### Critical architectural decisions

**Instagram API:** Uses the **Instagram API with Instagram Login** (`graph.instagram.com/v21.0`), NOT the Facebook Graph API. Token prefix is `IGAA` (stored as `META_ACCESS_TOKEN` for historical naming). Never use `graph.facebook.com`, `me/accounts`, Page tokens, or `fb_exchange_token` — those fail with page-permission errors.

**Token refresh:** Single GET to `graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=...` — no app id/secret needed. `scripts/refresh_token.py` + `refresh_token.yml` handle this monthly. Requires a `GH_PAT` secret (repo `secrets: write`) because `GITHUB_TOKEN` can't update secrets.

**Auto-approve:** `ResearchAgent.save_ideas_to_db()` sorts the 5 Gemini ideas by `estimated_engagement` and saves the top 3 as `approved` directly. `generate.yml` picks these up without any human step. The dashboard Approval Center remains for manual override (reject before posting, or approve the remaining 2).

**PublishingAgent lazy init:** `META_ACCESS_TOKEN` and `INSTAGRAM_USER_ID` are read with `os.environ.get()` (not `os.environ[]`) so `generate.yml` can construct `PublishingAgent` just for `upload_image_to_hosting()` without carrying Meta creds. `_require_meta()` guards the actual publish methods.

**Image paths:** After `generate.yml`, `image_paths` in Supabase holds **imgbb URLs** (strings starting with `http`), not local file paths. `upload_image_to_hosting()` passes URLs through unchanged, so double-uploading is safe. Dashboard renders URLs and local paths (checks `startswith("http")` first).

**Hashtags:** `generate.yml` calls `HashtagAgent.generate_hashtag_sets()` and stores 3 volume-mixed sets in the `hashtags` column. At publish time, every site composes the caption via `hashtag_agent.compose_caption(post, count_ideas('published'))`, which appends one **rotated** set (rotation = published count) so Instagram never sees a repeated hashtag block. `pick_hashtags()` handles both the 3-set shape and the legacy flat list. Never append hashtags inline at a publish site — route through `compose_caption`.

### Database (Supabase Postgres)

Access only via `agents/_db.py` — never import `supabase` client directly.

- `content_ideas`: `pending_review → approved → designed → published`
- `analytics_snapshots`: weekly AI analysis; read by `ResearchAgent` to inform next idea generation
- `config`: reserved, unused

### Environment variables

```
GEMINI_API_KEY          # Google AI Studio
META_ACCESS_TOKEN       # IGAA-prefixed token (Instagram Login API)
INSTAGRAM_USER_ID       # IG Business Account ID (numeric)
IMGBB_API_KEY           # Image hosting (public URL required by Meta)
SUPABASE_URL            # Supabase project URL
SUPABASE_KEY            # Supabase service_role key (not anon)
YOUTUBE_API_KEY         # YouTube Data API (TrendAgent) — free, 10k units/day
JAMENDO_CLIENT_ID       # Jamendo API (MusicAgent reel music) — optional; unset = silent reels
GROQ_API_KEY            # Free LLM fallback when Gemini 429s (agents/_llm.py) — no card
PEXELS_API_KEY          # Free stock footage for b-roll reels (agents/broll_agent.py)
NTFY_TOPIC / DISCORD_WEBHOOK / SLACK_WEBHOOK  # Optional post notifications (agents/notify.py)
GH_PAT                  # GitHub PAT with secrets:write — only for refresh_token.yml
META_APP_ID / META_APP_SECRET  # Legacy; not used by current publish/refresh flow
```

### Tasks — MANDATORY end-of-work step

The overarching goal of this project is **to make money** from the Instagram account (grow reach/followers → monetize). Every change should serve that.

`tasks.md` is the roadmap; `PLAN.md` is the active content-quality/machine plan. **At the end of every piece of work, update `tasks.md`** (and `PLAN.md`'s status log when relevant): mark what's done, in progress, and pending. Not optional — keep them current so context survives across sessions.

Also add new env vars to the Environment variables list above when introduced (e.g. `GROQ_API_KEY`, `PEXELS_API_KEY`, notification webhooks).

### config.yaml

Non-secret runtime config: niche, brand voice, brand colors, RSS feeds, subreddits, fonts, output dir. Secrets are never put here. The dashboard Settings page writes back to this file.

### Manual reach levers (not automatable)

The engine handles content + cadence, but these move follower growth and must be done by hand: an optimized bio + link-in-bio, and replying to comments within the first hour of a post (early engagement drives reach). Posting slots in `config.yaml` are UTC; tune them to `audience_timezone`'s active hours, and use `AnalyticsAgent`'s weekly report once it has data.

### Fonts

`fonts/Inter-Bold.ttf` and `fonts/Inter-Regular.ttf` (bundled). `DesignAgent` falls back to `ImageFont.load_default(size=N)` (Pillow ≥10.1) if missing — renders DejaVuSans at the correct size, not a microscopic bitmap.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Web dashboard (Next.js) — see dashboard-web/README.md
cd dashboard-web && npm install && npm run dev   # http://localhost:3000

# Build + publish one meme reel (the whole content pipeline)
python -m scripts.post_meme

# Refresh the IGAA token and print to stdout (used by refresh_token.yml)
python -m scripts.refresh_token
```

## Architecture

Fully automated Instagram **meme account** (Reddit memes → reels). No persistent
server — all scheduling is GitHub Actions cron.

The old AI/value-content pipeline (research → generate → publish: Gemini ideas,
Pillow carousels, Remotion scene reels, YouTube CC clips, story reposts) was
**removed entirely on 2026-07-11** — the user wants the page to be Reddit memes
only. Don't reintroduce it. If you see references to it in old docs/commits,
they're historical.

### Pipeline (fully hands-off)

```
meme.yml (06:00 & 15:00 UTC daily)
  MemeAgent.fetch_memes() — Reddit meme subreddits (config.meme_subreddits),
    skips already-used memes (config.seen_memes in Supabase)
  → MemeAgent.build_reel() — one meme per 6s reel, ffmpeg, readable hold
  → MusicAgent.pick_track() — upbeat CC music bed (Jamendo), genre+track rotate
    via a persistent counter (config.meme_music_seed); credit appended to caption
  → upload_video() → Supabase storage public URL
  → PublishingAgent.publish_reel() → Instagram API (auto-publish)

comment_reply.yml (every 2h, :30)
  poll recent media comments → Gemini drafts on-brand replies (SKIP spam/negative)
  → POST /{comment}/replies. Replied ids tracked in config.replied_comments.

analytics.yml (Sunday 20:00 UTC)
  Meta media insights → Gemini weekly analysis → Supabase: analytics_snapshots

linkbio.yml (daily 06:00 UTC)
  scripts/build_linkbio.py → GitHub Pages link-in-bio (meme page: latest reel +
  follow; the AI-themed funnel pages were removed 2026-07-11)

refresh_token.yml (monthly)
  scripts/refresh_token.py → refreshes the IGAA token into repo secrets
```

### Critical architectural decisions

**Instagram API:** Uses the **Instagram API with Instagram Login** (`graph.instagram.com/v21.0`), NOT the Facebook Graph API. Token prefix is `IGAA` (stored as `META_ACCESS_TOKEN` for historical naming). Never use `graph.facebook.com`, `me/accounts`, Page tokens, or `fb_exchange_token` — those fail with page-permission errors.

**Token refresh:** Single GET to `graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=...` — no app id/secret needed. `scripts/refresh_token.py` + `refresh_token.yml` handle this monthly. Requires a `GH_PAT` secret (repo `secrets: write`) because `GITHUB_TOKEN` can't update secrets.

**Music:** Trending/licensed IG audio can't be attached via the API — only music pre-embedded in the video file works for auto-publish. MemeAgent bakes in a CC Jamendo track; that's the deliberate trade for zero manual work.

**Meme dedupe:** `scripts/post_meme.py` persists used meme ids in Supabase `config.seen_memes` **before** publishing, so a publish retry can't double-use memes.

### Database (Supabase Postgres)

Access only via `agents/_db.py` — never import `supabase` client directly.

- `content_ideas`: legacy table from the removed AI pipeline (old rows only; nothing writes to it now)
- `analytics_snapshots`: weekly AI analysis
- `config`: key/value store — `seen_memes`, `meme_music_seed`, `replied_comments`, `best_hours`

### Environment variables

```
GEMINI_API_KEY          # Google AI Studio (comment replies, analytics, music mood)
META_ACCESS_TOKEN       # IGAA-prefixed token (Instagram Login API)
INSTAGRAM_USER_ID       # IG Business Account ID (numeric)
SUPABASE_URL            # Supabase project URL
SUPABASE_KEY            # Supabase service_role key (not anon)
JAMENDO_CLIENT_ID       # Jamendo API (MusicAgent reel music) — optional; unset = silent reels
GROQ_API_KEY            # Free LLM fallback when Gemini 429s (agents/_llm.py) — no card
NTFY_TOPIC / DISCORD_WEBHOOK / SLACK_WEBHOOK  # Optional post notifications (agents/notify.py)
GH_PAT                  # GitHub PAT with secrets:write — only for refresh_token.yml
IMGBB_API_KEY           # Legacy image hosting (unused since carousel pipeline removed)
META_APP_ID / META_APP_SECRET  # Legacy; not used by current publish/refresh flow
```

### Tasks — MANDATORY end-of-work step

The overarching goal of this project is **to make money** from the Instagram account (grow reach/followers → monetize). Every change should serve that.

`tasks.md` is the roadmap; `PLAN.md` is the active content-quality/machine plan. **At the end of every piece of work, update `tasks.md`** (and `PLAN.md`'s status log when relevant): mark what's done, in progress, and pending. Not optional — keep them current so context survives across sessions.

Also add new env vars to the Environment variables list above when introduced.

### config.yaml

Non-secret runtime config: niche, brand voice, brand colors, fonts, output dir, meme subreddits/timing, link-in-bio. Secrets are never put here.

### Manual reach levers (not automatable)

The engine handles content + cadence, but these move follower growth and must be done by hand: an optimized bio + link-in-bio, and replying to comments within the first hour of a post (early engagement drives reach). Posting slots (meme.yml cron) are UTC; tune them to `audience_timezone`'s active hours, and use `AnalyticsAgent`'s weekly report once it has data.

### Fonts

`fonts/Inter-Bold.ttf` and `fonts/Inter-Regular.ttf` (bundled). `MemeAgent` falls back to `ImageFont.load_default(size=N)` (Pillow ≥10.1) if missing — renders DejaVuSans at the correct size, not a microscopic bitmap.

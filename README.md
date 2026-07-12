# Instagram Meme Engine

A fully automated Instagram meme account. GitHub Actions cron jobs fetch top
Reddit memes (videos and images), build 9:16 reels, and publish them via the
Instagram API — no server, no manual steps. A Next.js dashboard (Google-auth
gated, hosted on Vercel) shows analytics and triggers jobs on demand.

## How it works

- `meme.yml` (2×/day) — alternates **Reddit video memes** (RSS → v.redd.it HLS →
  ffmpeg 9:16 re-frame, original audio) and **image meme reels** (meme-api.com +
  CC music bed). Publishes as a reel, then reposts it to Stories.
- `comment_reply.yml` (2h) — Gemini replies to new comments on-brand.
- `analytics.yml` (weekly) — Meta insights → AI analysis + follower trend.
- `linkbio.yml` (daily) — rebuilds the GitHub Pages link-in-bio.
- `refresh_token.yml` (monthly) — refreshes the Instagram token.

Full architecture: `CLAUDE.md`. Operating guide: `FLOW.md`. Roadmap: `tasks.md`.

## Layout

- `agents/` — meme fetch/build, publishing, comments, analytics, music, DB
- `scripts/` — entrypoints the workflows run (`post_meme.py`, `build_linkbio.py`, …)
- `dashboard-web/` — Next.js control panel (see its README for Vercel setup)
- `config.yaml` — non-secret runtime config (subreddits, brand, bio links)
- `fonts/`, `generated_content/` — assets and build output

## Getting started

1. `pip install -r requirements.txt`
2. Populate `.env` (see the env-var list in `CLAUDE.md`).
3. `python -m scripts.post_meme` builds and publishes one meme reel.

## License

MIT License. Feel free to adapt for your own use.

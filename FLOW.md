# FLOW.md — Operating & Maintenance Guide

Plain-English guide to **what breaks, where to fix it, and what to update going forward.**
For architecture/code details see `CLAUDE.md`; for the roadmap see `tasks.md`.

> **2026-07-11:** the AI/value-content pipeline (research → generate → publish,
> clips, stories) was removed. The page is a **Reddit meme account**; `meme.yml`
> is the only content pipeline.

---

## 1. The 30-second mental model

A set of **GitHub Actions cron jobs** (no server) run the whole thing:

| Workflow | When | What it does | Can break if… |
|---|---|---|---|
| `meme.yml` | daily 06:00 & 15:00 UTC | Reddit memes → 6s reel + CC music → auto-publish to IG | meme-api.com down, Meta token, Jamendo |
| `comment_reply.yml` | every 2h | Gemini replies to new comments | Gemini quota, Meta token |
| `analytics.yml` | weekly Sun 20:00 | metrics → AI analysis, best-hours, follower trend | Gemini quota, Meta token |
| `linkbio.yml` | daily 06:00 UTC | rebuilds the GitHub Pages bio funnel | Meta token (latest-post link) |
| `refresh_token.yml` | monthly 1st 03:00 | refreshes the Meta token | needs `GH_PAT` |

**Where to watch for failures:** GitHub repo → **Actions** tab. Red = failed. Click it → the failed step shows the error.

---

## 2. The things that WILL need you, eventually

### 🟠 #1 — Meta / Instagram token (publishing, comments, analytics)
**Symptom:** meme publish / comment / analytics fail with an auth/permission error.
**Normal:** `refresh_token.yml` auto-refreshes it monthly (needs the `GH_PAT` secret set once).
**If it still dies (token fully expired, ~60 days unused):** generate a fresh **IGAA** token in the Meta dashboard and `gh secret set META_ACCESS_TOKEN <<< "IGAA..."` (also update `.env` locally).

### 🟠 #2 — Gemini free-tier quota
**Symptom:** any AI step logs `429 RESOURCE_EXHAUSTED`. The agents retry, then fall back to Groq (`agents/_llm.py`), then skip.
**Fix:** wait for the daily reset, **or** enable billing on the Gemini key for a higher limit.

### 🟡 #3 — Meme source dries up
**Symptom:** `meme.yml` logs "No fresh memes found" repeatedly.
**Why:** meme-api.com outage, or `meme_min_score` too high / subreddits too narrow for the dedupe list.
**Fix:** add subreddits or lower `meme_min_score` in `config.yaml`.

---

## 3. Where each setting lives (and what to change for what)

| You want to change… | Edit here |
|---|---|
| Niche, brand voice, colors | `config.yaml` |
| **Meme subreddits / score floor / pacing** | `config.yaml` → `meme_subreddits`, `meme_min_score`, `memes_per_reel`, `meme_seconds_each` |
| **Posting times** | `.github/workflows/meme.yml` → the `cron:` line (UTC) |
| Music vibe | `scripts/post_meme.py` → `genres` list; fallback tags in `config.yaml` `reel_music_tags` |
| Comment-reply tone | `agents/comment_agent.py` (prompt) + `config.yaml` `brand_voice` |
| Bio links | `config.yaml` → `link_in_bio` (AI-themed funnel removed 2026-07-11; add `lead_magnet`/`affiliate` config back to re-enable guide/tools pages) |

**Secrets (GitHub → Settings → Secrets → Actions):** `GEMINI_API_KEY`, `GROQ_API_KEY`, `META_ACCESS_TOKEN`, `INSTAGRAM_USER_ID`, `SUPABASE_URL`, `SUPABASE_KEY`, `JAMENDO_CLIENT_ID`, `GH_PAT`.
The same values live in `.env` for local runs (`.env` is gitignored — never commit it).

---

## 4. Common "how do I…"

- **Post a meme reel right now:** Actions → "Meme Reel" → Run workflow (or `python -m scripts.post_meme` locally).
- **See analytics:** the web dashboard (`dashboard-web/`) → Analytics page.
- **Rebuild the bio page after editing config:** Actions → Link-in-bio → Run workflow (or wait for 06:00 UTC).

---

## 5. The honest levers
The machine is built; **revenue scales with audience, not more code.** The highest-value upkeep is: let the meme engine run to accumulate followers + post data, tune subreddits/timing from the weekly analytics report, and refresh the Meta token if the monthly auto-refresh ever fails.

# FLOW.md — Operating & Maintenance Guide

Plain-English guide to **what breaks, where to fix it, and what to update going forward.**
For architecture/code details see `CLAUDE.md`; for the roadmap see `tasks.md`.

---

## 1. The 30-second mental model

A set of **GitHub Actions cron jobs** (no server) run the whole thing:

| Workflow | When | What it does | Can break if… |
|---|---|---|---|
| `research.yml` | daily 07:00 UTC | trends + RSS → Gemini → 5 ideas, top 3 auto-approved | Gemini quota, YouTube API key |
| `generate.yml` | every 2h | approved ideas → carousels/reels (2:1) + music + hashtags | Gemini quota, ffmpeg, Jamendo |
| `publish.yml` | every 2h (gated) | posts to IG at best/fallback hours, ≤3/day | Meta token |
| `comment_reply.yml` | every 2h | Gemini replies to new comments | Gemini quota, Meta token |
| `story.yml` | daily 09:00 UTC | reposts latest to Stories | Meta token |
| `clip.yml` | **manual only** | CC YouTube → captioned reel | **YouTube cookies (expire!)**, Meta token |
| `analytics.yml` | weekly Sun 20:00 | metrics → AI analysis, best-hours, follower trend | Gemini quota, Meta token |
| `linkbio.yml` | daily 06:00 UTC | rebuilds bio + tools + guide pages → GitHub Pages | — |
| `refresh_token.yml` | monthly 1st 03:00 | refreshes the Meta token | needs `GH_PAT` |

**Where to watch for failures:** GitHub repo → **Actions** tab. Red = failed. Click it → the failed step shows the error.

---

## 2. The things that WILL need you, eventually

### 🔴 #1 — YouTube cookies expire (the clipper, `clip.yml`)
**Symptom:** `clip.yml` fails with *"cookies are no longer valid / Sign in to confirm you're not a bot."*
**Why:** YouTube rotates session cookies every few weeks (and whenever you log in/out).
**Fix — re-export and update the secret:**
1. In a browser **logged into YouTube**, use the **"Get cookies.txt LOCALLY"** extension → export `youtube.com` cookies.
2. Confirm the file has `LOGIN_INFO` and `__Secure-1PSID` lines (not just visitor cookies).
3. Update the secret: `gh secret set YOUTUBE_COOKIES < cookies.txt` (or repo → Settings → Secrets → Actions → `YOUTUBE_COOKIES` → update).
4. Re-run: Actions → "Clip Agent" → Run workflow (leave **dry_run = true** to preview without posting).

> The clipper is **manual-only** on purpose — a stale cookie would fail a scheduled run silently. Run it when you want a clip.

### 🟠 #2 — Meta / Instagram token (publishing, comments, stories, analytics)
**Symptom:** publish/comment/story/analytics fail with an auth/permission error.
**Normal:** `refresh_token.yml` auto-refreshes it monthly (needs the `GH_PAT` secret set once).
**If it still dies (token fully expired, ~60 days unused):** generate a fresh **IGAA** token in the Meta dashboard and `gh secret set META_ACCESS_TOKEN <<< "IGAA..."` (also update `.env` locally).

### 🟠 #3 — Gemini free-tier quota
**Symptom:** any AI step logs `429 RESOURCE_EXHAUSTED`. The agents retry then skip that item (won't crash the batch).
**Fix:** wait for the daily reset, **or** enable billing on the Gemini key for a higher limit. As posting volume grows you'll likely need this.

---

## 3. Where each setting lives (and what to change for what)

| You want to change… | Edit here |
|---|---|
| Niche, brand voice, colors, RSS feeds, subreddits | `config.yaml` |
| Posting times / audience timezone | `config.yaml` (`posting_times`, `audience_timezone`) — note: `publish.yml` cron is every 2h and *gates* to these hours |
| **Reel : carousel mix** | `generate.yml` → `as_reel = (idea['id'] % 3) != 0` (now 2 reels : 1 carousel) |
| Reel pacing | `config.yaml` → `reel_seconds_per_slide` |
| **Caption style / hooks / CTAs** | `agents/content_agent.py` (prompt) |
| **Clip subtitle style** (font, size, position, color) | `agents/clip_agent.py` → `ASS_HEADER` (Alignment 5 = middle; Fontsize; Outline) |
| Clip language | `agents/clip_agent.py` → `transcribe()` uses `task="translate"` (always English) |
| Bio links / funnel | `config.yaml` → `link_in_bio` |
| Lead-magnet guide contents | `data/lead_magnet.json` |
| Email capture form | `config.yaml` → `lead_magnet.signup_embed` (Kit embed) |
| Affiliate tools / Sovrn key | `config.yaml` → `affiliate` |
| Product (Gumroad) link | `config.yaml` → the `🛒` link in `link_in_bio.links` |
| The sellable product itself | `scripts/build_product.py` → re-run `python -m scripts.build_product` |

**Secrets (GitHub → Settings → Secrets → Actions):** `GEMINI_API_KEY`, `META_ACCESS_TOKEN`, `INSTAGRAM_USER_ID`, `IMGBB_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `YOUTUBE_API_KEY`, `YOUTUBE_COOKIES`, `JAMENDO_CLIENT_ID`, `GH_PAT`.
The same values live in `.env` for local runs (`.env` is gitignored — never commit it).

---

## 4. Common "how do I…"

- **Preview a clip without posting:** Actions → Clip Agent → Run workflow → `dry_run = true`. The log prints a Supabase URL — open it to check captions/framing. Set `dry_run = false` to actually post.
- **Force one full post now:** Actions → Generate, then Publish (or `python -m scripts.autopilot` locally for a carousel).
- **See analytics:** the Streamlit dashboard → Analytics tab (per-post reach/saves/shares, best/worst, follower trend).
- **Rebuild the bio/funnel pages after editing config:** Actions → Link-in-bio → Run workflow (or wait for 06:00 UTC).
- **Change what tools are recommended:** edit `config.yaml` `affiliate.tools` (real homepage URLs — Sovrn auto-affiliates the covered ones).

---

## 5. The honest levers
The machine is built; **revenue scales with audience, not more code.** The highest-value upkeep is: keep the cookies fresh (for clips, your best-performing format), let the engine run to accumulate followers + post data, and refresh the Meta token if the monthly auto-refresh ever fails.

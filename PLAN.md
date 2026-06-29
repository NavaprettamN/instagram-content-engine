# PLAN.md

> **Active plan = "Content Quality + Proper Machine" below.** The original
> build plan is archived at the bottom (historical context).

---

# ▶ ACTIVE: Content Quality + "Proper Machine" Roadmap (2026-06-30)

Goal unchanged: **make money** by growing real reach + followers. This section is
the source of truth for *content quality + cadence*. Companions: `CLAUDE.md`
(architecture), `FLOW.md` (maintenance), `tasks.md` (monetization).

## The problem (stated by user)

1. **Reels look bad.** Two formats, both weak:
   - *Voice reels*: voiceover + captions over a **flat solid-colour background** — nothing moves.
   - *Vimeo CC clips*: real footage but thin niche pool → dry screen-recordings.
2. **Carousels are static.** `DesignAgent` renders text on the **same solid background every time** — same colour, same layout.
3. **No enforced daily shape.**

## Target daily output (the contract)

**Every day: 1 carousel + 2 reels.** Reels = priority reach surface; carousel = the saveable value post.

| Slot (UTC, approx) | Type | Notes |
|---|---|---|
| Morning | Reel | b-roll voice reel (primary) |
| Afternoon | Carousel | redesigned, varied template |
| Evening | Reel | b-roll voice reel OR Vimeo clip (variety) |

Cron is delayed 60–90 min → slots are targets. New rule: **per-day type quota** — post exactly 2 reels + 1 carousel/day, don't just drain oldest.

## Phase A — Reels that actually move (HIGHEST IMPACT)

Keep the original-voiceover format (reliable, $0, no cookies) but put **real moving stock footage behind the captions** — the format every big faceless AI account uses. Voiceover + b-roll + synced captions + ducked music = scroll-stopping, automated, free.

- New `agents/broll_agent.py` — `fetch_clips(terms, n, seconds) -> [paths]` via **Pexels Video API** (free key), Pixabay fallback. Cache by term.
- Script → Gemini returns **2–4 visual search terms**; ~1 clip per 7–10s of voice.
- `voice_reel.py` upgrade: replace `color=` bg with a **concat of b-roll clips**, each cropped to 1080×1920, trimmed to its share of voice duration, dark overlay (caption legibility) + optional Ken-Burns. Captions + title banner on top. Music ducked.
- Fallback: b-roll fetch fails → solid-colour bg (today's behaviour). Never hard-fail.
- Hook rewrite: first line = 2-second pattern interrupt. ~30s, energetic TTS.

**Needs:** `PEXELS_API_KEY` (free, instant at pexels.com/api) → `.env` + GH secret.

## Phase B — Carousels with visual variety

`agents/design_agent.py`:
- **Palette rotation** — 5–6 curated brand-safe schemes, pick by `idea_id % N`.
- **Background variety** — rotate: gradient / gradient + geometric shapes / Pexels **photo** bg + dark overlay (reuse broll image search). No more flat colour.
- **Layout templates** — 3–4 hook-slide layouts (centred, left-accent-bar, big-number, quote-card), rotate per post.
- **Typography** — stronger hierarchy, accent shapes. Keep Inter + footer.

## Phase C — The machine (end-to-end glue)

- **Daily type quota** — `generate.yml` keeps queue ≥2 reels + ≥1 carousel; `publish.yml` posts by type quota not just oldest.
- **Quality gate** — Gemini scores script/caption (+ thumbnail) 1–10 on hook + clarity; reject & regen below threshold.
- **Theme rotation** — research tags each idea; avoid repeating angle within N days.
- **Asset cache** — cache b-roll/photos/music by key.
- **Vimeo clips = variety, not staple** — 1–2×/week, existing LLM vet.
- **Observability** — each run logs output; failures surface, FLOW.md = fix map.

## Phase D — Bigger ideas (after A–C)

- Talking-head/avatar reels (defer — complexity/cost).
- Trending-audio reels (IG API can't attach IG sounds — out of scope).
- YouTube-from-residential-IP (premium fallback, needs user's Mac/self-hosted runner).
- Quote cards / memes (high shareability).

## Build order

1. **Phase A** — b-roll voice reels (headline fix). Needs `PEXELS_API_KEY`.
2. **Phase B** — carousel variety.
3. **Phase C** — quota + quality gate + cache.
4. **Phase D** — evaluate after a week of analytics.

## Open dependency

- **`PEXELS_API_KEY`** (free, instant) blocks Phase A footage + Phase B photo bgs. Pixabay key is a drop-in fallback.

## Verification per phase

- **A:** render one b-roll reel locally → play → confirm moving footage + middle captions + voice + music; publish one to IG.
- **B:** render 3 carousels → confirm different palette/layout/bg.
- **C:** dry-run a day → queue holds 2 reels + 1 carousel; quality gate rejects a weak script.

## Status log

- 2026-06-30: Plan written. Vimeo clip pipeline verified end-to-end (IG `18323571790287982`); `publish_reel` now retries with cache-buster on Meta 2207077. Awaiting `PEXELS_API_KEY` to start Phase A.

---

# 🗄 ARCHIVED: Original build plan ($0/month free stack)

## Context

You want a self-running Instagram Content Engine that:
- Auto-generates carousel posts (captions + branded image slides) using AI
- Posts directly to a **Business** Instagram account via the official Meta Graph API
- Runs on a schedule with a human-in-the-loop approval step in a small web dashboard
- Must be **$0/month** — every API, host, and dependency must have a sustainable free tier

The repo already contains a Python multi-agent skeleton (`agents/research_agent.py`, `content_agent.py`, `design_agent.py`, `publishing_agent.py`, `analytics_agent.py`, `hashtag_agent.py`), a `dashboard.py` Streamlit UI, a SQLite schema, and a working Meta Graph API publish flow. It was built against **Azure OpenAI** (paid) and **Imgur** (image host) with an always-on `schedule`-library loop in `orchestrator.py`. The plan below rebuilds the AI + scheduling + deployment layers with free providers, reusing the existing agent structure, DB schema, and dashboard.

**Confirmed decisions:**
- Visual style: easy to host free + authentic → **PIL text-on-color carousels** (deterministic, no AI image API needed, zero compute cost, perfect for educational content)
- Workflow: **Human-in-the-loop** (Streamlit dashboard approval gate)
- Niche: **AI Productivity Tools** (kept from current `config.yaml` — has excellent free content sources and fits the text-slide format)
- Format: **Carousels** first

---

## Feasibility verdict: Yes, fully feasible at $0/month

| Concern | Verdict | Notes |
|---|---|---|
| Posting to IG via API | Yes | Requires **Business/Creator** account (not personal). Free. |
| Free caption / idea LLM | Yes | Gemini 2.5 Flash free tier (~15 RPM, ~1500 req/day) |
| Image generation | Yes | Pillow (already in repo design_agent) — fully local, zero cost |
| Image hosting (Meta needs public URL) | Yes | imgbb (unlimited free, no card) |
| Scheduling | Yes | GitHub Actions cron — 2000 min/mo free, no server needed |
| Dashboard hosting | Yes | Streamlit Community Cloud (free, deploys from GitHub) |
| Persistent DB | Yes | Supabase Postgres free tier (500 MB) |

**Hosting callout:** Vercel is excellent for JS/Next.js, but this app is Python + Streamlit. The Python-native free hosts that actually fit are **Streamlit Community Cloud** (purpose-built, one-click deploy from GitHub) or **Hugging Face Spaces** (Streamlit-supported). The scheduled jobs don't need *any* host — they run on **GitHub Actions cron**, which means there's no always-on server to keep alive.

---

## Credentials to obtain

All free. I'll walk you through each during implementation.

| # | Credential | Where | Why |
|---|---|---|---|
| 1 | IG account → **Business or Creator** | Instagram app → Settings → Account type | API only works for non-personal |
| 2 | **Facebook Page** linked to the IG account | facebook.com | Meta requires it as the bridge |
| 3 | **Meta for Developers app** with "Instagram Graph API" product | developers.facebook.com | Issues the access token |
| 4 | **Long-lived Page Access Token** (scopes: `instagram_business_basic`, `instagram_business_content_publish`, `pages_show_list`, `pages_read_engagement`) | Graph API Explorer + token-exchange call | 60-day expiry; we'll add a refresh helper |
| 5 | **IG Business Account ID** (`ig_user_id`) | One-time Graph API query | Goes in `config.yaml` |
| 6 | **Google AI Studio API key** | aistudio.google.com | Gemini LLM |
| 7 | **imgbb API key** | api.imgbb.com | Image hosting for Meta URL fetch |
| 8 | **Supabase project** + service-role key | supabase.com | Persistent DB for serverless runs |
| 9 | **GitHub repo** + Actions secrets | github.com | Hosts code + scheduler |

---

## Recommended free stack

| Layer | Service | Replaces |
|---|---|---|
| LLM | **Google Gemini 2.5 Flash** via `google-genai` SDK | Azure OpenAI calls in all 6 agents |
| Image generation | **Pillow** (existing `design_agent.py`) | — already free, keep as-is |
| Image hosting | **imgbb** | Hardcoded Imgur in `publishing_agent.py:21` |
| Scheduler | **GitHub Actions cron** | `orchestrator.py` `schedule` loop |
| Database | **Supabase Postgres** (or SQLite locally) | `data/content_engine.db` |
| Approval UI | **Streamlit Community Cloud** | Local-only `dashboard.py` |
| Publishing | **Meta Graph API v19.0** | Already in repo, unchanged |

---

## Architecture: reuse vs. replace

### Reuse as-is
- `agents/publishing_agent.py` — Meta Graph API publish flow for carousels (lines 56–97) is correct and stays
- `agents/research_agent.py` — RSS + Reddit trend gathering
- `agents/design_agent.py` — Pillow-based 1080×1080 carousel slide generator (matches "authentic, easy to host" requirement)
- `agents/hashtag_agent.py` — hashtag set strategy
- `dashboard.py` — Streamlit UI; approval workflow is already designed for this
- `content_ideas` schema — lifecycle `pending_review → approved → designed → published` stays

### Swap providers (small, contained edits)
- All LLM calls in `agents/research_agent.py`, `content_agent.py`, `analytics_agent.py`, `hashtag_agent.py` → Gemini via shared helper (`agents/_llm.py`)
- `agents/publishing_agent.py:12–29` `upload_image_to_hosting()` → imgbb call; read key from config, not hardcoded `YOUR_IMGUR_CLIENT_ID`
- `config.yaml` → drop `azure_*` keys, add `gemini_api_key`, `imgbb_api_key`, `supabase_url`, `supabase_key`

### Replace
- `orchestrator.py` `schedule` loop → **GitHub Actions workflows** (four cron files in `.github/workflows/`):
  - `research.yml` — daily at 07:00 UTC: `python -m agents.research_agent`
  - `generate.yml` — every 2h: generates carousel content + designs slides for approved ideas
  - `publish.yml` — twice daily (10:00, 18:00 UTC): publishes any `status=designed` row
  - `analytics.yml` — weekly Sunday 20:00 UTC
- SQLite (`data/content_engine.db`) → **Supabase Postgres** (Actions are stateless, can't share local DB across runs). Same schema; swap `sqlite3` calls for `psycopg`/`supabase-py`.

### Fix
- `requirements.txt` currently has only 6 packages but the code imports `feedparser`, `PIL`, `yaml`, `schedule` — missing. Add them, add `google-genai` and `supabase`, drop unused `sqlalchemy`.
- `publishing_agent.py:22` hardcodes `"Client-ID YOUR_IMGUR_CLIENT_ID"` — never reads from config. Will fix when swapping to imgbb.

---

## Critical files to modify

| File | Change |
|---|---|
| `config.yaml` | Drop Azure block, add Gemini + imgbb + Supabase keys |
| `requirements.txt` | Add `google-genai`, `feedparser`, `Pillow`, `pyyaml`, `supabase`; remove `sqlalchemy` |
| `agents/_llm.py` *(new)* | Shared Gemini client + helper (`generate_text(prompt, json_schema=None)`) |
| `agents/research_agent.py` | Replace OpenAI client with `_llm.generate_text(...)` |
| `agents/content_agent.py` | Same |
| `agents/hashtag_agent.py` | Same |
| `agents/analytics_agent.py` | Same |
| `agents/publishing_agent.py` | Replace `upload_image_to_hosting()` with imgbb POST; read key from config |
| `agents/_db.py` *(new)* | Tiny wrapper: `get_ideas(status)`, `update_idea(id, **fields)` against Supabase |
| `dashboard.py` | Swap `sqlite3` calls for `_db.py` helper; deploy as-is to Streamlit Cloud |
| `orchestrator.py` | Delete (or keep as local dev helper) |
| `.github/workflows/research.yml` *(new)* | Cron + checkout + `python -m agents.research_agent` |
| `.github/workflows/generate.yml` *(new)* | Cron + generate + design for `status=approved` |
| `.github/workflows/publish.yml` *(new)* | Cron + publish for `status=designed` |
| `.github/workflows/analytics.yml` *(new)* | Weekly cron |
| `fonts/Inter-Bold.ttf`, `Inter-Regular.ttf` | Drop in (or fall back to Pillow defaults) |

---

## Implementation phases

1. **Credentials sprint** *(you + me, ~30 min)* — convert IG → Business, link FB Page, create Meta app, fetch long-lived token + IG account ID, get Gemini + imgbb + Supabase keys. Stash in `.env` for local + GitHub repo Secrets for Actions.

2. **Provider swap** — write `agents/_llm.py`, replace LLM calls in 4 agents; replace Imgur upload in `publishing_agent.py` with imgbb; update `config.yaml` + `requirements.txt`.

3. **DB migration** — create Supabase project, run schema SQL (matches existing SQLite schema), write `agents/_db.py`, point `dashboard.py` at it.

4. **Scheduler** — write the 4 GitHub Actions workflows; each is ~25 lines (checkout, setup-python, install, run module, store creds from secrets).

5. **Dashboard deploy** — push to GitHub, connect repo to Streamlit Community Cloud, set env vars (Supabase URL/key only — no need for Meta token in the UI).

6. **End-to-end smoke test** — manually trigger `publish.yml` via `workflow_dispatch` with a hand-crafted approved idea; confirm post appears on IG; confirm Supabase row flips to `status=published`; confirm dashboard shows it.

---

## Verification

- `python -c "from agents.publishing_agent import PublishingAgent; import yaml; PublishingAgent(yaml.safe_load(open('config.yaml'))).publish_carousel(['test1.png','test2.png'], 'smoke test')"` — locally confirms token + IG ID + imgbb hosting + Meta publish all work end-to-end.
- Trigger `.github/workflows/publish.yml` via `workflow_dispatch` from the Actions tab.
- Visual confirmation: the post appears on the IG Business account feed.
- DB confirmation in Supabase: `select status, post_id, published_at from content_ideas order by id desc limit 1;` — `status=published`, `post_id` populated, `published_at` set.
- Dashboard renders the new post under Analytics with no errors.

---

## What you need to do next

1. Confirm you have / can convert to a Business Instagram account
2. Tell me which Facebook Page you'll link (or if you need to create one)

Once those two are sorted, I'll implement in the order above. We can stop at any phase — e.g., we could just do phases 1–2 first to get the AI generation working locally before wiring up the scheduler and Supabase.

# Monetization Roadmap — Instagram Content Engine

Synced from Notion "Let's Ship" → Tasks database (linked to Instagram Content Agent project).

---

## 📊 Current Status (updated 2026-07-11)

> **Goal: make money** — grow reach/followers → monetize. Update this file at
> the end of every work session (mandated in CLAUDE.md).

### 🎯 Phase H (2026-07-11): memes-only pivot — AI-content pipeline REMOVED
User decision: the page is a **Reddit meme account only**. Despite the F3
pillar rebalance, AI carousels/reels kept posting; removed the whole
AI/value-content machine instead of tuning it:
- Deleted workflows: `research.yml`, `generate.yml`, `publish.yml`, `clip.yml`,
  `story.yml`, `autopilot.yml`.
- Deleted agents: research, trend, content, design, hashtag, broll, clip,
  scene/voice/motion reel, video, `_captions` + `remotion/` renderer +
  `orchestrator.py` + scripts `autopilot.py`, `clip_publish.py`, `post_story.py`.
- Kept: `meme.yml` (build + auto-publish meme reels 2×/day), `comment_reply.yml`,
  `analytics.yml`, `linkbio.yml`, `refresh_token.yml`.
- `config.yaml` trimmed to meme/brand keys; niche + brand voice now
  meme-account; `requirements.txt` cut to what's still imported.
- **Follow-up cleanup (same day, user-approved):** deleted the 82 orphaned
  `content_ideas` rows in Supabase (pending_review/approved/designed; 46
  published kept as history); removed the dashboard Content Queue page and
  idea KPIs (Overview now followers/Δ/top posts), Controls now triggers
  meme/comment/analytics/linkbio only; link-in-bio re-themed to the meme page
  (latest reel + follow) — AI cheat-sheet lead magnet, Sovrn affiliate tools
  page, and Gumroad product link removed (`data/lead_magnet.json`,
  `scripts/build_product.py` deleted). Old funnel tasks #8–10 are retired.

### ✅ Done & running (current machine)
- **Meme reels** — alternate per run: Reddit VIDEO memes (RSS → v.redd.it HLS →
  9:16 re-frame, original audio; falls back to images) and image meme reels
  (meme-api.com, 6s hold, CC music rotation). Dedupe via `config.seen_memes`,
  auto-publish 06:00 & 15:00 UTC, then the same reel reposted to Stories.
- **Comment auto-reply**, **weekly analytics**, **link-in-bio** (meme-themed:
  latest reel + "Promote your brand" DM link + follow), **token auto-refresh**.
- **Dashboard LIVE on Vercel** (2026-07-12) — https://meme-engine-dashboard.vercel.app
  "Meme Engine": new UI, meme format picker (Auto/Video/Images), recent-posts
  grid with live engagement, Google auth locked to the owner. Git auto-deploys
  from main (root dir dashboard-web); OAuth client + all env vars configured.
  [~] Sign-in fix deployed but NOT yet user-confirmed: first attempt hit
  redirect_uri_mismatch (two OAuth clients existed; Vercel had old ID + new
  secret). Fixed: AUTH_GOOGLE_ID now the "Web client 1" client (…bceqan, in
  Google project "finance-app") — verified the live OAuth redirect carries it.
  Next session: ask user if login works; if not, check Google propagation /
  client Save state. Old unused client …qlbe0h can be deleted in Google console.
- **Dashboard analytics enriched** (2026-07-12) — Overview now pulls Instagram
  account-level insights (last 30d: accounts reached, account interactions,
  accounts engaged, profile views, likes, comments, saves, shares, link-in-bio
  taps) via `/{ig-user}/insights?metric_type=total_value`, plus per-post
  insights (reach/saves/shares/views) merged into `getRecentMedia`. New
  "Account insights" KPI grid + "Per-post breakdown" table on the Overview
  page; post cards now show reach. Each metric fetched separately so one
  unsupported metric can't blank the panel (degrades to null/"–"). lib/data.ts
  + app/(app)/overview/page.tsx. Build + typecheck pass.
- **Dashboard UI redesign — Notion style** (2026-07-12) — replaced the dark
  neon-gradient theme with a clean light Notion-style system (warm neutrals,
  hairline borders, single blue accent #2383e2, flat cards). Dropped ALL emoji
  in favour of a dependency-free inline SVG line-icon set (components/Icon.tsx):
  brand monogram "M", nav, KPI corner icons, post-card stats, job cards, run
  status. Recolored FollowerChart for the white surface; refined tables
  (right-aligned nums, row hover), tags, buttons, posts grid. Build + typecheck
  pass; login verified rendering locally in the new theme. Pushed to main
  (auto-deploys to Vercel). Note: overview can't be rendered locally (needs the
  Supabase/AUTH env that only lives in Vercel) — verify visually on the live URL.
- **Dashboard dark mode** (2026-07-12) — full dark variant via a
  :root[data-theme="dark"] token block over the light palette. No-flash inline
  script in app/layout.tsx resolves theme before paint (localStorage choice,
  else OS prefers-color-scheme); sidebar ThemeToggle.tsx flips data-theme +
  persists. FollowerChart made theme-aware (chart tokens via style, since SVG
  attrs don't resolve var()). Fixed brand mark, chart tooltip, post-type badge,
  tag colors for dark. Build + typecheck pass; dark CSS + init script verified
  served locally. Pushed to main.
- **Strategy session + smarter meme selection** (2026-07-13) — researched
  content/video/reach/monetization (web). Decisions locked in PLAN.md Phase I:
  memes-only PER ACCOUNT, free-until-revenue, slight monetizable niche tilt,
  fully-automated audio, and the BIG future direction = MULTIPLE single-niche
  meme accounts on one engine (plan later, PLAN.md I4). SHIPPED I1: MemeAgent
  .fetch_memes now over-fetches 50/sub, ranks by real Reddit upvotes, floors at
  meme_min_score, downloads top N (fallback to best). Verified live (48→top4 by
  ups). NOT doing: Veo/paid image gen (not free), narrated-story format (would
  break memes-only).
- **I2 shareability (SHIPPED 2026-07-13, free)** — MemeAgent._share_copy: one
  cached Gemini 2.5 Flash call (free VISION — sends the lead meme's actual image,
  not the junk Reddit title) returns {hook, caption}. Hook drawn on frame 0
  (_draw_hook, bold+outlined); caption ends in a "send this to the friend who…"
  CTA → targets DM sends (#1 2026 signal). Added image_path to _llm.generate_text
  (Groq fallback is text-only). Tone guardrail for sensitive memes. Static
  fallback if LLM down. Verified live (MLK meme → coherent respectful copy; video
  title-only path; full reel self-check OK). Open Q for user: move to 1 meme/reel
  so hook+caption+frame are fully coherent (currently 4 unrelated memes/reel).

### 💰 Monetization plan (meme account, 2026-07-11 ideation)
Meme pages make money from **attention arbitrage** — the product is reach.
Realistic ladder, in order of when each unlocks:
1. **Shoutouts / promo slots (primary; ~5–10k followers)** — brands, apps, and
   smaller pages pay for a story or reel promo. Setup DONE: "📢 Promote your
   brand here" DM link live in the bio. Next: #11 media kit auto-generated from
   analytics (reach, saves, audience geo) + a simple rate card when DMs start.
2. **Affiliate that fits meme traffic (~10k)** — broad-appeal offers only
   (mobile games/apps with CPI programs, food/shopping deals). The linkbio
   builder still supports an affiliate page — re-add config when there's reach.
3. **IG creator monetization (gated)** — reels bonuses are invite-only and
   mostly unavailable in India; treat as a bonus, not a plan.
4. **Digital product (~20k+)** — meme pages sell templates/pack or shoutout
   bundles poorly; better: sell **placement**, keep products for later.
5. **Page flipping / network (later)** — grown meme pages resell; multi-account
   (#13) multiplies this.
Everything is audience-gated → the real job now is cadence + format quality;
revenue tasks unblock at follower milestones, not code milestones.

### 🔄 In progress / needs attention
- **Watch meme performance** — video vs image reels is now the A/B to watch in
  weekly analytics; tune subreddits, cadence (maybe 3×/day), posting hours.
- **Notification channel** — wire the chosen secret (ntfy topic / Discord / Slack webhook).

### ⬜ Pending
- #11 Media kit (first monetization code task — build when promo DMs start or ~5k followers).
- #12 Sponsored slot scheduler (after #11).
- #13–15 Scale (multi-account, cross-platform, SaaS).

---

## Historical status (pre-pivot, for context)

### ✅ Done & running
- **Full content engine** — research (trends) → auto-approve → quality-gate → generate → publish, all on GitHub Actions cron.
- **B-roll voice reels (primary format)** — hook → script → free edge-tts voiceover → **real moving Pexels stock footage** behind **kinetic word-pop captions** + animated **title underline** + **progress bar** + ducked music. Big jump over the old flat-bg reels. (`broll_agent.py`, `voice_reel.py`, `_captions.py`.)
- **Carousel variety** — 6 rotating palettes, gradient backgrounds, accent blobs, layout rotation (no more identical flat slides).
- **Free LLM fallback** — Gemini primary; on a 429 falls straight to **Groq** (free, no card, ~14.4k req/day). Beats the daily-quota wall without billing. (`agents/_llm.py`.)
- **Daily content mix** — publish enforces **2 reels + 1 carousel / UTC day** (`daily_mix`), reels first, with empty-queue fallback + ~6h spacing.
- **LLM quality gate** — each reel/carousel scored 1-10; best of 2 attempts kept; dry content regenerated.
- **Reliable reel publishing** — re-hosts under a fresh name on Meta 2207077 fetch flake; failed publishes stay `designed` to retry (no lost posts / quota miscount).
- **Post notifications** — `agents/notify.py` pings ntfy / Discord / Slack when a post goes live (set one webhook secret).
- **Monetization funnel live** — bio → free cheat-sheet (Kit email) → Sovrn affiliate → Gumroad product (GitHub Pages).
- Comment auto-reply, Stories auto-promo, rich analytics dashboard, performance feedback loop, hashtag rotation, **FLOW.md** maintenance guide.

### 🔄 In progress / needs attention
- **Phase E planned (2026-07-05)** — user feedback after a week live: carousels too samey, all-AI topics cap reach, reels reuse the same stock clips. New plan in PLAN.md: E1 content pillars ✅ shipped (weighted pillar rotation + recent-hook repetition guard + broader sources; verified ≥3 pillars per batch), E2 b-roll/music rotation ✅ shipped (idea-id-seeded result rotation, verified different clips + tracks), E3 Remotion motion-graphics reels ✅ shipped, then user judged v1 "not engaging" → E5 ad-style scene reels ✅ shipped (voiceover-paced scene cuts: Pollinations AI images + Pexels b-roll + kinetic headlines + whoosh SFX; replaces v1 in the 1-in-4 slot). E4 MCP question scoped out. **Phase E complete.**
- **Phase F shipped (2026-07-07)** — niche pivot + memes + trending audio. User found all-AI boring/low-reach. Research: IG API can't attach trending audio (only pre-embedded, or human taps at post time); top faceless niches = finance/psychology/memes. Built: (F1) `agents/meme_agent.py` meme-dump reels from Reddit via meme-api.com keyless proxy (Reddit JSON 403s unauth); (F2) `scripts/post_meme.py` + `meme.yml` = notification-publish — builds reel, hosts to Supabase, pings phone (ntfy) so user adds native trending audio in-app (~20s), no API publish; (F3) pillars rebalanced to psychology+money lead, AI minor. Verified e2e local + CI. Scene reels (E5) now default for every auto reel with CC music. **Next: watch analytics — memes vs value posts, tune pillar weights.**
- **Let it run** (user, 2026-06-30) — pipeline running on Groq-backed generation; review after a few days of analytics before adding Phase D.
- **Combined LLM quota** — Gemini + Groq free tiers now cover daily load; watch if heavy days exhaust both.
- **Vimeo CC clips** — occasional real-footage variety (cookie-free, LLM-vetted); thin niche pool so they skip when nothing good. B-roll voice reels are the daily base.
- **Notification channel** — wire the chosen secret (ntfy topic / Discord / Slack webhook).

### ⬜ Pending
- **Phase D (optional, post-analytics):** theme/angle rotation to avoid repetition; music asset cache; evaluate talking-head/avatar reels; YouTube-from-residential-IP for premium tutorial clips.
- #11 Media kit, #12 Sponsored slots (audience-gated — need reach to matter).
- #13–15 Scale (multi-account, cross-platform, SaaS).

---

## Phase 1: Growth Engine (Jul–Aug 2026)

| # | Task | Priority | Dates | Status |
|---|---|---|---|---|
| 1 | **Best-Time-to-Post optimizer** — analytics computes best hours + follower trend. ⚠️ REWORKED: exact-hour publish gating broke posting (GitHub cron delay) → now gates on quota + ~6h spacing instead | 🔴 High | Jul 1–7 | ✅ |
| 2 | **Comment auto-reply agent** — Auto-reply to comments within 1hr using Gemini contextual replies | 🔴 High | Jul 7–14 | ✅ |
| 3 | **Stories engagement bot** — Auto-repost latest post to Stories daily (drives profile visits). Note: API can't add poll/quiz/link stickers — plain image only | 🟡 Medium | Jul 14–21 | ✅ |
| 4 | **Link-in-bio manager** — Single bio link funnel: latest post → affiliate offers → lead magnet → product | 🔴 High | Jul 21–28 | ✅ |
| 5 | **Content performance dashboard** — per-post reach/likes/saves/shares + reach-weighted score, best/worst, eng-rate. In dashboard Analytics page | 🟡 Medium | Jul 28–Aug 4 | ✅ |
| 6 | **Follower growth tracker** — follower-count trend chart + per-post analytics. (Per-user unfollow alerts dropped — not exposed by IG API) | 🟢 Low | Aug 4–11 | ✅ |
| 7 | **Performance feedback loop** — top-scoring posts (by saves/shares) fed back into ResearchAgent to make more of what works. (True per-post A/B isn't possible on IG — can't split-test one post's hook) | 🟡 Medium | Aug 11–18 | ✅ |

## Phase 2: Monetization (Aug–Oct 2026)

| # | Task | Priority | Dates | Status |
|---|---|---|---|---|
| 8 | **Affiliate link engine** — Sovrn Commerce auto-affiliation live on tools.html (real merchant URLs → affiliate links client-side); bio auto-links; content nudges "link in bio". ✅ deployed. NB: only Sovrn-covered merchants actually earn (hover → redirect.viglink.com to confirm) | 🟣 Urgent | Aug 1–31 | ✅ |
| 9 | **Digital product pipeline** — "AI Productivity Pack" PDF (30 prompts, 8 categories; scripts/build_product.py) live on Gumroad, wired into bio "Shop" slot. ✅ deployed | 🔴 High | Aug 15–Sep 15 | ✅ |
| 10 | **Lead magnet + email capture** — Free "AI Tools Cheat Sheet" guide (guide.html) + Kit email-capture form embedded, linked from bio. ✅ live & deployed | 🔴 High | Sep 1–30 | ✅ |
| 11 | **Media kit generator** — Auto-generated from analytics for brand sponsorships ($200–1K/post) | 🟡 Medium | Oct 1–15 | ❌ |
| 12 | **Sponsored slot scheduler** — Rate card + calendar for paid posts alongside organic content | 🟡 Medium | Oct 15–31 | ❌ |

## Phase 3: Scale (Nov 2026+)

| # | Task | Priority | Dates | Status |
|---|---|---|---|---|
| 13 | **Multi-account mode** — Run same engine for 5 niches. One config per account. 5x revenue potential | 🟡 Medium | Nov 1–30 | ❌ |
| 14 | **Cross-platform repurposing** — IG reel → YouTube Shorts → TikTok → Twitter/X | 🟢 Low | Nov 15–Dec 15 | ❌ |
| 15 | **SaaS-ify the dashboard** — Multi-tenant SaaS. Sell this engine as a product | 🟢 Low | Dec 1–Jan 31 | ❌ |

---

## Already Shipped ✅

- Phase 2: Free stack migration (Gemini + Supabase + GitHub Actions)
- Instagram-Login API switch (IGAA tokens)
- 3x daily auto-publish (08:00, 14:00, 20:00 UTC)
- Meta token auto-refresh (monthly cron)
- Analytics feedback loop (ResearchAgent reads last week's performance)
- Carousel slide footer (handle + page counter)
- Inter fonts + size-aware fallback
- Error handling (Gemini 503 retry, lazy Meta creds, field guards)
- Hashtag rotation system (3 sets rotated by publish count)
- Reach-optimized captions/hooks
- TrendAgent (YouTube Data API + Google Trends + best-effort TikTok)
- Reel pipeline (ffmpeg slideshow → MP4 → Supabase Storage → Instagram)
- MusicAgent (Jamendo CC music baked into reels)
- CC YouTube clipper (cookies + deno + EJS → captioned reel, validated in CI)
- Best-Time-to-Post optimizer (adaptive gate: analytics best-hours, fallback slots, daily quota)
- Comment auto-reply agent (polls comments, Gemini replies, SKIP for spam, every 2h)
- Gemini 429/quota retry in shared _llm client
- Link-in-bio manager (GitHub Pages funnel, auto latest-post link, daily rebuild)
- Rich analytics: per-post performance + reach-weighted scoring, best/worst, follower-growth trend, correct IG-Login insight metrics (reach/saved/shares/total_interactions)
- Story auto-promo bot (reposts latest to Stories daily, once per post)
- Performance feedback loop (top posts → ResearchAgent makes more of what works)
- Affiliate engine #8 COMPLETE (Sovrn Commerce auto-affiliation live on tools.html + bio auto-link + FTC disclosure + content nudge)
- Lead magnet #10 COMPLETE (cheat-sheet guide + Kit email-capture form, deployed to Pages, linked from bio)
- Digital product #9 COMPLETE (AI Productivity Pack PDF on Gumroad, wired into bio)
- **Original AI voice reels** — edge-tts voiceover + synced middle captions + branded bg (replaced YouTube-repost reels); 2:1 reel/carousel mix
- Clip subtitles fixed — Whisper translate (always English) + stylish middle ASS captions (shared agents/_captions.py)
- Clipper dry-run preview mode (render without posting)
- **Publish gate fix** — quota+spacing instead of brittle exact-hour (cron-delay-proof); restored posting
- FLOW.md operating/maintenance guide; node_modules gitignored

**✅ PHASE 1 COMPLETE** — growth engine done. Next: Phase 2 monetization (#8 affiliate is the first revenue stream).
- OpenCode MCP setup (GitHub + Notion MCP)
- Notion architecture diagram (components) + flow diagram (process timeline) — embedded in project Notion page
- Global skill `notion-diagrams` at `~/.config/opencode/skills/notion-diagrams/` for repeatable diagram generation across projects
- **Cadence → 5 posts/day (2026-07-13)** — meme.yml cron now fires at 5 IST-tuned slots (08:30/13:00/17:30/20:30/23:00 IST); video↔image 50/50 alternation unchanged. Confirmed JAMENDO_CLIENT_ID is set (image reels have music); silent reels only from audio-less video-meme source clips (`-map 0:a?`), accepted as rare.
- **Live-pipeline hardening (2026-07-13)** — from a code review, fixed only the real live-path items: (1) ffmpeg `_run_ffmpeg` 300s timeout so a stalled HLS pull can't hang the run; (2) `post_meme` seen-set now capped by id COUNT not chars (no partial-id splicing); (3) `publish_story` no longer publishes a non-FINISHED video container; (4) `_rehost` temp file unlinked in `finally`. Skipped as dead-code/false-positive: legacy `publish_single_image`/`publish_carousel` KeyErrors, imgbb path, and `_db` `"upsert":"true"` (string is correct for the storage header).

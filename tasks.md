# Monetization Roadmap — Instagram Content Engine

Synced from Notion "Let's Ship" → Tasks database (linked to Instagram Content Agent project).

---

## 📊 Current Status (updated 2026-06-29)

### ✅ Done & running
- **Full content engine** — research (trends) → auto-approve → generate → publish, all on GitHub Actions cron.
- **Original AI voice reels** (NEW primary format) — hook → Gemini script → free edge-tts voiceover → synced middle captions → branded bg + music. Replaced low-quality YouTube reposts. **2 reels : 1 carousel** mix.
- **Posting FIXED** — best-time exact-hour gate was silently skipping every post (GitHub cron runs 60–90 min late). Reworked to **quota + spacing** gate; publishing resumed (12-post backlog now clearing ~3/day).
- **Monetization funnel live** — bio page → free cheat-sheet (Kit email capture) → Sovrn affiliate tools page → Gumroad product. All deployed on GitHub Pages.
- Comment auto-reply, Stories auto-promo, rich analytics dashboard, performance feedback loop, hashtag rotation.
- **FLOW.md** maintenance guide.

### 🔄 In progress / needs attention
- **Gemini free-tier quota** is the current bottleneck — heavy days hit the daily 429 cap, which skips script/idea generation. **Recommended: enable billing on the Gemini key** (a few $/mo) to remove it.
- **YouTube clipper** — works but cookies expire (~weeks); now *optional* since voice reels are primary. PO-token provider (cookie-free automation) was chosen but **not built** — deferred.

### ⬜ Pending (audience-gated — low value until followers grow)
- #11 Media kit, #12 Sponsored slots (need reach to matter).
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

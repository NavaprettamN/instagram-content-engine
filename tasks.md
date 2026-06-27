# Monetization Roadmap — Instagram Content Engine

Synced from Notion "Let's Ship" → Tasks database (linked to Instagram Content Agent project).

## Phase 1: Growth Engine (Jul–Aug 2026)

| # | Task | Priority | Dates | Status |
|---|---|---|---|---|
| 1 | **Best-Time-to-Post optimizer** — AnalyticsAgent analyzes engagement by hour/day → auto-tunes publish.yml cron slots | 🔴 High | Jul 1–7 | ✅ |
| 2 | **Comment auto-reply agent** — Auto-reply to comments within 1hr using Gemini contextual replies | 🔴 High | Jul 7–14 | ✅ |
| 3 | **Stories engagement bot** — Auto-post daily story with polls/quizzes/Q&A stickers | 🟡 Medium | Jul 14–21 | ❌ |
| 4 | **Link-in-bio manager** — Single bio link funnel: latest post → affiliate offers → lead magnet → product | 🔴 High | Jul 21–28 | ✅ |
| 5 | **Content performance dashboard** — "Post X topic at Y time for Z engagement". Rank topics by saves/shares/comments | 🟡 Medium | Jul 28–Aug 4 | ❌ |
| 6 | **Follower growth tracker** — Source tracking (hashtag vs explore vs profile), unfollow alerts | 🟢 Low | Aug 4–11 | ❌ |
| 7 | **Reach-optimized hooks A/B test** — 3 hook variants per idea, track which drives more saves/shares | 🟡 Medium | Aug 11–18 | ❌ |

## Phase 2: Monetization (Aug–Oct 2026)

| # | Task | Priority | Dates | Status |
|---|---|---|---|---|
| 8 | **Affiliate link engine** — Promote AI tools in content, auto-insert affiliate links, track commissions. Target: $500–2K/mo | 🟣 Urgent | Aug 1–31 | ❌ |
| 9 | **Digital product pipeline** — Create "AI Productivity Pack" (templates, prompts). Sell via Gumroad/Lemon Squeezy | 🔴 High | Aug 15–Sep 15 | ❌ |
| 10 | **Lead magnet + email capture** — Free "Top 50 AI Tools" PDF → email signup → ConvertKit nurture → upsell | 🔴 High | Sep 1–30 | ❌ |
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
- OpenCode MCP setup (GitHub + Notion MCP)

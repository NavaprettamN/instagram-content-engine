# System Architecture

## What this system does

An automated Instagram content pipeline for the **AI Productivity Tools** niche. AI generates ideas and carousel images; a human approves them via a web dashboard; the system publishes to Instagram on a schedule.

## Pipeline (data flow)

```
┌─────────────────────────────────────────────────────────────────┐
│                        SCHEDULED (GitHub Actions)                │
│                                                                  │
│  07:00 UTC daily                                                 │
│  ResearchAgent                                                   │
│    ├── RSS feeds (TechCrunch AI, The Verge, Hacker News)        │
│    ├── Reddit hot posts (r/artificial, r/productivity, etc.)     │
│    └── Gemini 2.5 Flash → 5 content ideas                       │
│         └── Saved to Supabase: status = pending_review          │
│                                                                  │
│  Every 2h (only if approved ideas exist)                         │
│  ContentAgent + DesignAgent                                      │
│    ├── ContentAgent → Gemini → full carousel structure           │
│    ├── HashtagAgent → Gemini → 3 rotating hashtag sets          │
│    ├── DesignAgent → Pillow → 7-8 PNG slides (1080×1080)        │
│    └── Saved to Supabase: status = designed                     │
│                                                                  │
│  10:00 and 18:00 UTC daily                                       │
│  PublishingAgent                                                  │
│    ├── Uploads PNGs to imgbb (free public hosting)               │
│    ├── Creates carousel container via Meta Graph API v19.0       │
│    └── Publishes → Supabase: status = published                 │
│                                                                  │
│  Sunday 20:00 UTC weekly                                         │
│  AnalyticsAgent                                                  │
│    ├── Pulls account metrics from Meta Graph API                 │
│    └── Gemini → weekly performance analysis → Supabase          │
└─────────────────────────────────────────────────────────────────┘

                  ▼ Human approval gate ▼

┌─────────────────────────────────────────────────────────────────┐
│                  Streamlit Dashboard (dashboard.py)              │
│                  Hosted: Streamlit Community Cloud               │
│                                                                  │
│  Pages:                                                          │
│  • Dashboard     — pipeline metrics at a glance                 │
│  • Approval Center — review/edit/approve/reject ideas           │
│  • Content Queue — all ideas by status                          │
│  • Analytics     — published content performance + AI analysis  │
│  • Run Agents    — manually trigger any agent                   │
│  • Settings      — niche, brand voice, sources                  │
└─────────────────────────────────────────────────────────────────┘
```

## Content lifecycle (status field)

```
pending_review  →  approved  →  designed  →  published
                ↘  rejected
```

| Status | Meaning |
|---|---|
| `pending_review` | Research Agent generated the idea; waiting for human |
| `approved` | Human approved; Content + Design agents will process it |
| `rejected` | Human rejected; ignored by all scheduled jobs |
| `designed` | Images generated; ready to publish |
| `published` | Live on Instagram; `post_id` and `published_at` populated |

## Free stack summary

| Layer | Service | Notes |
|---|---|---|
| LLM | Gemini 2.5 Flash | Free tier ~1500 req/day |
| Image generation | Pillow (local) | Zero cost, no API |
| Image hosting | imgbb | Unlimited free; Meta needs public URLs |
| Scheduler | GitHub Actions cron | 2000 min/mo free |
| Database | Supabase Postgres | 500 MB free tier |
| Dashboard | Streamlit Community Cloud | Free, auto-deploys from GitHub |
| Publishing | Meta Graph API v19.0 | Free; Business account required |

## Key design rules

- **Secrets** (API keys, tokens) always come from environment variables or `.env`. Never hardcoded.
- **Non-secrets** (niche, brand colors, RSS URLs, schedule times) live in `config.yaml`.
- **All agents are stateless** — they read/write Supabase; no local state between runs.
- **GitHub Actions runs are ephemeral** — generated images are uploaded to imgbb before publishing; PNGs are not persisted across Action runs. Images are only generated locally (via dashboard "Generate" button) or by the Action which uploads immediately.

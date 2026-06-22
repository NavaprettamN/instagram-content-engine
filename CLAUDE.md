# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit dashboard (primary interface)
streamlit run dashboard.py

# Manually trigger the research agent (generates 5 ideas → Supabase)
python -c "
import yaml
from agents.research_agent import ResearchAgent
config = yaml.safe_load(open('config.yaml'))
ResearchAgent(config).run()
"

# Manually run generate pipeline for approved ideas
python -c "
import json, yaml
from agents.content_agent import ContentAgent
from agents.design_agent import DesignAgent
from agents._db import get_ideas, update_idea
config = yaml.safe_load(open('config.yaml'))
for idea in get_ideas(status='approved'):
    content = ContentAgent(config).generate_content(idea)
    paths   = DesignAgent(config).generate_carousel_images(content, idea['id'])
    update_idea(idea['id'], generated_content=json.dumps(content),
                image_paths=json.dumps(paths), status='designed')
"
```

## Architecture

A multi-agent Instagram automation system with a human-in-the-loop approval workflow. AI generates ideas and carousel images → human approves via dashboard → system publishes on schedule.

### Pipeline

```
ResearchAgent (07:00 UTC daily via GitHub Actions)
  → RSS + Reddit → Gemini 2.5 Flash → 5 ideas → Supabase: pending_review

[Human approves in Streamlit dashboard]

ContentAgent + DesignAgent (every 2h via GitHub Actions)
  → Gemini → carousel JSON structure
  → Pillow → 7-8 PNG slides (1080×1080) → uploaded to imgbb
  → Supabase: status=designed, image_paths=[imgbb URLs]

PublishingAgent (10:00 + 18:00 UTC via GitHub Actions)
  → Meta Graph API v19.0 → carousel post on Instagram
  → Supabase: status=published, post_id=<IG media ID>

AnalyticsAgent (Sunday 20:00 UTC via GitHub Actions)
  → Meta API metrics → Gemini analysis → Supabase analytics_snapshots
```

### Key files

| File | Purpose |
|---|---|
| `agents/_llm.py` | Shared Gemini 2.5 Flash client — used by all AI agents |
| `agents/_db.py` | Supabase wrapper — used by all agents and dashboard |
| `agents/research_agent.py` | RSS/Reddit → Gemini ideas → Supabase |
| `agents/content_agent.py` | Approved idea → full carousel/reel JSON |
| `agents/design_agent.py` | Carousel JSON → PNG slides (Pillow, no API) |
| `agents/publishing_agent.py` | imgbb upload + Meta Graph API publish |
| `agents/analytics_agent.py` | Meta metrics → Gemini weekly analysis |
| `agents/hashtag_agent.py` | Topic → 3 rotating hashtag sets |
| `dashboard.py` | Streamlit approval UI, wraps `_db.py` |
| `config.yaml` | Non-secret config: niche, brand colors, RSS URLs |
| `.env` | All secrets (never committed) |
| `.github/workflows/` | Four cron jobs: research, generate, publish, analytics |

### Database (Supabase Postgres)

Three tables — see `docs/database.md` for full schema.

- **`content_ideas`** — full lifecycle: `pending_review → approved → designed → published`
- **`analytics_snapshots`** — weekly metrics + AI analysis text
- **`config`** — reserved key-value store

Access only via `agents/_db.py` functions (`get_ideas`, `update_idea`, etc.) — never import the Supabase client directly in agents or dashboard.

### Environment variables

All loaded via `python-dotenv` (`load_dotenv()` at top of each agent). Required:

```
GEMINI_API_KEY          # Google AI Studio
META_ACCESS_TOKEN       # Facebook Page Access Token (60-day, refresh monthly)
INSTAGRAM_USER_ID       # IG Business Account ID (numeric, e.g. 17841449119738027)
META_APP_ID / META_APP_SECRET  # For token refresh
IMGBB_API_KEY           # Image hosting
SUPABASE_URL / SUPABASE_KEY    # Database
```

### Free stack

- **LLM:** Gemini 2.5 Flash (`google-genai` SDK) — replaces Azure OpenAI
- **Images:** Pillow locally + imgbb hosting — zero cost
- **Scheduler:** GitHub Actions cron — no always-on server
- **DB:** Supabase Postgres free tier (500 MB)
- **Dashboard:** Streamlit Community Cloud (not Vercel — this is a Python/Streamlit app)

## Docs

| File | Contents |
|---|---|
| `docs/architecture.md` | System diagram, lifecycle, free stack table |
| `docs/agents.md` | Each agent's interface and output schema |
| `docs/database.md` | Supabase schema + `_db.py` API reference |
| `docs/setup.md` | Step-by-step credential and deployment guide |
| `PLAN.md` | Original implementation plan with feasibility analysis |

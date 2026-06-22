# Setup Guide

## Prerequisites

- Python 3.10+
- Git + GitHub account
- Instagram Business or Creator account
- Facebook Page (linked to the Instagram account)

## 1. Clone and install

```bash
git clone <your-repo-url>
cd instagram-content-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Credentials checklist

All secrets go in `.env` at the project root. See `.env.example` for the template.

| Variable | Where to get it |
|---|---|
| `META_ACCESS_TOKEN` | Meta Graph API Explorer → long-lived Page Access Token (60-day) |
| `INSTAGRAM_USER_ID` | Query `/{PAGE_ID}?fields=instagram_business_account` after getting token |
| `META_APP_ID` | developers.facebook.com → your app → App Settings → Basic |
| `META_APP_SECRET` | Same as above (click Show) |
| `GEMINI_API_KEY` | aistudio.google.com → Create API key |
| `IMGBB_API_KEY` | api.imgbb.com (free account) |
| `SUPABASE_URL` | supabase.com → Project → Settings → API → Project URL |
| `SUPABASE_KEY` | Same page → service_role key (not the anon key) |

## 3. Meta token setup (detailed)

### One-time setup
1. Go to developers.facebook.com → Create App → type "Business"
2. Add product: Instagram Graph API
3. Go to Tools → Graph API Explorer
4. Select your app, generate User Access Token with permissions:
   - `pages_show_list`, `pages_read_engagement`
   - `instagram_basic`, `instagram_content_publish`
   - `business_management`
5. Exchange for long-lived token (60 days):
   ```
   GET https://graph.facebook.com/v19.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id={APP_ID}
     &client_secret={APP_SECRET}
     &fb_exchange_token={SHORT_LIVED_TOKEN}
   ```
6. Get your Page Access Token (doesn't expire):
   ```
   GET /me/accounts?fields=name,access_token,instagram_business_account
   ```
   Use the `access_token` value from the response as `META_ACCESS_TOKEN`.

### Token refresh (every ~60 days)
Re-run step 5 with the current long-lived token as the `fb_exchange_token` — it resets the expiry.

## 4. Supabase database schema

The schema is auto-applied on first setup. To apply manually, run this SQL in the Supabase SQL Editor:

```sql
CREATE TABLE IF NOT EXISTS content_ideas (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50),
    hook TEXT,
    outline TEXT,
    caption_draft TEXT,
    hashtags TEXT,
    status VARCHAR(50) DEFAULT 'pending_review',
    created_at TIMESTAMP DEFAULT NOW(),
    engagement_estimate VARCHAR(50),
    generated_content TEXT,
    image_paths TEXT,
    published_at TIMESTAMP,
    post_id VARCHAR(100),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id SERIAL PRIMARY KEY,
    date DATE,
    followers INTEGER,
    reach INTEGER,
    impressions INTEGER,
    profile_views INTEGER,
    engagement_rate FLOAT,
    analysis TEXT
);

CREATE TABLE IF NOT EXISTS config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT
);
```

## 5. Custom fonts (optional)

For best-looking carousels, download **Inter** from fonts.google.com and place:
- `fonts/Inter-Bold.ttf`
- `fonts/Inter-Regular.ttf`

Without these, Pillow falls back to its built-in bitmap font (still functional but smaller/less crisp).

## 6. Run locally

```bash
# Start the approval dashboard
streamlit run dashboard.py

# Manually run the research agent once
python -c "
import yaml
from agents.research_agent import ResearchAgent
config = yaml.safe_load(open('config.yaml'))
ResearchAgent(config).run()
"

# Manually run full generate pipeline for approved ideas
python -c "
import yaml
from agents.content_agent import ContentAgent
from agents.design_agent import DesignAgent
from agents._db import get_ideas, update_idea
import json

config = yaml.safe_load(open('config.yaml'))
for idea in get_ideas(status='approved'):
    content = ContentAgent(config).generate_content(idea)
    paths   = DesignAgent(config).generate_carousel_images(content, idea['id'])
    update_idea(idea['id'], generated_content=json.dumps(content),
                image_paths=json.dumps(paths), status='designed')
print('Done')
"
```

## 7. Deploy the dashboard (Streamlit Community Cloud)

1. Push the repo to GitHub
2. Go to share.streamlit.io → New app → connect the repo
3. Set **Main file path** to `dashboard.py`
4. Under **Secrets**, add all variables from your `.env` file in TOML format:
   ```toml
   SUPABASE_URL = "https://xxx.supabase.co"
   SUPABASE_KEY = "eyJ..."
   META_ACCESS_TOKEN = "EAA..."
   INSTAGRAM_USER_ID = "178..."
   GEMINI_API_KEY = "AQ..."
   IMGBB_API_KEY = "f52..."
   ```
5. Deploy — the app is now always accessible at a public URL

## 8. Set up the scheduler (GitHub Actions)

1. In your GitHub repo → Settings → Secrets and variables → Actions → New repository secret
2. Add each variable from `.env` as a secret (same names)
3. The four workflow files in `.github/workflows/` are already configured:
   - `research.yml` — runs at 07:00 UTC daily
   - `generate.yml` — runs every 2 hours
   - `publish.yml` — runs at 10:00 and 18:00 UTC daily
   - `analytics.yml` — runs every Sunday at 20:00 UTC
4. To test manually: GitHub → Actions tab → select a workflow → "Run workflow"

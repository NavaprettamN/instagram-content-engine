# Agent Reference

All agents live in `agents/`. Each is a self-contained class instantiated with the `config` dict loaded from `config.yaml`. Secrets are read from environment variables inside the agent (via `agents/_llm.py` and `agents/_db.py` helpers).

---

## Shared helpers

### `agents/_llm.py`
Gemini 2.5 Flash client. Used by all AI agents.

```python
from agents._llm import generate_text

# Plain text response
text = generate_text("Write a hook for an AI productivity post", system="You are an expert copywriter")

# JSON response (returns parsed dict/list)
data = generate_text("Generate 5 ideas as JSON array", json_response=True, temperature=0.8)
```

### `agents/_db.py`
Supabase Postgres wrapper. Used by all agents and `dashboard.py`.

```python
from agents._db import get_ideas, get_idea, count_ideas, save_idea, update_idea
from agents._db import get_analytics, save_analytics

ideas = get_ideas(status="pending_review")          # list of dicts
ideas = get_ideas(status=["approved", "designed"])  # multiple statuses
idea  = get_idea(42)                                # single dict by id
n     = count_ideas("pending_review")               # int
id_   = save_idea({"hook": "...", "status": "pending_review", ...})
update_idea(42, status="approved", notes="looks good")
```

---

## ResearchAgent

**File:** `agents/research_agent.py`  
**Triggered:** Daily 07:00 UTC via GitHub Actions `research.yml`  
**Purpose:** Gather trends, generate 5 content ideas, save to DB.

```python
from agents.research_agent import ResearchAgent
import yaml
config = yaml.safe_load(open("config.yaml"))
agent = ResearchAgent(config)
ideas = agent.run()  # returns list of saved idea dicts
```

**Pipeline:**
1. `gather_trends()` — parses `config["rss_feeds"]` via feedparser
2. `gather_reddit_ideas()` — hits Reddit JSON API for `config["subreddits"]`
3. `generate_content_ideas(trends, reddit)` — Gemini prompt → 5 ideas as JSON
4. `save_ideas_to_db(ideas)` — writes each idea with `status=pending_review`

**Output schema saved to DB:**
```json
{
  "content_type": "carousel",
  "hook": "7 AI tools that replaced my $500/mo stack",
  "outline": ["Tool 1...", "Tool 2..."],
  "caption_draft": "Full caption text...",
  "hashtags": ["#aitools", "#productivity"],
  "engagement_estimate": "high",
  "status": "pending_review"
}
```

---

## ContentAgent

**File:** `agents/content_agent.py`  
**Triggered:** Every 2h via GitHub Actions `generate.yml` (processes `status=approved` ideas)  
**Purpose:** Expand an approved idea into a full carousel structure.

```python
from agents.content_agent import ContentAgent
agent = ContentAgent(config)
content = agent.generate_content(idea_dict)  # routes by content_type
```

**Methods:**
- `generate_carousel(idea)` → full carousel JSON (slides 1–8 + caption + alt text)
- `generate_reel_script(idea)` → reel script JSON (voiceover, segments, CTA)
- `generate_content(idea)` → routes to the above based on `idea["content_type"]`

**Carousel output schema:**
```json
{
  "slide_1_hook": "Bold headline ≤8 words",
  "slide_1_subtext": "One-line teaser ≤15 words",
  "slides": [
    {"slide_number": 2, "headline": "...", "body": "...", "icon_suggestion": "🤖"}
  ],
  "slide_final_cta": "Follow for more AI productivity tips",
  "caption": "Full 150-200 word caption with hashtags",
  "alt_text": "Accessibility description"
}
```

---

## HashtagAgent

**File:** `agents/hashtag_agent.py`  
**Triggered:** Part of `generate.yml` run (called alongside ContentAgent)  
**Purpose:** Generate 3 rotating hashtag sets per content topic.

```python
from agents.hashtag_agent import HashtagAgent
agent = HashtagAgent(config)
sets = agent.generate_hashtag_sets("AI tools for developers", num_sets=3)
```

**Strategy per set:** 2 high-volume (500K+ posts) + 3 medium (50K-500K) + 3 low (5K-50K).

---

## DesignAgent

**File:** `agents/design_agent.py`  
**Triggered:** Part of `generate.yml` run (called after ContentAgent)  
**Purpose:** Render carousel JSON into 1080×1080 PNG slides using Pillow.

```python
from agents.design_agent import DesignAgent
agent = DesignAgent(config)
image_paths = agent.generate_carousel_images(carousel_content, idea_id)
# Returns: list of local PNG paths
# e.g. ["generated_content/carousel_42/slide_01.png", ...]
```

**Slide layout:**
- Slide 1: Hook headline + subtext + accent line (brand red bar)
- Slides 2–7: Icon emoji + headline (accent color) + body text
- Final slide: CTA text + "Save • Share • Follow"

**Fonts:** Looks for `fonts/Inter-Bold.ttf` and `fonts/Inter-Regular.ttf`; falls back to Pillow default if missing.

---

## PublishingAgent

**File:** `agents/publishing_agent.py`  
**Triggered:** 10:00 and 18:00 UTC via GitHub Actions `publish.yml`  
**Purpose:** Upload images to imgbb, publish carousel to Instagram via Meta Graph API.

```python
from agents.publishing_agent import PublishingAgent
agent = PublishingAgent(config)
result = agent.publish_carousel(["slide_01.png", "slide_02.png"], caption)
# result["id"] = Instagram post ID
```

**Methods:**
- `upload_image_to_hosting(image_path)` → uploads to imgbb, returns public URL
- `publish_single_image(image_path, caption)` → posts single image
- `publish_carousel(image_paths, caption)` → posts multi-image carousel
- `publish_reel(video_url, caption)` → posts reel (video must be pre-hosted)

**Meta Graph API flow:**
1. Upload each PNG to imgbb → get public URL
2. Create a media container per image (`is_carousel_item=True`)
3. Create carousel container with all child IDs
4. Wait 10s for processing
5. Call `media_publish` → get post ID

---

## AnalyticsAgent

**File:** `agents/analytics_agent.py`  
**Triggered:** Sunday 20:00 UTC via GitHub Actions `analytics.yml`  
**Purpose:** Pull account metrics and generate a weekly AI analysis.

```python
from agents.analytics_agent import AnalyticsAgent
agent = AnalyticsAgent(config)
insights = agent.get_account_insights(days=7)
posts    = agent.get_recent_posts(limit=25)
analysis = agent.generate_weekly_analysis(insights, posts)
```

**Meta API metrics pulled:**
- Account: impressions, reach, follower_count, profile_views
- Per post: impressions, reach, engagement, saved, shares, like_count, comments_count

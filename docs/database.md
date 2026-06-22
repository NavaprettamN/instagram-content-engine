# Database Reference

**Engine:** Supabase Postgres (free tier, 500 MB)  
**Access:** Via `agents/_db.py` helper in all Python code — never use the Supabase client directly in agents or dashboard.

---

## Table: `content_ideas`

Primary lifecycle table. Every content idea lives here from creation to publication.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-incrementing integer |
| `content_type` | VARCHAR(50) | `carousel`, `reel`, or `static_image` |
| `hook` | TEXT | Short attention-grabbing headline (the "scroll stopper") |
| `outline` | TEXT | JSON array of 3–5 bullet points: `["Point 1", "Point 2"]` |
| `caption_draft` | TEXT | Full Instagram caption (150–200 words) |
| `hashtags` | TEXT | JSON array of hashtags: `["#aitools", "#productivity"]` |
| `status` | VARCHAR(50) | See lifecycle below |
| `created_at` | TIMESTAMP | Set by ResearchAgent when idea is first saved |
| `engagement_estimate` | VARCHAR(50) | `high`, `medium`, or `low` (AI's prediction) |
| `generated_content` | TEXT | JSON blob of full carousel/reel structure (set by ContentAgent) |
| `image_paths` | TEXT | JSON array of local PNG paths (set by DesignAgent) |
| `published_at` | TIMESTAMP | Set when PublishingAgent successfully posts |
| `post_id` | VARCHAR(100) | Instagram media ID returned by Meta Graph API |
| `notes` | TEXT | Human notes from dashboard approval UI |

### Status lifecycle

```
pending_review → approved → designed → published
             ↘ rejected
```

| Status | Set by |
|---|---|
| `pending_review` | ResearchAgent (initial) |
| `approved` | Human via dashboard Approval Center |
| `rejected` | Human via dashboard Approval Center |
| `designed` | ContentAgent + DesignAgent pipeline |
| `published` | PublishingAgent after successful Meta API call |

---

## Table: `analytics_snapshots`

Weekly performance snapshots. One row per analytics run.

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PK | Auto-incrementing integer |
| `date` | DATE | Date the snapshot was taken |
| `followers` | INTEGER | Total follower count at time of snapshot |
| `reach` | INTEGER | Weekly unique accounts reached |
| `impressions` | INTEGER | Weekly total impressions |
| `profile_views` | INTEGER | Weekly profile visits |
| `engagement_rate` | FLOAT | Computed engagement rate for the week |
| `analysis` | TEXT | Gemini-generated markdown analysis report |

---

## Table: `config`

Key-value store for runtime configuration overrides. Currently unused by code; reserved for future dashboard settings persistence.

| Column | Type | Description |
|---|---|---|
| `key` | VARCHAR(100) PK | Setting name |
| `value` | TEXT | Setting value (always stored as string) |

---

## `agents/_db.py` API reference

```python
from agents._db import (
    get_ideas, get_idea, count_ideas, save_idea, update_idea,
    get_analytics, save_analytics
)

# Read
ideas = get_ideas()                             # all ideas, newest first
ideas = get_ideas(status="pending_review")      # filter by single status
ideas = get_ideas(status=["approved","designed"])# filter by multiple
idea  = get_idea(42)                            # single row as dict, or None
n     = count_ideas("pending_review")           # integer count

# Write
new_id = save_idea({                            # returns new row id
    "content_type": "carousel",
    "hook": "...",
    "status": "pending_review",
    ...
})
update_idea(42, status="approved", notes="ok") # keyword args = columns

# Analytics
snaps = get_analytics(limit=10)                # newest first
save_analytics({
    "date": "2026-06-23",
    "followers": 142,
    "analysis": "..."
})
```

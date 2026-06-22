import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_client: Client = None

def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    return _client

# ── content_ideas ──────────────────────────────────────────────────

def get_ideas(status=None):
    q = _get_client().table("content_ideas").select("*")
    if status:
        if isinstance(status, list):
            q = q.in_("status", status)
        else:
            q = q.eq("status", status)
    return q.order("created_at", desc=True).execute().data

def get_idea(idea_id):
    result = _get_client().table("content_ideas").select("*").eq("id", idea_id).execute()
    return result.data[0] if result.data else None

def count_ideas(status):
    result = _get_client().table("content_ideas").select("id", count="exact").eq("status", status).execute()
    return result.count or 0

def save_idea(idea_dict):
    result = _get_client().table("content_ideas").insert(idea_dict).execute()
    return result.data[0]["id"]

def update_idea(idea_id, **fields):
    _get_client().table("content_ideas").update(fields).eq("id", idea_id).execute()

# ── analytics_snapshots ────────────────────────────────────────────

def get_analytics(limit=10):
    return _get_client().table("analytics_snapshots").select("*").order("date", desc=True).limit(limit).execute().data

def save_analytics(snapshot_dict):
    _get_client().table("analytics_snapshots").insert(snapshot_dict).execute()

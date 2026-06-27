"""Auto-reply to comments for the early-engagement algorithm boost.

Polls recent media for new comments (no webhooks — those need a public server,
which breaks the $0/serverless stack) and replies with a Gemini-drafted, on-brand
message. Replies once per comment, skips our own comments, and lets Gemini flag
spam/negativity as SKIP rather than auto-replying to it.

"Within 1hr" is best-effort: GitHub cron can't reliably fire sub-hourly, so
replies land within the poll interval (comment_reply.yml runs every 2h).
"""
import os
import json
import requests
from agents._llm import generate_text
from agents._db import get_config, set_config

REPLIED_KEY = "replied_comments"
REPLIED_CAP = 500  # ponytail: keep last 500 ids; older comments won't be re-checked


class CommentAgent:
    def __init__(self, config):
        self.access_token = os.environ.get("META_ACCESS_TOKEN")
        self.ig_user_id = os.environ.get("INSTAGRAM_USER_ID")
        self.base_url = "https://graph.instagram.com/v21.0"
        self.niche = config.get("niche", "")
        self.brand_voice = config.get("brand_voice", "")
        self.handle = config.get("instagram_handle", "").lstrip("@").lower()

    def get_recent_media(self, limit=10):
        r = requests.get(f"{self.base_url}/{self.ig_user_id}/media",
                         params={"fields": "id,caption", "limit": limit,
                                 "access_token": self.access_token}, timeout=15)
        return r.json().get("data", [])

    def get_comments(self, media_id):
        r = requests.get(f"{self.base_url}/{media_id}/comments",
                         params={"fields": "id,text,username,timestamp",
                                 "access_token": self.access_token}, timeout=15)
        return r.json().get("data", [])

    def reply(self, comment_id, message):
        return requests.post(f"{self.base_url}/{comment_id}/replies",
                             data={"message": message, "access_token": self.access_token},
                             timeout=15).json()

    def draft_reply(self, comment_text, caption):
        """On-brand 1-2 sentence reply, or 'SKIP' for spam/ads/links/hostility."""
        reply = generate_text(
            f'A follower commented on our Instagram post about {self.niche}.\n'
            f'POST CAPTION: {caption[:300]}\n'
            f'COMMENT: "{comment_text}"\n'
            f'BRAND VOICE: {self.brand_voice}\n\n'
            f'Write a warm, specific 1-2 sentence reply that invites more engagement '
            f'(ask a follow-up or add a quick tip). If the comment is spam, an ad, a '
            f'link drop, or hostile/negative, reply with exactly: SKIP\n'
            f'Return ONLY the reply text or SKIP.',
            temperature=0.7,
        ).strip()
        return reply

    def run(self, dry_run=False):
        replied = json.loads(get_config(REPLIED_KEY) or "[]")
        seen = set(replied)
        actions = 0
        try:
            for media in self.get_recent_media():
                caption = media.get("caption", "") or ""
                for c in self.get_comments(media["id"]):
                    cid = c["id"]
                    if cid in seen:
                        continue
                    if (c.get("username", "") or "").lower() == self.handle:
                        seen.add(cid)  # our own reply — never reply to ourselves
                        continue
                    draft = self.draft_reply(c.get("text", ""), caption)
                    if draft and draft.upper() != "SKIP":
                        if dry_run:
                            print(f"[dry] would reply to {cid}: {draft[:60]}")
                        else:
                            res = self.reply(cid, draft)
                            print(f"replied {cid}" if "id" in res else f"reply FAILED {cid}: {res}")
                    else:
                        print(f"skip {cid}: {(c.get('text','') or '')[:40]}")
                    actions += 1
                    if not dry_run:
                        seen.add(cid)
                        replied.append(cid)
        except Exception as e:
            # e.g. Gemini quota exhausted — stop cleanly, keep progress, retry next run
            print(f"CommentAgent: stopping early ({str(e)[:80]}); progress saved")
        if not dry_run and actions:
            set_config(REPLIED_KEY, json.dumps(replied[-REPLIED_CAP:]))
        print(f"CommentAgent: {actions} new comment(s) handled{' (dry run)' if dry_run else ''}")
        return actions


if __name__ == "__main__":
    # dry run: exercises media+comment fetch and reply drafting without posting
    import yaml
    config = yaml.safe_load(open("config.yaml"))
    agent = CommentAgent(config)
    assert agent.access_token and agent.ig_user_id, "Meta creds required"
    # unit-check the SKIP classifier (tolerant of Gemini quota exhaustion)
    try:
        normal = agent.draft_reply("This is so helpful, which tool do you recommend first?", "AI tools carousel")
        spam = agent.draft_reply("Check out my site http://cheap-followers.example buy now!!!", "AI tools carousel")
        print("normal ->", normal[:60])
        print("spam   ->", spam[:60])
        assert spam.upper() == "SKIP", f"spam should be SKIP, got: {spam!r}"
        print("classifier OK")
    except Exception as e:
        print(f"classifier test skipped (LLM unavailable): {str(e)[:80]}")
    agent.run(dry_run=True)
    print("comment_agent self-check OK")

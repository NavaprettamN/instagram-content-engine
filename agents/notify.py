"""Optional post notifications. Best-effort: if no channel env var is set, it's a
no-op; a failed send never breaks publishing.

Pick ONE by setting its env var (checked in this order):
  NTFY_TOPIC      -> pushes to https://ntfy.sh/<topic> (free, no signup; install the
                     ntfy app and subscribe to the topic). Topic is a secret-ish
                     string only you know.
  DISCORD_WEBHOOK -> a Discord channel webhook URL.
  SLACK_WEBHOOK   -> a Slack incoming-webhook URL.
"""
import os
import requests


def send(title, message, url=None):
    """Send a notification through whichever channel is configured. Returns True
    if something was sent, False otherwise. Never raises."""
    try:
        topic = os.environ.get("NTFY_TOPIC")
        if topic:
            # ntfy headers must be ASCII/latin-1 — strip emoji etc. from the title
            # (body keeps full UTF-8). Hooks can contain emoji, so this is required.
            safe_title = (title or "New post").encode("ascii", "ignore").decode() or "New post"
            headers = {"Title": safe_title}
            if url:
                headers["Click"] = url  # tapping the notification opens the post
            requests.post(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"),
                          headers=headers, timeout=15)
            return True
        discord = os.environ.get("DISCORD_WEBHOOK")
        if discord:
            body = f"**{title}**\n{message}" + (f"\n{url}" if url else "")
            requests.post(discord, json={"content": body}, timeout=15)
            return True
        slack = os.environ.get("SLACK_WEBHOOK")
        if slack:
            body = f"*{title}*\n{message}" + (f"\n{url}" if url else "")
            requests.post(slack, json={"text": body}, timeout=15)
            return True
    except Exception as e:
        print(f"notify: send failed ({str(e)[:80]})")
    return False


if __name__ == "__main__":
    # ponytail: smoke check — with no channel env set, send() is a clean no-op.
    assert send("test", "hello") is False, "expected no-op without a channel"
    print("notify no-op path OK")

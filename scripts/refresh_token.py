"""Refresh the long-lived Meta token and print the Page token to stdout.

Run monthly (well inside the ~60-day window). Prints ONLY the new Page access
token on the last stdout line so a workflow can capture it; everything else
goes to stderr.

    python -m scripts.refresh_token
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH = "https://graph.facebook.com/v19.0"


def log(*a):
    print(*a, file=sys.stderr)


def main():
    token = os.environ["META_ACCESS_TOKEN"]
    app_id = os.environ["META_APP_ID"]
    app_secret = os.environ["META_APP_SECRET"]
    ig_user_id = os.environ["INSTAGRAM_USER_ID"]

    # 1. Re-exchange for a fresh long-lived user token (resets the 60-day clock).
    r = requests.get(f"{GRAPH}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": token,
    }).json()
    if "access_token" not in r:
        log("Exchange failed:", r)
        sys.exit(1)
    user_token = r["access_token"]

    # 2. Find the Page that owns the IG business account, grab its Page token.
    pages = requests.get(f"{GRAPH}/me/accounts", params={
        "fields": "id,access_token,instagram_business_account",
        "access_token": user_token,
    }).json()
    for page in pages.get("data", []):
        if str(page.get("instagram_business_account", {}).get("id")) == str(ig_user_id):
            log(f"Refreshed Page token for page {page['id']}")
            print(page["access_token"])  # the one line the workflow captures
            return
    log("No page found linked to INSTAGRAM_USER_ID. Pages seen:", pages)
    sys.exit(1)


if __name__ == "__main__":
    main()

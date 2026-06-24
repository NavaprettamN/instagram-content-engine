"""Refresh the long-lived Instagram-Login token and print the new one to stdout.

The IGAA token (Instagram API with Instagram Login) refreshes with a single call
to graph.instagram.com — no app id/secret, no Facebook Page. Run monthly, well
inside the ~60-day window. Prints ONLY the new token on the last stdout line;
everything else goes to stderr.

    python -m scripts.refresh_token
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()


def main():
    token = os.environ["META_ACCESS_TOKEN"]
    r = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
    ).json()
    if "access_token" not in r:
        print("Refresh failed:", r, file=sys.stderr)
        sys.exit(1)
    print(f"Refreshed; expires_in={r.get('expires_in')}s", file=sys.stderr)
    print(r["access_token"])  # the one line the workflow captures


if __name__ == "__main__":
    main()

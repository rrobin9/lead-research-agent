"""Smoke test for GNews API.

Queries GNews /search for Stripe press coverage in the last 30 days
(sorted by publish date, English, max 10 articles) and saves the full raw
response to sample_data/raw/stripe_gnews.json.

Docs: https://gnews.io/docs/v4
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


GNEWS_URL = "https://gnews.io/api/v4/search"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "raw" / "stripe_gnews.json"


def main() -> None:
    load_dotenv()
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key or api_key == "your_gnews_api_key_here":
        print("Error: GNEWS_API_KEY is missing or still the placeholder value.", file=sys.stderr)
        print("Copy .env.example to .env and fill in a real GNews API key.", file=sys.stderr)
        sys.exit(1)

    from_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "q": "Stripe",
        "lang": "en",
        "max": 10,
        "sortby": "publishedAt",
        "from": from_date,
        "apikey": api_key,
    }

    try:
        resp = requests.get(GNEWS_URL, params=params, timeout=30)
    except requests.RequestException as exc:
        print(f"Error: GNews request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if not resp.ok:
        print(f"Error: GNews returned {resp.status_code}", file=sys.stderr)
        print(f"Body: {resp.text[:1000]}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    print(json.dumps(data, indent=2)[:4000])
    if len(json.dumps(data)) > 4000:
        print("... (truncated in terminal; full blob written to file)")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2))
    size = OUTPUT_PATH.stat().st_size
    print(f"\n✅ Saved {size} chars to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

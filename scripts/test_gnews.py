"""Smoke test for GNews API.

Queries GNews /search for the target company's press coverage in the last
30 days (sorted by publish date, English, max 10 articles) and saves the
full raw response to sample_data/raw/<slug>_gnews.json.

Docs: https://gnews.io/docs/v4

Usage:
  python scripts/test_gnews.py               # defaults to stripe.com
  python scripts/test_gnews.py gong.io
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


GNEWS_URL = "https://gnews.io/api/v4/search"
RAW_DIR = Path(__file__).resolve().parent.parent / "sample_data" / "raw"


def main() -> None:
    domain = sys.argv[1] if len(sys.argv) > 1 else "stripe.com"
    slug = domain.split(".")[0]
    company_name = slug.capitalize()
    output_path = RAW_DIR / f"{slug}_gnews.json"

    load_dotenv()
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key or api_key == "your_gnews_api_key_here":
        print("Error: GNEWS_API_KEY is missing or still the placeholder value.", file=sys.stderr)
        print("Copy .env.example to .env and fill in a real GNews API key.", file=sys.stderr)
        sys.exit(1)

    from_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = {
        "q": company_name,
        "lang": "en",
        "max": 10,
        "sortby": "publishedAt",
        "from": from_date,
        "apikey": api_key,
    }

    print(f"Querying GNews: q={company_name!r}, from={from_date}")

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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2))
    size = output_path.stat().st_size
    print(f"\n✅ Saved {size} chars to {output_path}")


if __name__ == "__main__":
    main()

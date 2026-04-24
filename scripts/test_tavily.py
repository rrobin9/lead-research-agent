"""Smoke test for Tavily web search.

Runs a single advanced Tavily search for recent Stripe signals (funding,
hiring, news) and saves the full raw response to
sample_data/raw/stripe_tavily.json so we can inspect the shape before
wiring Tavily into the n8n workflow.
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


TAVILY_URL = "https://api.tavily.com/search"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "raw" / "stripe_tavily.json"


def main() -> None:
    load_dotenv()
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key or api_key.startswith("tvly-..."):
        print("Error: TAVILY_API_KEY is missing or still the placeholder value.", file=sys.stderr)
        print("Copy .env.example to .env and fill in a real Tavily API key.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "api_key": api_key,
        "query": "Stripe recent funding hiring news 2025",
        "search_depth": "advanced",
        "max_results": 10,
    }

    try:
        resp = requests.post(TAVILY_URL, json=payload, timeout=60)
    except requests.RequestException as exc:
        print(f"Error: Tavily request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if not resp.ok:
        print(f"Error: Tavily returned {resp.status_code}", file=sys.stderr)
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

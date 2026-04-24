"""Smoke test for Firecrawl company-homepage scraping.

Scrapes `https://<domain>` via Firecrawl /scrape (markdown format) and saves
the response to sample_data/raw/<slug>_firecrawl.json.

LinkedIn scraping was dropped from this fixture after the Stripe validation
run — Firecrawl returns 403 on LinkedIn company and people-search pages
under their current policy, so there's no point hitting it. Decision-maker
extraction happens downstream from Tavily results in the agent.

Usage:
  python scripts/test_firecrawl.py               # defaults to stripe.com
  python scripts/test_firecrawl.py gong.io
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"
RAW_DIR = Path(__file__).resolve().parent.parent / "sample_data" / "raw"


def scrape(url: str, api_key: str) -> dict:
    try:
        resp = requests.post(
            FIRECRAWL_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"url": url, "formats": ["markdown"]},
            timeout=60,
        )
    except requests.RequestException as exc:
        print(f"  ! Request failed for {url}: {exc}", file=sys.stderr)
        return {"error": "request_failed", "detail": str(exc), "url": url}

    if not resp.ok:
        print(f"  ! {resp.status_code} from Firecrawl for {url}", file=sys.stderr)
        print(f"    body: {resp.text[:500]}", file=sys.stderr)
        return {"error": "http_error", "status": resp.status_code, "body": resp.text, "url": url}

    return resp.json()


def main() -> None:
    domain = sys.argv[1] if len(sys.argv) > 1 else "stripe.com"
    slug = domain.split(".")[0]
    homepage_url = f"https://{domain}"
    output_path = RAW_DIR / f"{slug}_firecrawl.json"

    load_dotenv()
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key or api_key.startswith("fc-..."):
        print("Error: FIRECRAWL_API_KEY is missing or still the placeholder value.", file=sys.stderr)
        print("Copy .env.example to .env and fill in a real Firecrawl API key.", file=sys.stderr)
        sys.exit(1)

    print(f"Scraping homepage: {homepage_url}")
    combined = {"homepage": scrape(homepage_url, api_key)}

    print("\n--- Combined response ---")
    print(json.dumps(combined, indent=2)[:4000])
    if len(json.dumps(combined)) > 4000:
        print("... (truncated in terminal; full blob written to file)")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(combined, indent=2))
    size = output_path.stat().st_size
    print(f"\n✅ Saved {size} chars to {output_path}")


if __name__ == "__main__":
    main()

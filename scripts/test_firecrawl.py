"""Smoke test for Firecrawl company enrichment.

Runs three Firecrawl /scrape calls against Stripe as a known-good target:
  (a) company homepage
  (b) LinkedIn company page
  (c) LinkedIn people search (surfacing decision-maker names/titles)

Combines all three responses into a single JSON blob and saves it to
sample_data/raw/stripe_firecrawl.json for shape inspection.

LinkedIn pages frequently return a login wall — the script does NOT abort
when a single call fails; it records the error in the output slot and
continues, so you can see what Firecrawl can and can't pull in practice.
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "raw" / "stripe_firecrawl.json"

TARGETS = {
    "homepage": "https://stripe.com",
    "linkedin_company": "https://www.linkedin.com/company/stripe",
    "linkedin_people": "https://www.linkedin.com/search/results/people/?keywords=stripe%20vp%20sales",
}


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
    load_dotenv()
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key or api_key.startswith("fc-..."):
        print("Error: FIRECRAWL_API_KEY is missing or still the placeholder value.", file=sys.stderr)
        print("Copy .env.example to .env and fill in a real Firecrawl API key.", file=sys.stderr)
        sys.exit(1)

    combined: dict[str, dict] = {}
    for label, url in TARGETS.items():
        print(f"Scraping {label}: {url}")
        combined[label] = scrape(url, api_key)

    print("\n--- Combined response ---")
    print(json.dumps(combined, indent=2)[:4000])
    if len(json.dumps(combined)) > 4000:
        print("... (truncated in terminal; full blob written to file)")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(combined, indent=2))
    size = OUTPUT_PATH.stat().st_size
    print(f"\n✅ Saved {size} chars to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

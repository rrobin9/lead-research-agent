"""Local end-to-end prototype of the lead research agent pipeline.

Loads raw API snapshots from sample_data/raw/ (Firecrawl homepage, Tavily
web results, GNews articles), runs two sequential Claude Sonnet 4.5 calls:
  Call 1 — prompts/01_research_synthesis.md as system prompt → structured briefing
  Call 2 — prompts/02_scoring_and_hook.md as system prompt → scored dossier

Prints a formatted summary to the terminal, saves the full briefing +
dossier + metadata to sample_data/outputs/stripe_dossier.json, and logs
token usage and cost.

This is the reference implementation we'll translate into an n8n workflow.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv


# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------

COMPANY_DOMAIN = "stripe.com"

MODEL = "claude-sonnet-4-5"

# Pricing in USD per 1M tokens (Claude Sonnet 4.5, per user spec)
INPUT_COST_PER_MTOK = 3.00
OUTPUT_COST_PER_MTOK = 15.00

HOMEPAGE_TRUNCATE_CHARS = 3000

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "sample_data" / "raw"
OUT_DIR = REPO_ROOT / "sample_data" / "outputs"
PROMPTS_DIR = REPO_ROOT / "prompts"

FIRECRAWL_PATH = RAW_DIR / "stripe_firecrawl.json"
TAVILY_PATH = RAW_DIR / "stripe_tavily.json"
GNEWS_PATH = RAW_DIR / "stripe_gnews.json"

PROMPT_01_PATH = PROMPTS_DIR / "01_research_synthesis.md"
PROMPT_02_PATH = PROMPTS_DIR / "02_scoring_and_hook.md"

OUTPUT_PATH = OUT_DIR / "stripe_dossier.json"

WIDTH = 64


# ----------------------------------------------------------------------
# File loaders
# ----------------------------------------------------------------------

def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"Error: missing required file: {path}", file=sys.stderr)
        print("Run the test_*.py scripts first to generate the sample data.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"Error: {path} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)


def load_text(path: Path) -> str:
    if not path.exists():
        print(f"Error: missing required prompt file: {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text()


# ----------------------------------------------------------------------
# Research context assembly
# ----------------------------------------------------------------------

def extract_homepage_markdown(firecrawl: dict) -> str:
    homepage = firecrawl.get("homepage") or {}
    if not homepage.get("success"):
        return "[Firecrawl homepage scrape did not return success=true. No homepage content available.]"
    markdown = (homepage.get("data") or {}).get("markdown") or ""
    if not markdown:
        return "[Firecrawl homepage returned success but no markdown content.]"
    if len(markdown) > HOMEPAGE_TRUNCATE_CHARS:
        markdown = markdown[:HOMEPAGE_TRUNCATE_CHARS] + "\n\n[...truncated for length...]"
    return markdown


def format_tavily(tavily: dict) -> str:
    results = tavily.get("results") or []
    if not results:
        return "[No Tavily results.]"
    blocks = []
    for r in results:
        blocks.append(
            f"Title: {r.get('title', '(no title)')}\n"
            f"URL: {r.get('url', '')}\n"
            f"Content: {r.get('content', '')}"
        )
    return "\n\n".join(blocks)


def format_gnews(gnews: dict) -> str:
    articles = gnews.get("articles") or []
    if not articles:
        return "[No GNews articles.]"
    blocks = []
    for a in articles:
        source_name = (a.get("source") or {}).get("name", "")
        blocks.append(
            f"Title: {a.get('title', '(no title)')}\n"
            f"Published: {a.get('publishedAt', '')}\n"
            f"Source: {source_name}\n"
            f"Description: {a.get('description', '')}"
        )
    return "\n\n".join(blocks)


def assemble_research_context(firecrawl: dict, tavily: dict, gnews: dict, domain: str) -> str:
    return (
        f"You are researching the company with domain: {domain}\n\n"
        f"Here is the raw intelligence gathered from three sources. "
        f"Synthesize this into a structured briefing per your schema.\n\n"
        f"=== SOURCE 1: Company homepage (via Firecrawl) ===\n"
        f"{extract_homepage_markdown(firecrawl)}\n\n"
        f"=== SOURCE 2: Web research (via Tavily) ===\n"
        f"{format_tavily(tavily)}\n\n"
        f"=== SOURCE 3: Recent news (via GNews) ===\n"
        f"{format_gnews(gnews)}\n\n"
        f"Return the briefing as JSON per your schema. Start with {{ and end with }}."
    )


# ----------------------------------------------------------------------
# Claude call + JSON parsing
# ----------------------------------------------------------------------

def strip_and_parse_json(text: str) -> dict:
    """Extract a JSON object from a Claude response, tolerant of markdown fences and preamble."""
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last < first:
        raise ValueError("No JSON object delimiters found in response")
    return json.loads(text[first:last + 1])


def call_claude(
    client: Anthropic,
    system_prompt: str,
    user_message: str,
    temperature: float,
    max_tokens: int,
    label: str,
) -> tuple[dict, dict]:
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.APIError as exc:
        print(f"Error: Anthropic API error during {label}: {exc}", file=sys.stderr)
        sys.exit(1)

    raw_text = response.content[0].text
    usage = {
        "input": response.usage.input_tokens,
        "output": response.usage.output_tokens,
    }
    try:
        parsed = strip_and_parse_json(raw_text)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"\nFailed to parse JSON from Claude ({label}):", file=sys.stderr)
        print(f"  Error: {exc}", file=sys.stderr)
        print(f"\n--- Raw response ---\n{raw_text}\n--- end raw ---", file=sys.stderr)
        sys.exit(1)
    return parsed, usage


# ----------------------------------------------------------------------
# Summary printer
# ----------------------------------------------------------------------

def resolve_company_name(briefing: dict, domain: str) -> str:
    return briefing.get("company_name") or domain.split(".")[0].title()


def resolve_size(briefing: dict) -> str:
    employee_range = briefing.get("employee_range")
    employee_count = briefing.get("employee_count")
    if employee_range:
        return str(employee_range)
    if employee_count:
        return f"{employee_count:,} employees"
    return "Unknown"


def print_summary(
    briefing: dict,
    dossier: dict,
    usage_1: dict,
    usage_2: dict,
    runtime_s: float,
    domain: str,
) -> None:
    company_name = resolve_company_name(briefing, domain)

    print("=" * WIDTH)
    print("  LEAD RESEARCH AGENT — DOSSIER")
    print("=" * WIDTH)
    print()
    print(f"Company: {company_name} ({domain})")
    print(f"Industry: {briefing.get('industry', 'Unknown')}")
    print(f"Size: {resolve_size(briefing)}")
    confidence = briefing.get("confidence_score")
    if confidence is not None:
        print(f"Confidence: {confidence}/100")
    else:
        print("Confidence: —")
    print()

    # ---- SCORING ----
    print("-" * WIDTH)
    print("  SCORING")
    print("-" * WIDTH)
    print()

    disqualified = bool(dossier.get("disqualified"))
    fit_score = dossier.get("fit_score", "—")
    tier = dossier.get("tier", "—")
    rec = dossier.get("recommended_action", "—")

    print(f"Fit Score:  {fit_score}/100   →   Tier {tier}")
    print(f"Recommended action: {rec}")
    print()
    print("Reasoning:")
    print(f"  {dossier.get('tier_reasoning', '—')}")
    print()

    matches = dossier.get("icp_matches") or []
    gaps = dossier.get("icp_gaps") or []
    if matches:
        print("ICP matches:")
        for m in matches:
            print(f"  • {m}")
        print()
    if gaps:
        print("ICP gaps:")
        for g in gaps:
            print(f"  • {g}")
        print()

    # ---- HOOK (or disqualifier notice) ----
    print("-" * WIDTH)
    if disqualified:
        print("  DISQUALIFIED")
        print("-" * WIDTH)
        print()
        print(f"Reason: {dossier.get('disqualifier_reason', '—')}")
        print()
        print("No personalization hook generated — lead filtered out.")
        print()
    else:
        print("  PERSONALIZATION HOOK")
        print("-" * WIDTH)
        print()
        hook = dossier.get("personalization_hook")
        if hook is None:
            print("  (No personalization hook — likely no strong signals in briefing.)")
            print()
        else:
            print("Opening line:")
            print(f'  "{hook.get("opening_line", "")}"')
            print()
            print(f"Angle: {hook.get('angle', '')}")
            print(f"Avoid: {hook.get('avoid', '')}")
            print()

        contact = dossier.get("suggested_contact")
        if contact:
            print(f"Suggested contact: {contact.get('name', '')}, {contact.get('title', '')}")
            print(f"  Why: {contact.get('why_them', '')}")
            print()

        print(f"Best channel: {dossier.get('best_channel', '—')}")
        print()

    # ---- METADATA ----
    print("-" * WIDTH)
    print("  METADATA")
    print("-" * WIDTH)
    print()
    cost_1 = (usage_1["input"] * INPUT_COST_PER_MTOK + usage_1["output"] * OUTPUT_COST_PER_MTOK) / 1_000_000
    cost_2 = (usage_2["input"] * INPUT_COST_PER_MTOK + usage_2["output"] * OUTPUT_COST_PER_MTOK) / 1_000_000
    total_cost = cost_1 + cost_2

    print(f"Call 1 (synthesis):   {usage_1['input']:>6,} in  /  {usage_1['output']:>6,} out  tokens")
    print(f"Call 2 (scoring):     {usage_2['input']:>6,} in  /  {usage_2['output']:>6,} out  tokens")
    print(f"Total cost:           ${total_cost:.4f}")
    print(f"Runtime:              {runtime_s:.1f}s")
    print()
    print(f"Full dossier saved to: {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> None:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key.startswith("sk-ant-..."):
        print("Error: ANTHROPIC_API_KEY is missing or still the placeholder value.", file=sys.stderr)
        print("Copy .env.example to .env and fill in a real Anthropic API key.", file=sys.stderr)
        sys.exit(1)

    firecrawl = load_json(FIRECRAWL_PATH)
    tavily = load_json(TAVILY_PATH)
    gnews = load_json(GNEWS_PATH)

    prompt_01 = load_text(PROMPT_01_PATH)
    prompt_02 = load_text(PROMPT_02_PATH)

    research_context = assemble_research_context(firecrawl, tavily, gnews, COMPANY_DOMAIN)

    client = Anthropic(api_key=api_key)
    start = time.perf_counter()

    print(f"Call 1: Synthesizing research briefing for {COMPANY_DOMAIN}...")
    briefing, usage_1 = call_claude(
        client,
        system_prompt=prompt_01,
        user_message=research_context,
        temperature=0.3,
        max_tokens=2000,
        label="synthesis",
    )
    print(f"  → {usage_1['input']:,} in / {usage_1['output']:,} out tokens")

    company_name = resolve_company_name(briefing, COMPANY_DOMAIN)
    call_2_user_message = (
        f"Here is the research briefing for {company_name}:\n\n"
        f"{json.dumps(briefing, indent=2)}\n\n"
        f"Score this company against the ICP and generate a personalization hook "
        f"per your schema. Start with {{ and end with }}."
    )

    print(f"Call 2: Scoring ICP fit + writing hook...")
    dossier, usage_2 = call_claude(
        client,
        system_prompt=prompt_02,
        user_message=call_2_user_message,
        temperature=0,
        max_tokens=1500,
        label="scoring",
    )
    print(f"  → {usage_2['input']:,} in / {usage_2['output']:,} out tokens")

    runtime_s = time.perf_counter() - start

    cost_1 = (usage_1["input"] * INPUT_COST_PER_MTOK + usage_1["output"] * OUTPUT_COST_PER_MTOK) / 1_000_000
    cost_2 = (usage_2["input"] * INPUT_COST_PER_MTOK + usage_2["output"] * OUTPUT_COST_PER_MTOK) / 1_000_000

    output = {
        "company_domain": COMPANY_DOMAIN,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "briefing": briefing,
        "dossier": dossier,
        "metadata": {
            "model": MODEL,
            "call_1_tokens": usage_1,
            "call_2_tokens": usage_2,
            "total_cost_usd": round(cost_1 + cost_2, 4),
            "runtime_seconds": round(runtime_s, 2),
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2))

    print()
    print_summary(briefing, dossier, usage_1, usage_2, runtime_s, COMPANY_DOMAIN)


if __name__ == "__main__":
    main()

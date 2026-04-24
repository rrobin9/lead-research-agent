# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An automated B2B lead research pipeline orchestrated by **n8n** that enriches company leads with data from Apollo, Tavily, Firecrawl, and NewsAPI — then uses Claude to synthesize a research brief, score ICP fit, and draft personalized outreach hooks. Output goes to Google Sheets and Slack.

There is no Python application to run directly. The pipeline runs inside n8n; Python scripts in `scripts/` are utilities only. Claude prompts are templates with `{{variable}}` placeholders injected by n8n nodes.

## Setup

```bash
cp .env.example .env
# Fill in all API keys
pip install -r requirements.txt
```

Import `n8n/workflow.json` into your n8n instance and configure credentials using keys from `.env`.

## Pipeline Flow

```
Google Sheet (new row) 
  → Apollo enrichment (firmographics, contacts)
  → Tavily web search (recent signals)
  → Firecrawl scrape (homepage + /about)
  → NewsAPI (last 30 days)
  → Claude: prompts/01_research_synthesis.md (structured brief)
  → Claude: prompts/02_scoring_and_hook.md (ICP score 0–100 + 3 outreach hooks)
  → Google Sheet (append output) + Slack (post summary)
```

## Prompt Architecture

The two Claude prompts are chained: output of `01_research_synthesis.md` becomes `{{research_brief}}` input to `02_scoring_and_hook.md`.

**Prompt 01** takes: `{{apollo_data}}`, `{{tavily_results}}`, `{{firecrawl_content}}`, `{{news_articles}}` → outputs a structured 6-section research brief.

**Prompt 02** takes: `{{research_brief}}` + `{{icp_definition}}` → outputs ICP score, disqualifiers, 3 outreach hooks (trigger/positioning/problem-based), and recommended next step.

## Key Design Rules

- Every API is treated as **optional** — the pipeline must produce output even if 2 of 5 data sources fail. See `prompts/failure_modes.md` for per-service mitigations.
- Never fail silently — every error path must write a status to the Google Sheet row.
- Firecrawl content is the first to trim if context is too long (cap at 2000 chars).
- Validate Claude output: score must be a numeric 0–100, all 3 hooks must be present — re-prompt once if not.
- Apollo: retry on 429 with 5s backoff (max 3 retries); pass empty object on 404.
- Cache Apollo results — don't re-enrich the same domain within 30 days.

## Cost Optimization

- Use **Claude Haiku** for synthesis (prompt 01), **Sonnet** for hook writing (prompt 02).
- Firecrawl: scrape homepage only unless it yields <500 chars (login wall).
- See `docs/cost-analysis.md` for full per-service cost breakdown template.

## Testing

See `prompts/test_cases.md` for the validation checklist and 4 test case archetypes (strong fit, weak fit, edge case, data-poor company). Run end-to-end against these before processing real leads. Raw API responses during testing should be saved to `sample_data/raw/`.

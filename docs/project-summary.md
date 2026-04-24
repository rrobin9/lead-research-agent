# Project Summary

## Root

| File | Purpose |
|------|---------|
| `README.md` | Project overview, stack, setup instructions, folder map |
| `CLAUDE.md` | Guidance for Claude Code when working in this repo |
| `.env.example` | API key template (Anthropic, Apollo, Tavily, Firecrawl, NewsAPI, Slack, Google Sheets) |
| `requirements.txt` | 3 Python deps: `anthropic`, `python-dotenv`, `requests` |

## prompts/

The core Claude prompt templates that power the pipeline.

| File | Purpose |
|------|---------|
| `01_research_synthesis.md` | Takes raw API data, outputs a structured 6-section research brief |
| `02_scoring_and_hook.md` | Takes the brief + ICP definition, outputs ICP score + 3 outreach hooks |
| `failure_modes.md` | Per-service failure mitigations and workflow design rules |
| `test_cases.md` | 4 test archetypes + end-to-end validation checklist |

## docs/

| File | Purpose |
|------|---------|
| `cost-analysis.md` | Per-service cost breakdown table + volume projections (template, not yet filled in) |
| `project-summary.md` | This file |

## demo/

| File | Purpose |
|------|---------|
| `loom-link.md` | Placeholder for walkthrough video link |

## Empty Directories (placeholders for future content)

| Directory | Intended content |
|-----------|-----------------|
| `n8n/` | Exported n8n workflow JSON |
| `scripts/` | Utility Python scripts |
| `sample_data/raw/` | Raw API responses saved during development/debugging |
| `sample_data/outputs/` | Final enriched lead outputs |

---

> The project is a well-structured skeleton — the prompts and documentation are in place, but the n8n workflow, Python scripts, and sample data have not been added yet.

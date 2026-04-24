# AI-Powered B2B Lead Research Agent

An automated pipeline that enriches B2B leads with deep research using n8n, Claude, Tavily, Firecrawl, and GNews — then scores them and drafts personalized outreach hooks.

## Stack

| Tool | Role |
|------|------|
| **n8n** | Workflow orchestration |
| **Claude (Anthropic)** | Research synthesis + hook writing |
| **Tavily** | Web search for recent company signals |
| **Firecrawl** | Company enrichment: homepage + LinkedIn company page + LinkedIn people search |
| **GNews API** | Recent news mentions (true free tier, 100 req/day) |
| **Google Sheets** | Input/output data store |
| **Slack** | Delivery of scored leads + hooks |

## How It Works

1. Trigger: New row added to Google Sheet with company name + domain
2. Firecrawl enrichment: scrape company homepage, LinkedIn company page, and LinkedIn people search for contacts
3. Tavily search: recent company signals (hiring, product launches, expansions)
4. Firecrawl: deep scrape of homepage + /about for positioning language
5. GNews API: last 30 days of press coverage
6. Claude synthesis: combine all signals into a structured research brief
7. Claude scoring: ICP fit score (0–100) + confidence level
8. Claude hook: 2–3 personalized outreach angles
9. Output: append to Google Sheet + post summary to Slack

## Folder Structure

```
lead-research-agent/
├── docs/               # Cost analysis, architecture notes
├── prompts/            # Claude prompt templates
├── scripts/            # Utility Python scripts
├── n8n/                # Exported n8n workflow JSON
├── sample_data/
│   ├── raw/            # Raw API responses (for testing)
│   └── outputs/        # Final enriched lead outputs
└── demo/               # Loom link, screenshots
```

## Setup

### Prerequisites
- n8n (self-hosted or cloud)
- Python 3.10+
- API keys for all services (see `.env.example`)

### Installation

```bash
git clone <repo-url>
cd lead-research-agent
cp .env.example .env
# Fill in your API keys in .env
pip install -r requirements.txt
```

### n8n Workflow

Import `n8n/workflow.json` into your n8n instance. Configure credentials for each service using the keys from your `.env`.

## Prompts

See `prompts/` for the Claude prompt templates:
- `01_research_synthesis.md` — combines raw signals into a structured brief
- `02_scoring_and_hook.md` — scores ICP fit and writes outreach hooks

## Cost Analysis

See `docs/cost-analysis.md` for estimated per-lead API costs across all services.

## Demo

See `demo/loom-link.md` for walkthrough video.

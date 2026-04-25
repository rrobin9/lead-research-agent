# AI-Powered B2B Lead Research Agent

Drop in a company domain, get back a qualified lead dossier in ~25 seconds for ~$0.05. Built with Claude Sonnet 4.5 and three free-tier APIs (Firecrawl, Tavily, GNews). The agent reads what's publicly true about a company, scores it against a defined ICP, and either drafts a personalized outreach hook or refuses with a specific reason.

## What it does

```
$ python3 scripts/test_agent_local.py linear.app

  → Fetches Linear's homepage (Firecrawl), recent web signals (Tavily),
    and last-30-days press coverage (GNews)
  → Synthesizes a structured briefing (Claude Sonnet 4.5, temp 0.3)
  → Scores the briefing against the ICP and writes a hook (Sonnet 4.5, temp 0)
  → Saves the dossier as JSON, prints a formatted summary

  Tier:               B (fit_score 68/100)
  Recommended action: outreach_now
  Hook example:       "$50M Series D in October and 21 open roles means
                       you're scaling fast — at 18K customers, how are you
                       thinking about enterprise motion?"
```

*(Linear sits at the Tier B↔C boundary — about 1 in 4 runs lands at Tier B with a hook like the one above; the other 3 land at Tier C with the agent declining to write a hook. See "Validation" below for why this is intentional.)*

The output is opinionated: the agent will refuse to write a hook for a clearly bad lead rather than produce generic flattery.

## Architecture

The pipeline runs as a Python prototype that's intentionally portable to n8n later — each step is a discrete, single-purpose tool call:

```
domain
  ↓
Firecrawl /scrape   (homepage markdown, truncated to 3,000 chars)
Tavily /search      (10 results, "advanced" depth)
GNews /search       (10 articles, last 30 days)
  ↓
Claude Sonnet 4.5 — Call 1 (research synthesis, temperature 0.3)
  → structured briefing JSON
  ↓
Claude Sonnet 4.5 — Call 2 (ICP scoring + hook, temperature 0)
  → scored dossier JSON + personalization hook
  ↓
sample_data/outputs/<slug>_dossier.json
```

| Layer | Tool | Why |
|---|---|---|
| Web scraping | **Firecrawl** | Homepage markdown extraction. LinkedIn was attempted; LinkedIn's anti-scraping policy returns 403 — that path was removed. |
| Web search | **Tavily** | Deep, broad research snippets — best for firmographics + funding history. |
| Recent news | **GNews API** | True free tier (100 req/day), tight 30-day window — best for "what happened this week." |
| Synthesis + scoring | **Claude Sonnet 4.5** | Two-call pipeline: research-analyst persona, then sales-strategist persona. |

Planned (not yet built): an n8n workflow wrapping the same pipeline with Google Sheets input and Slack delivery.

## How to run it

```bash
git clone <repo-url> && cd lead-research-agent
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, FIRECRAWL_API_KEY, TAVILY_API_KEY, GNEWS_API_KEY
pip install -r requirements.txt

# Generate raw fixtures for a target
python3 scripts/test_firecrawl.py linear.app
python3 scripts/test_tavily.py    linear.app
python3 scripts/test_gnews.py     linear.app

# Run the agent
python3 scripts/test_agent_local.py linear.app
```

All four scripts default to `stripe.com` if no domain is passed. Output JSONs land in `sample_data/raw/<slug>_*.json` and `sample_data/outputs/<slug>_dossier.json`.

## Validation

The pipeline has been run end-to-end against five targets, each picked to stress a different part of the ICP scoring logic:

| Target | Verdict | What this revealed |
|---|---|---|
| **stripe.com** | DISQUALIFIED — fintech | The "not a software company" disqualifier needed explicit fintech language to fire deterministically (was inconsistent on first runs). |
| **gong.io** | DISQUALIFIED — competitor | Confirms the named-peer-set disqualifier still fires on a true competitor after tightening the language. |
| **monday.com** | Tier C — nurture | Confidence dropped to 45/100 because the word "Monday" produced noisy Tavily/GNews fixtures (state-holiday articles, etc.). Surfaces the need for query-quoting in production. |
| **linear.app** | Tier B↔C — borderline | PLG company with strong funding/hiring signals. Tier drifts B↔C across runs at temperature=0; documented as model variance on borderline cases. |
| **okta.com** | DISQUALIFIED — boundary case | Claude misread "B2B SaaS for sales/RevOps" as "must sell sales/RevOps tools" rather than "any B2B SaaS prospect." A real ICP-language ambiguity, not a model error. |

The bigger story: the agent has *opinions*. It refused 3 of 5 leads for distinct, specific reasons, and produced a real hook for the one borderline candidate. Triage is the value, not yes-on-everything pattern matching.

## Cost & performance

Per-lead numbers from `sample_data/outputs/`:

| Metric | Value |
|---|---|
| Total cost | **$0.044 – $0.057** (median ≈ $0.053) |
| Runtime | **20–36 seconds** end-to-end |
| Tokens | ~8k input + 900 output (synthesis); ~3k input + 400 output (scoring) |

Anthropic API spend dominates. The three enrichment services (Firecrawl, Tavily, GNews) all have free tiers that cover well over 100 leads/month at this volume. At ~$5 per 100 leads, the dominant cost in real use would be a sales rep's time reading the dossiers.

## What's next

- **n8n workflow** wrapping the same Python pipeline
- **Google Sheets trigger** for batch input and dossier write-back
- **Slack webhook** for delivery + tier-based routing
- **Cost dashboard** in `docs/cost-analysis.md` filled in with real-run numbers

## What I'd do for production

The 5-target validation surfaced four real limitations worth flagging before real leads see this:

- **ICP language ambiguity** (Okta case) — *"A Sales/RevOps platform for B2B SaaS companies"* parses two ways. Production prompt should explicitly disambiguate that the prospect's product category isn't the gating factor.
- **Common-name search noise** (monday.com case) — for short or generic names, the Tavily/GNews queries should quote the domain or include a category disambiguator (`"monday.com" software`, not bare `Monday`).
- **Borderline-case variance** (Linear case) — `temperature=0` doesn't strictly determinize Claude on edge calls. Production should run the scoring call 3× and majority-vote the tier, or expose per-dimension sub-scores so a downstream system can re-bucket consistently.
- **LinkedIn anti-scraping** (architectural) — Firecrawl is policy-blocked at 403 on LinkedIn under their current rules. Decision-maker extraction had to pivot from "scrape /people/" to "extract names from Tavily snippets," which is lower-recall. A real production pipeline would integrate a LinkedIn-licensed source (Apollo, Lusha, ZoomInfo) or pull contacts from an existing sales engagement tool.

Each of these is a prompt/query/orchestration change, not an architecture rewrite — they're addressable independently.

---

**Repo layout:** `prompts/` for the two Claude system prompts · `scripts/` for the four CLI tools · `sample_data/raw/` for committed API fixtures · `sample_data/outputs/` for committed dossiers · [docs/project-summary.md](docs/project-summary.md) for the deeper internal write-up.

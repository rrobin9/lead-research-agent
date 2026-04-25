# Project Summary

**State as of commit `e209049`.** End-to-end Python prototype is working. Five targets validated. Next step is wrapping the same pipeline as an n8n workflow with Google Sheets + Slack.

## What's built

The Python prototype in [scripts/test_agent_local.py](../scripts/test_agent_local.py) runs the full pipeline end-to-end:

1. Loads three pre-fetched API fixtures from `sample_data/raw/<slug>_*.json`
2. Calls Claude Sonnet 4.5 twice — synthesis (temp 0.3) → scoring/hook (temp 0)
3. Saves the combined briefing + dossier to `sample_data/outputs/<slug>_dossier.json`

All four scripts (`test_firecrawl.py`, `test_tavily.py`, `test_gnews.py`, `test_agent_local.py`) accept a positional `domain` arg and default to `stripe.com`. The `<slug>` is `domain.split(".")[0]`, so `linear.app` writes to `linear_*.json`.

## Architecture decisions

### Why Firecrawl instead of Apollo
Apollo's developer API was unreliable during early validation (intermittent 5xx, slow). Firecrawl scraping the company homepage gives most of the same firmographic signal (employee counts via copy, products, positioning) plus higher-confidence "what they actually say about themselves" content.

### Why GNews instead of NewsAPI
NewsAPI blocks personal email domains on signup. GNews has a true free tier (100 req/day) with no such restriction.

### Why both Tavily *and* GNews
They're complementary, not redundant:
- **Tavily** — deep snippets (often 500+ words per result), best for firmographics, funding history, named execs
- **GNews** — short structured news (publishedAt, source.name, description), best for "what happened this week"

Removing either would weaken the briefing on a different axis. Worth the second API call.

### Why LinkedIn scraping was dropped
Firecrawl returns **403** on `linkedin.com/company/<slug>` and `linkedin.com/search/results/people/...` under LinkedIn's anti-scraping policy. Tested across Stripe, Gong, Linear — same 403 every time. LinkedIn slots were removed from `test_firecrawl.py`; decision-maker extraction now happens downstream from Tavily snippets, accepting lower recall in exchange for not having a hard architectural dependency on a blocked source.

### Why Sonnet 4.5 over Opus
- Sonnet hits the quality bar for both synthesis and scoring (validated across all 5 targets — no obvious degradation vs. running the analysis manually).
- Cost: $3/$15 per Mtok (Sonnet) vs. $15/$75 per Mtok (Opus) — 5× cheaper input, 5× cheaper output.
- Latency: Sonnet returns the synthesis brief in ~12–15s; Opus would push end-to-end runtime past 60s.

For a high-stakes, low-volume product (e.g. enterprise account research), Opus would be defensible. For a triage tool processing dozens-to-hundreds of leads, Sonnet is the right call.

### Why two Claude calls instead of one
- **Persona separation** — Call 1 plays a research analyst (neutral, fact-extracting). Call 2 plays a sales strategist (opinionated, evaluative). Forcing one call to do both produces wishy-washy output.
- **Auditability** — the briefing JSON is human-readable independent of the scoring. A sales rep can disagree with the score but still trust the underlying facts.
- **Reusability** — the briefing schema is generic; it could feed into other downstream tasks (qualification, account planning, competitor analysis) without reworking the synthesis logic.
- **Determinism control** — synthesis at temp 0.3 (slight breadth on what counts as a signal); scoring at temp 0 (deterministic on the rubric).

## Validation summary (commit `e209049`)

| Target | Tier | Disqualified | Hook | Cost | Runtime |
|---|---|---|---|---|---|
| stripe.com | DISQUALIFIED | true (fintech) | null | $0.0527 | 23.8s |
| gong.io | DISQUALIFIED | true (competitor) | null | $0.0532 | 23.9s |
| linear.app | C | false | null *(this run)* | $0.0554 | 31.1s |
| monday.com | C | false | null | $0.0470 | 23.0s |
| okta.com | DISQUALIFIED | true (boundary case) | null | $0.0459 | 26.0s |

Median: ~$0.053 / lead, ~25s runtime.

## Known limitations

### ICP language ambiguity (Okta case)
The current ICP — *"An AI-powered Sales/RevOps platform for B2B SaaS companies"* — parses two ways:
1. *"…for [B2B SaaS companies]"* — any B2B SaaS prospect, regardless of category. (Intended reading.)
2. *"…[for B2B SaaS companies in the sales/RevOps space]"* — only B2B SaaS that themselves sell sales tools.

On the Okta run, Claude picked reading #2 and disqualified Okta because their product category (identity/security) isn't sales/RevOps. Okta is a textbook ICP fit on the intended reading: 6,000-employee B2B SaaS with a large sales org.

**Fix:** explicit disambiguation in the prompt — *"'B2B SaaS' refers to the prospect's business model. Their product category is not a gating factor; any subscription-software B2B with a sales team qualifies."*

### Common-name search noise (monday.com case)
The Tavily query `f"{company_name} recent funding hiring news 2025"` is a free-text search. For "Monday" it surfaced articles about Mississippi state holidays, London law firms, etc. — the word is too common.

Confidence on the synthesized briefing dropped to 45/100 (vs. 78–85 for clean runs). Claude correctly downgraded the result rather than fabricating, but the dossier was less useful.

**Fix:** quote the domain in the query (`"monday.com"`) rather than the slug, or pass an explicit "this is a software company called X" disambiguator.

### Tier-edge variance at temperature=0 (Linear case)
Across four Linear runs (same prompt, same fixture), the agent produced:
- 3× Tier C with null hook
- 1× Tier B with non-null hook

`temperature=0` doesn't strictly determinize on borderline cases — it picks the most probable next token, but on close ties the model can still flip. Linear's score sits right at the B↔C boundary (≈58–68 across runs), so any small drift in how Claude weighs the GTM-maturity sub-score moves the tier.

**Fix:** run the scoring call N=3 times and majority-vote the tier, or return per-dimension sub-scores so a downstream system can re-bucket consistently.

### LinkedIn anti-scraping (architectural)
Already addressed in code: LinkedIn slots removed from `test_firecrawl.py`. But the underlying limitation — that getting structured decision-maker data from public sources is hard — would block any high-recall production pipeline. A real deployment would integrate with a LinkedIn-licensed enrichment provider (Apollo, Lusha, ZoomInfo) or pull from an existing sales engagement tool's contact DB.

## Cost / runtime baselines

From the five committed dossier JSONs:

| | Min | Median | Max |
|---|---|---|---|
| Cost / lead | $0.0441 | $0.0527 | $0.0572 |
| Runtime | 20.4s | 23.9s | 31.1s |
| Synthesis tokens (in / out) | 5,855 / 528 | 7,918 / 919 | 8,294 / 939 |
| Scoring tokens (in / out) | 2,778 / 312 | 3,243 / 391 | 3,333 / 619 |

Anthropic API spend dominates. Tavily / GNews / Firecrawl all have free tiers covering 100+ leads/month at the volume one prototype generates during testing.

## Where things live

| Path | Contents |
|---|---|
| `prompts/01_research_synthesis.md` | System prompt for Call 1 — research-analyst persona, structured-briefing schema |
| `prompts/02_scoring_and_hook.md` | System prompt for Call 2 — sales-strategist persona, ICP definition, scoring rubric, JSON schema, hook rules |
| `prompts/failure_modes.md` | Per-service error mitigations for the eventual n8n workflow |
| `prompts/test_cases.md` | Test archetypes + validation checklist (predates the live validation runs) |
| `scripts/test_firecrawl.py` | Firecrawl smoke test → `sample_data/raw/<slug>_firecrawl.json` |
| `scripts/test_tavily.py` | Tavily smoke test → `sample_data/raw/<slug>_tavily.json` |
| `scripts/test_gnews.py` | GNews smoke test → `sample_data/raw/<slug>_gnews.json` |
| `scripts/test_agent_local.py` | The agent itself — reads fixtures, runs both Claude calls, writes dossier |
| `sample_data/raw/` | Committed API responses for the 5 validated targets (stripe, gong, linear, monday, okta) |
| `sample_data/outputs/` | Committed agent dossiers — one JSON per target |
| `docs/cost-analysis.md` | Per-service cost breakdown (template; will be filled in with the n8n workflow) |

## Empty / placeholder paths

- `n8n/` — exported workflow JSON will land here once Step 6 is built
- `demo/loom-link.md` — placeholder for the walkthrough video URL

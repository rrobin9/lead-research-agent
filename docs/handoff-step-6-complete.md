# Step 6 Complete — n8n Workflow Live

## Status
n8n workflow built, activated, and validated end-to-end on three live targets.

## Validated targets in n8n (live runs)
| Target | Tier | Score | Notes |
|---|---|---|---|
| linear.app | C | 60 | Correctly ID'd as PLG, no sales motion (matches Python prototype) |
| vercel.com | B | 73 | Caught $250M Series C trigger + April 2024 security breach context |
| emergent.sh | DISQUALIFIED | 0 | Correctly caught: dev tool platform, not B2B SaaS target |

## Architecture (13 nodes)
Sheets Trigger → Update Row (processing) → [Tavily ‖ Firecrawl ‖ GNews] → Merge → Synthesis (Sonnet 4.5 @ 0.3) → Scoring (Sonnet 4.5 @ 0) → Write Results to Sheet → Switch by Tier → [Slack A ‖ B ‖ C ‖ Disqualified]

## Known gaps (deferred to Step 7)
- No error handling — if any HTTP node fails, sheet stays at status=processing
- Slack webhook URL pasted inline in 4 nodes (export risk)
- GNews query strips TLD via `.split('.')[0]` — broadens search noise on common names
- No status=error fallback path

## Step 7 next steps
- Loom walkthrough (~4 min)
- Excalidraw architecture diagram
- Fill in docs/cost-analysis.md with real numbers from these 3 runs
- README polish
- Address known gaps above (optional, depending on time)

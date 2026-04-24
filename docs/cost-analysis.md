# Cost Analysis

Estimated per-lead API costs. Update as you test with real data.

## Per-Lead Cost Breakdown

| Service | Plan / Tier | Est. calls per lead | Est. cost per lead |
|---------|-------------|--------------------|--------------------|
| Apollo | — | 1 enrichment | — |
| Tavily | — | 1 search (10 results) | — |
| Firecrawl | — | 1–2 pages scraped | — |
| NewsAPI | — | 1 search | — |
| Claude (Anthropic) | — | 2 calls (~4k tokens input, ~1k output each) | — |
| **Total** | | | **~$X.XX / lead** |

## Notes

- Fill in pricing from each service's current pricing page
- Claude costs depend on which model you use (Haiku vs Sonnet vs Opus)
- Apollo pricing is per enrichment credit — check your plan's credit limit
- Tavily and Firecrawl have free tiers; track when you hit limits

## Volume Projections

| Leads/month | Est. monthly cost |
|-------------|-------------------|
| 100 | — |
| 500 | — |
| 1,000 | — |
| 5,000 | — |

## Cost Optimization Notes

- Use Claude Haiku for synthesis (fast, cheap) and Sonnet only for hook writing
- Cache Apollo results — don't re-enrich the same domain within 30 days
- Firecrawl: scrape homepage only unless homepage has no useful content

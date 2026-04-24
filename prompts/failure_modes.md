# Failure Modes & Mitigations

Known failure modes to handle in the n8n workflow and prompts.

## API Failures

| Service | Failure | Mitigation |
|---------|---------|------------|
| Apollo | 429 rate limit | Retry with 5s backoff; max 3 retries |
| Apollo | 404 (company not found) | Pass empty object; Claude prompt handles missing data |
| Tavily | No results | Pass empty array; Claude flags low-confidence |
| Firecrawl | Timeout / blocked | Pass empty string; note in brief |
| NewsAPI | No articles | Pass empty array (expected for small companies) |
| Google Sheets | Write fails | Log to n8n execution log; do not silently drop |
| Slack | Webhook fails | Log; do not block pipeline completion |

## Claude Prompt Failures

- **Truncation:** If input context is too long, Firecrawl content gets trimmed first (lowest signal density). Cap at 2000 chars.
- **Score not a number:** Add output validation node in n8n; re-prompt once if score missing.
- **Hook missing:** Validate all 3 hooks present; re-prompt if any are missing.
- **Hallucinated data:** Prompt instructs Claude to use only provided data. Flag if Claude cites a source not in inputs.

## Data Quality Issues

- **Wrong company matched by Apollo:** Validate domain matches before using firmographics.
- **Outdated news:** NewsAPI `from` param should always be `today - 30 days`. Hardcode this in the n8n HTTP node.
- **Website content is a login wall:** Firecrawl returns <500 chars → flag as "website not scrapeable" in brief.

## Workflow Design Rules

- Never fail silently — every error path should write a status to the Google Sheet row.
- Treat each API as optional: the pipeline should produce *something* even if 2 of 5 data sources fail.
- Log all raw API responses to `sample_data/raw/` during development for debugging.

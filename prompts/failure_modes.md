What to do when Claude returns bad output. Bake these into your n8n workflow.
Failure 1: Response isn't valid JSON
Symptoms: JSON.parse throws, response has ```json fences or preamble text
Fix in n8n:

Add a Code node after the Anthropic node that strips markdown fences before parsing
Use regex: response.replace(/^```json\s*/,'').replace(/```\s*$/,'').trim()
If still fails, retry the call once with max_tokens increased by 500

Failure 2: JSON is valid but schema is wrong
Symptoms: Missing required fields, wrong types (e.g. employee_count as string)
Fix in n8n:

Add a validation Code node using a lightweight schema check
On failure, retry with an appended message: "Your previous response was missing fields X, Y. Return the complete JSON matching the schema."

Failure 3: Model invents facts
Symptoms: The dossier mentions a funding round that wasn't in any source
Fix:

Add this line to the system prompt: "Every claim in recent_signals MUST be traceable to a specific source_hint. If you cannot trace it, omit it."
Spot-check 10% of outputs manually during your first week

Failure 4: Scoring drifts over time
Symptoms: Same company scored differently across runs
Fix:

Set temperature: 0 on the scoring call (but keep temperature: 0.3 on research synthesis — slightly more creative summaries are fine)
Pin the model version explicitly (don't use "latest")

Failure 5: Personalization hook is generic
Symptoms: "I noticed you're scaling fast" with no specifics
Fix:

The prompt already bans "I noticed" — if it sneaks through, add a post-check regex that triggers a retry
In the retry, append: "Your previous hook was too generic. Reference a specific fact from recent_signals by name, date, or number."

Failure 6: Hook references a competitor by name
Symptoms: "Saw you use HubSpot — we're better" (legally/tonally risky)
Fix:

Add to scoring prompt: "Never compare the prospect to a named competitor in the hook. Reference their situation, not their tooling."

Failure 7: Cost creep
Symptoms: Token usage per lead creeping above $0.10
Fix:

Truncate Firecrawl markdown to first 3,000 chars before including
Truncate Tavily results to top 5 with content under 500 chars each
Use claude-haiku-4-5 for research synthesis when inputs are already clean
Log usage.input_tokens and usage.output_tokens to your Sheets Results tab
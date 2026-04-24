Use these to validate the prompts behave consistently. Run each through both prompts and check the output matches expectations.

Test case 1 — Strong fit (expected: Tier A, score 80-95)
Company: Clay.com
Why it's a good test: Real company, B2B SaaS, ~200 employees, recent Series B, hiring aggressively, tech stack visible.
Expected output highlights:

tier: "A", fit_score: 85-95
recent_signals includes their Series B (Jan 2025) and hiring
personalization_hook.opening_line references either the funding or a specific feature launch
suggested_contact is a VP Sales or CRO

Test case 2 — Wrong size (expected: Tier C or D)
Company: A 15-person seed-stage startup you find on Product Hunt
Why it's a good test: Too small for ICP. Score should reflect this.
Expected output highlights:

tier: "C" or "D", fit_score: 20-50
icp_gaps includes "below employee threshold"
recommended_action: "monitor" or "disqualify"
Still produces valid JSON even with weak signals

Test case 3 — Wrong industry but big signals (expected: Tier C, thoughtful reasoning)
Company: A staffing agency that just raised a Series B
Why it's a good test: Checks whether the model respects the "no services businesses" disqualifier even when other signals scream "buyer."
Expected output highlights:

tier: "C", fit_score: 30-50
tier_reasoning explicitly calls out the industry mismatch
icp_gaps includes industry/business model

Test case 4 — Sparse data (expected: valid JSON, low confidence)
Company: A company where Apollo returns nothing and only the website scrape has data
Why it's a good test: Makes sure the prompts degrade gracefully when inputs are thin.
Expected output highlights:

Prompt 1: confidence_score: 30-50, most fields null, data_gaps populated
Prompt 2: may return personalization_hook: null, tier dropped a level

Test case 5 — Conflicting data (expected: handled, noted)
Company: Feed it raw inputs where Apollo says "200 employees" but LinkedIn scrape says "450 employees"
Why it's a good test: Validates the conflict-handling rule.
Expected output highlights:

Uses the more recent source
data_gaps mentions the employee count discrepancy
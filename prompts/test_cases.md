# Test Cases

Use these companies to validate the pipeline end-to-end before running on real leads.

## Test Case 1 — Strong ICP Fit
**Company:** 
**Domain:** 
**Expected score range:** 75–90
**What to verify:** 

## Test Case 2 — Weak ICP Fit
**Company:** 
**Domain:** 
**Expected score range:** 20–40
**What to verify:** 

## Test Case 3 — Edge Case / Ambiguous
**Company:** 
**Domain:** 
**Expected score range:** 45–60
**What to verify:** 

## Test Case 4 — Data-Poor Company (small/private)
**Company:** 
**Domain:** 
**Expected behavior:** Pipeline should complete without crashing; brief should flag low-confidence data sources

---

## Validation Checklist

For each test run:
- [ ] Apollo returns data (or gracefully handles 404)
- [ ] Tavily returns ≥3 results
- [ ] Firecrawl returns homepage content
- [ ] NewsAPI returns results (or empty array — not an error)
- [ ] Claude synthesis completes without truncation
- [ ] Score is a number 0–100
- [ ] All 3 hooks are present in output
- [ ] Google Sheet row is updated
- [ ] Slack message is posted

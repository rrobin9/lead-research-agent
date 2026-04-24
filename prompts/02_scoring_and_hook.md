# Prompt: ICP Scoring + Outreach Hook

<!--
  Input variables (injected by n8n):
  - {{research_brief}}  — output from prompt 01_research_synthesis
  - {{icp_definition}}  — paste your ICP criteria here or inject from a config node
-->

You are a senior B2B sales strategist. Using the research brief below, score this lead against our ICP and write personalized outreach hooks.

## ICP Definition
{{icp_definition}}

## Research Brief
{{research_brief}}

---

## Your Output

### ICP Score
- **Score:** X/100
- **Confidence:** High / Medium / Low
- **Scoring rationale:** 3–5 bullet points explaining the score. For each criterion in the ICP, state whether this company passes, fails, or is unknown.

### Disqualifiers (if any)
- List any hard disqualifiers that should pause outreach immediately.

### Outreach Hooks (write 3)

For each hook:
- **Angle:** what specific signal you're referencing
- **Opening line:** the first sentence of the email/LinkedIn message (personalized, not generic)
- **Why it works:** what pain or aspiration this angle speaks to

Hook 1 — [Trigger-based: reference a recent company event]
Hook 2 — [Positioning-based: reference their own language back to them]
Hook 3 — [Problem-based: name a pain common at their stage/size]

### Recommended Next Step
- Cold email / LinkedIn DM / warm intro / hold — and why.

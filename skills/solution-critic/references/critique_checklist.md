# Critique Checklist

A structured checklist for the `solution-critic` to work through before
producing scores. Each section maps to a failure mode or scoring dimension.

---

## Section A: Problem–Solution Alignment

- [ ] **Does the solution address the stated root cause?**
  (Not just the symptom described in the problem)
- [ ] **Is the scope of the solution proportional to the scope of the problem?**
  (Not a sledgehammer for a small nail; not a band-aid on a major wound)
- [ ] **Does the solution target the correct geographic area and affected population?**
- [ ] **Are all affected stakeholders considered** (not just the most visible group)?

---

## Section B: Implementation Realism

- [ ] **Are the implementation steps genuinely actionable?**
  (Each step starts with a verb and names a responsible party)
- [ ] **Is the timeline plausible?**
  (Multi-year infrastructure vs. emergency response should have different horizons)
- [ ] **Does the solution rely on assumptions that should be stated explicitly?**
  (e.g., "assumes functioning municipal government", "assumes reliable power supply")
- [ ] **Is the technology or approach already demonstrated at comparable scale?**
- [ ] **Are there prerequisite conditions** (land acquisition, legislation) that might block step 1?

---

## Section C: Assumptions Audit

- [ ] **Budget assumption**: Is the estimated cost based on comparable projects,
  or is it invented?
- [ ] **Capacity assumption**: Does the solution assume expertise or institutions
  that may not exist locally?
- [ ] **Data assumption**: Does the solution require reliable data that may not be
  collected yet?
- [ ] **Political assumption**: Does it assume sustained political will over a
  multi-year period without a mechanism to ensure it?
- [ ] **Community acceptance assumption**: Is community buy-in taken for granted
  without a consultation step?

---

## Section D: Hidden Risks

- [ ] **Who loses from this solution?** (Displacement of vendors, livelihoods, etc.)
- [ ] **Could it be gamed or corrupted?** (Tender manipulation, subsidy capture)
- [ ] **Does it create a new dependency?**
  (e.g., on a single vendor, on continued external funding, on a foreign technology)
- [ ] **Environmental side-effects**: Does the solution itself generate
  pollution, land use change, or ecological harm?
- [ ] **Does it entrench inequity?** (Better services for already-served areas)

---

## Section E: Improvement Triggers

Generate at least one `improvement_suggestion` if any of the following is true:

| Condition | Suggested improvement type |
|-----------|---------------------------|
| No short-term action | "Add immediate relief measure for first 30 days" |
| Steps are vague | "Specify responsible actor and measurable output for each step" |
| Cost is missing | "Provide rough cost estimate per implementation phase" |
| No monitoring mechanism | "Include a monitoring and evaluation step with defined KPIs" |
| No stakeholder list | "Name the primary implementer and funder explicitly" |
| Unintended consequence flagged | "Add mitigation step for [identified risk]" |
| Timeline missing | "Specify timeline for each phase" |

---

## Checklist Summary

Count failed checks per section and use to calibrate scores:

| Section | Failed checks → | Impact on score |
|---------|----------------|----------------|
| A (alignment) | > 1 | Lower realism |
| B (realism) | > 2 | Lower realism |
| C (assumptions) | > 2 | Lower feasibility |
| D (risks) | > 2 | Lower cost-effectiveness |
| E (improvements) | Any | Add to improvement_suggestions |

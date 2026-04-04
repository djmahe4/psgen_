# Solution Evaluation Rubric

A standardised 1–10 scoring guide for the `solution-critic` skill. All
dimensions are domain-agnostic.

---

## Scoring Principles

- **Anchor to real-world examples**, not abstract ideals.
- **Score independently** on each dimension before computing composite.
- A score of **5 is the neutral midpoint** ("plausible but unverified").
- Avoid clustering all scores at 7–8 (sycophancy) or 1–3 (overcriticism).

---

## Dimension 1: Realism Score (1–10)

> "Has this type of solution been demonstrated to work in a comparable context?"

| Score | Meaning |
|-------|---------|
| 9–10 | Proven in multiple comparable contexts; well-documented evidence |
| 7–8 | Proven in at least one comparable context; minor adaptation needed |
| 5–6 | Theoretical basis is sound; limited real-world evidence at this scale |
| 3–4 | Relies on optimistic assumptions; few comparable precedents |
| 1–2 | Relies on technology/capacity that does not exist or has never worked |

**Calibration anchors:**
- Score 9: "Emergency water tanker distribution during supply failure" — done globally
- Score 5: "Community-managed micro-grid" — works in some contexts, fails in others
- Score 2: "AI will automatically detect and fix all infrastructure problems"

---

## Dimension 2: Feasibility Score (1–10)

> "Given local resource, governance, and capacity constraints, can this be implemented?"

| Score | Meaning |
|-------|---------|
| 9–10 | All resources, authority, and capacity are clearly available |
| 7–8 | Most constraints are manageable; 1–2 significant hurdles |
| 5–6 | Multiple meaningful constraints; feasible with effort and luck |
| 3–4 | Major constraints (funding gap, governance failure, capacity shortage) |
| 1–2 | Requires conditions that clearly do not exist (political will, funding, skills) |

**Key constraints to check:**
- Legal authority to act
- Budget availability and funding pathway
- Technical skills in the implementing agency
- Community / political acceptance
- Physical infrastructure prerequisites

---

## Dimension 3: Cost-Effectiveness Score (1–10)

> "Is the expected benefit proportional to the cost and effort required?"

| Score | Meaning |
|-------|---------|
| 9–10 | Outstanding ROI; low cost, high impact, proven efficiency |
| 7–8 | Good ROI; cost is reasonable relative to number of people helped |
| 5–6 | Acceptable ROI; cost is somewhat high but impact justifies it |
| 3–4 | Poor ROI; high cost for modest or uncertain impact |
| 1–2 | Very poor ROI; cost far exceeds plausible benefit |

**Benchmark heuristic (cost per person helped):**

| Domain | Typical cost-effectiveness threshold |
|--------|--------------------------------------|
| Basic water supply | < $50 per person/year = good |
| Primary healthcare | < $100 per person/year = good |
| Infrastructure (roads, rails) | < $1,000 per person served = reasonable |
| Environmental remediation | Highly context-dependent |

---

## Composite Score Calculation

```
overall_score = round( (realism + feasibility + cost_effectiveness) / 3 )
```

Rounding rules:
- 0.5 rounds **up** (conservative bias — prefer regeneration when borderline)
- Result is bounded [1, 10]

### Routing thresholds
| overall_score | Agent action |
|--------------|-------------|
| ≥ 7 | Pass solution to formatter |
| < 7 AND iteration < 3 | Regenerate with improvement_suggestions |
| iteration == 3 | Pass regardless of score (note low score in output) |

---

## Dimension 4: Unintended Consequences

This dimension does **not** produce a numeric score; instead it populates the
`unintended_consequences` list.

Always check for:
- **Displacement effects**: Does the solution move the problem elsewhere?
- **Equity effects**: Does it disproportionately harm a vulnerable group?
- **Dependency creation**: Does it create long-term reliance on external support?
- **Environmental side-effects**: Does it introduce a new environmental harm?
- **Perverse incentives**: Could it discourage desirable behaviours?

Provide **at least one** consequence even for high-scoring solutions — no
solution is risk-free.

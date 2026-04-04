# Common Solution Failure Patterns

A catalogue of anti-patterns that the `solution-critic` should detect and
flag in `improvement_suggestions`. All patterns are domain-agnostic.

---

## Pattern 1: The Generic Action Trap

**Description**: Solution steps use vague, universal phrases that could apply
to any problem in any domain.

**Detection signals**:
- Steps contain: "Raise awareness", "Promote best practices",
  "Improve coordination", "Engage stakeholders", "Conduct training"
  **without** specifying for whom, on what, by whom, or with what outcome.

**Example bad step**: "Raise community awareness about the issue."

**Corrected version**: "Run a 6-week door-to-door campaign in the 3 most
affected neighbourhoods, reaching 5,000 households, with printed guides on
water conservation — delivered by trained NGO volunteers."

**Critic action**: Flag each vague step; set `realism_score` ≤ 5.

---

## Pattern 2: Unrealistic Scale

**Description**: The solution proposes an intervention whose scale or speed is
not achievable given local capacity.

**Detection signals**:
- "Deploy 500 engineers nationwide within 2 weeks"
- "Build 100 new hospitals in 6 months"
- "Digitise all government records by next quarter"

**Root cause**: The solution copies ambition from high-capacity contexts
(e.g., wealthy nations) without accounting for local resource availability.

**Critic action**: Lower `feasibility_score` proportionally; suggest
phased/piloted alternative in `improvement_suggestions`.

---

## Pattern 3: The Magical Technology Fix

**Description**: The solution relies on a single technology (AI, blockchain,
drone, satellite) as the primary mechanism, without addressing the governance,
data quality, or capacity needed to make it work.

**Detection signals**:
- "Use AI to predict and prevent all [problem type]"
- "Blockchain-based system will ensure transparency"
- "Drone delivery will solve supply chain issues"

**Root cause**: Technology framing avoids the harder problem of institutional
and human change.

**Critic action**: Lower `realism_score` if no implementation steps address
data readiness, training, or governance. Add "Specify the data pipeline,
integration effort, and staff training required" to `improvement_suggestions`.

---

## Pattern 4: The Infinite-Horizon Solution

**Description**: All implementation steps are long-term (> 2 years) with no
immediate relief action for the currently affected population.

**Detection signals**:
- No step with a timeline of < 90 days.
- `short_term_action` field is null.
- First step involves legislation, infrastructure construction, or a multi-year study.

**Critic action**: Add to `improvement_suggestions`: "Include an immediate
(0–30 day) relief measure that reduces harm while the long-term solution is
being implemented."

---

## Pattern 5: The Single-Stakeholder Assumption

**Description**: The solution implicitly assumes one entity can and will do
everything, when in reality multiple agencies, funders, or community actors
are needed.

**Detection signals**:
- Every step refers to the same actor ("the government", "the city").
- No mention of community, private sector, or civil society roles.
- Funding source is not named.

**Critic action**: Lower `feasibility_score` by 1–2 points; add
"Identify and assign roles to at least 3 distinct stakeholder groups" to
`improvement_suggestions`.

---

## Pattern 6: Ignoring the Most Vulnerable

**Description**: The solution serves the average or majority population
without addressing the disproportionate impact on vulnerable groups (elderly,
children, disabled, informal workers, migrants).

**Detection signals**:
- No mention of accessibility, equity, or targeting.
- Cost-recovery model that penalises low-income users.
- Physical intervention that displaces informal settlements.

**Critic action**: Add to `unintended_consequences`: "[Vulnerable group] may
not benefit from or may be harmed by this solution." Add improvement
suggestion to include equity safeguards.

---

## Pattern 7: No Monitoring or Exit Criteria

**Description**: The solution has no mechanism to measure success or decide
when it has worked (or failed).

**Detection signals**:
- No KPI, metric, or target mentioned.
- No evaluation or review checkpoint.
- No condition under which the intervention would be scaled back or stopped.

**Critic action**: Add to `improvement_suggestions`: "Define 2–3 measurable
KPIs and a 6-month review checkpoint to assess effectiveness."

---
skill: solution-critic
version: "1.0"
model: gemini-2.5-flash-latest
tool: critique_solution_tool
structured_output: Critique
triggers:
  - solution generated or regenerated
  - ENABLE_CRITIC=true
  - overall_score < 7 after previous critique
---

# Solution Critic

## Purpose
Independently evaluate a proposed solution on five axes — realism,
feasibility, cost-effectiveness, unintended consequences, and improvement
potential — and return a structured `Critique` with an `overall_score`.
If `overall_score < 7`, the agent regenerates the solution using the
`improvement_suggestions`.

---

## When to Activate
- Every time a `Solution` is generated (when `ENABLE_CRITIC=true`).
- On each regeneration cycle until `overall_score >= 7` or `iteration == 3`.

---

## Step-by-Step Reasoning

1. **Load context**  
   Retrieve `Problem` and `Solution` from agent state.

2. **Scoring prompt**  
   Ask the LLM to score on five axes (1–10 each):
   - Realism: "Has this been done in a comparable context?"
   - Feasibility: "Are the required resources available locally?"
   - Cost-effectiveness: "Is cost proportional to impact?"
   - Unintended consequences: list risks
   - Improvement suggestions: list concrete fixes

3. **Structured output via `.with_structured_output(Critique)`**

4. **Composite score**  
   `overall_score = round((realism + feasibility + cost_effectiveness) / 3)`

5. **Route decision**  
   - `overall_score >= 7` → pass solution forward to formatter
   - `overall_score < 7` AND `iteration < 3` → route back to solver
   - `iteration == 3` → pass best solution regardless of score

6. **Attach critique to solution**  
   `solution.critique = critique` before forwarding.

---

## Failure Modes
| Mode | Symptom | Mitigation |
|------|---------|------------|
| All scores 10 | LLM being sycophantic | Add adversarial system prompt instruction |
| All scores 1 | LLM being overly critical | Same — add calibration anchor |
| Empty consequences | LLM omits risks | Explicitly ask for ≥ 1 consequence |
| Infinite loop | Iteration counter not incremented | Guard in graph.py |

---

## Evaluation Criteria
- `realism_score`, `feasibility_score`, `cost_effectiveness_score` each 1–10.
- `unintended_consequences` ≥ 1 item.
- `improvement_suggestions` ≥ 1 item when `overall_score < 9`.
- `reasoning` ≥ 50 words.

---

## Example Triggers
- Solution generated: "Build new drainage canal across the city."
- Critic evaluates: realism=4 (no budget), feasibility=3 (requires land acquisition).
- overall_score=4 → agent regenerates with suggestion "Phase construction over 5 years".

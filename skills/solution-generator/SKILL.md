---
skill: solution-generator
version: "1.0"
model: gemini-2.5-flash-latest
tool: generate_solutions_tool
structured_output: Solution
triggers:
  - problems list non-empty in agent state
  - user asks "how can this be fixed?"
  - critic requests regeneration with improvement_suggestions
---

# Solution Generator

## Purpose
Produce realistic, step-by-step solutions for ranked problems.  Each solution
must include difficulty, estimated cost, and expected impact.  When called
after a critique, it incorporates `improvement_suggestions` from the
`Critique` object.

---

## When to Activate
- `agent_state.problems` is non-empty and `solutions` is empty.
- Critic node returns `overall_score < 7` and requests regeneration.
- User explicitly asks for a solution to a specific problem.

---

## Step-by-Step Reasoning

1. **Context injection**  
   Build a prompt that includes:
   - Problem description, severity, affected_people, location
   - Previous critique (if present): realism_score, improvement_suggestions
   - RAG memory: any similar past solutions retrieved from vector store

2. **Few-shot examples**  
   Provide 1–2 solved examples (different domain) to anchor format.

3. **Structured generation via `.with_structured_output(Solution)`**  
   No manual JSON parsing; Pydantic validates all fields.

4. **Cost estimation**  
   Prompt the LLM to provide a rough cost range in local currency.  If
   location currency is unknown, use USD.

5. **Difficulty calibration**  
   - easy  → < 6 months, single agency, < $500 k
   - medium → 6–24 months, multi-agency, $500 k–$10 M
   - hard  → > 24 months, cross-governmental, > $10 M

6. **Return**  
   Append `Solution` to `agent_state.solutions`; leave `critique=None`
   (critic node populates it next).

---

## Failure Modes
| Mode | Symptom | Mitigation |
|------|---------|------------|
| Generic steps | "Raise awareness", "Form committee" | Inject domain-specific constraints in prompt |
| Missing cost | `estimated_cost=None` | Fallback: ask LLM again with explicit cost prompt |
| Infinite loop | critic keeps rejecting | Hard cap of 3 iterations in graph.py |
| Overly optimistic | Impact claims unrealistic | Critic will flag; regeneration adds caveats |

---

## Evaluation Criteria
- `implementation_steps` contains ≥ 3 concrete, actionable items.
- `estimated_cost` present and plausible.
- `difficulty` consistent with step complexity.
- After critic loop: `overall_score` ≥ 7.

---

## Example Triggers
- "How do we fix the drainage problem in Bangalore?"
- Critic returns improvement_suggestions: ["Add community consultation phase"].
- RAG retrieves a similar successful solution from memory.

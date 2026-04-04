---
skill: problem-extractor-and-ranker
version: "1.0"
model: gemini-2.5-flash-latest
tool: extract_problems_tool
structured_output: Problem
triggers:
  - news_items populated in agent state
  - user requests problem list
---

# Problem Extractor and Ranker

## Purpose
Extract distinct, well-evidenced societal problems from a batch of news
articles, estimate their human impact, assign a severity level, and return
them ranked by `affected_people` (descending).

---

## When to Activate
- `news_items` is non-empty in agent state.
- `problems` list is empty or explicitly invalidated.
- User says "what are the main issues?" or similar.

---

## Step-by-Step Reasoning

1. **Contextual grounding**  
   Combine all snippet text with the `context` string (location/topic).

2. **Few-shot priming**  
   Use 2 few-shot examples embedded in the system prompt so the LLM
   understands the desired output structure.

3. **Structured extraction via `.with_structured_output(Problem)`**  
   Invoke the LLM chain once per batch; get back a validated `List[Problem]`
   without manual JSON parsing.

4. **Deduplication**  
   Remove problems whose `description` cosine similarity > 0.85 (using
   in-memory embeddings when RAG is enabled).

5. **Impact estimation**  
   If `affected_people == 0`, ask the LLM a follow-up question:
   "How many people live in {location}?  What % would be affected by {problem}?"

6. **Severity assignment**  
   Use the following heuristic as a soft prior:
   - critical — > 500 k affected OR life/death risk
   - high — 100 k–500 k OR major infrastructure
   - medium — 10 k–100 k OR economic harm
   - low — < 10 k AND no immediate danger

7. **Ranking**  
   Sort by `affected_people` descending.  Tie-break by severity.

8. **Return**  
   Populate `agent_state.problems`.

---

## Failure Modes
| Mode | Symptom | Mitigation |
|------|---------|------------|
| LLM returns empty list | No problems extracted | Retry with simplified prompt |
| Severity miscalibrated | All "critical" | Add calibration note to system prompt |
| Duplicate problems | Same issue twice | Dedup by description similarity |
| Hallucinated numbers | `affected_people` = 999999999 | Cap at city population from context |

---

## Evaluation Criteria
- Each `Problem.description` ≤ 200 chars, specific, non-generic.
- `affected_people` within plausible range for the location.
- Severity distribution reasonable (not all critical).
- Evidence field populated for ≥ 50 % of problems.

---

## Example Triggers
- After researcher returns articles about Chennai flooding.
- "List the top 5 issues in Nairobi".
- RAG memory suggests similar problems were found previously.

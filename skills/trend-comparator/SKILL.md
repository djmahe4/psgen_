---
skill: trend-comparator
version: "1.0"
model: gemini-2.5-flash-latest
tool: search_news
triggers:
  - user asks "compare" or "trend" or "getting worse"
  - agent detects same problem in memory from a previous session
  - ENABLE_TREND_COMPARE=true (optional flag)
---

# Trend Comparator

## Purpose
Compare the prevalence or severity of a problem category across two time
windows (e.g., 2024 vs 2025) or across two regions (e.g., Delhi vs Mumbai).
Detect rising issues by counting mentions and severity escalation.

---

## When to Activate
- User query contains temporal or comparative language:
  "Is flooding getting worse?", "Compare crime in X vs Y", "trend over time".
- Vector store memory returns a problem from a prior session matching the
  current location + category.

---

## Step-by-Step Reasoning

1. **Define comparison axes**  
   Determine whether comparison is:
   - **Temporal**: same location, two time windows (e.g., `time_filter="m"` vs
     archived memory)
   - **Spatial**: same topic, two locations

2. **Dual news fetch**  
   Call `search_news` twice with different `time_filter` values or different
   location strings.

3. **Problem extraction per window**  
   Run `extract_problems_tool` on each batch independently.

4. **Comparison logic**  
   For each matched problem pair:
   - Compare `affected_people` (% change)
   - Compare `severity` (escalation: low→medium = +1, etc.)
   - Count mention frequency

5. **Trend classification**  
   - Rising: `affected_people` increased > 20 % OR severity escalated
   - Stable: < 20 % change in both
   - Declining: `affected_people` decreased > 20 % AND severity same or lower

6. **Summary generation**  
   Ask LLM to write a 3–5 sentence comparative summary.

7. **Return**  
   Append trend metadata to `agent_state.problems[i]` as an optional field,
   and surface in UI under the "Trend" badge.

---

## Failure Modes
| Mode | Symptom | Mitigation |
|------|---------|------------|
| No historical data | Memory empty for location | Inform user; show single-period data only |
| Incomparable problems | Different extraction each run | Match by category keyword, not exact string |
| False rising trend | News volume spike (event-driven) | Normalise by total article count |
| Rate limit | Second `search_news` fails | Retry once; skip trend if still failing |

---

## Evaluation Criteria
- Trend label (rising/stable/declining) supported by numeric evidence.
- Comparison uses at least 3 articles per window.
- Summary ≤ 150 words, cites specific data points.

---

## Example Triggers
- "Is the water crisis in Chennai worse than last year?"
- "Compare air quality issues in Delhi and Mumbai."
- Memory shows flooding problem in Lagos from 2 sessions ago.

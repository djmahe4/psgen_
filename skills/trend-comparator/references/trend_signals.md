# Trend Signal Definitions

Standardised definitions for classifying whether a problem is rising,
declining, or stable, with anomaly detection guidance.

---

## 1. Primary Trend Classification

Use the `people_change_pct` and `severity_delta` computed in the comparison
framework to assign a trend label.

### Rising Trend
The problem is getting worse over time or is more severe in the comparison location.

**Conditions** (any one sufficient):
- `people_change_pct >= +20 %`
- `severity_delta >= +1` (e.g., medium → high)
- New problem category appeared in Arm 2 that was absent in Arm 1

**Confidence modifier**: If both conditions are true, confidence is higher.

---

### Declining Trend
The problem is improving over time or is less severe in the comparison location.

**Conditions** (all must hold):
- `people_change_pct <= -20 %`
- `severity_delta <= 0` (no escalation)
- Problem category still present in Arm 2 (not simply absent from news)

**Confidence note**: A problem disappearing from the news does not necessarily
mean it is resolved — it may simply be underreported. Note this caveat when
`arm2_article_count < 2`.

---

### Stable Trend
The problem persists at roughly the same scale with no clear direction.

**Conditions**:
- `-20 % < people_change_pct < +20 %`
- `severity_delta == 0`

---

### New / Emerging
A problem category found in Arm 2 (comparison) that did not appear in Arm 1 (baseline).

**Conditions**:
- No matching problem in Arm 1
- `arm2.affected_people > 0`

**Always classify as Rising unless `confidence < 0.3`** (may simply be
underreported in Arm 1).

---

### Resolved / No Longer Detected
A problem found in Arm 1 that does not appear in Arm 2.

**Conditions**:
- No matching problem in Arm 2
- `arm1.affected_people > 0`

**Do not classify as Declining** — absence of news coverage ≠ resolution.
Use label `"undetected_in_period"` and add caveat.

---

## 2. Anomaly Detection Signals

These signals suggest the trend classification may be misleading. Always
report them in `insights`.

| Signal | Indicator | Interpretation |
|--------|-----------|---------------|
| Event-driven spike | One catastrophic event in Arm 2 inflates numbers | May not reflect structural change |
| Media attention surge | Arm 2 has 3× more articles for same issue | Rising numbers may reflect coverage, not reality |
| Seasonal pattern | Both arms are not from the same season of year | Seasonal variation; compare same-season data |
| Cross-regional size difference | City A is 10× larger than City B | Normalise per capita before comparing |
| Data gap | One arm has < 2 articles | Low confidence; flag explicitly |
| Conflicting signals | `people_change_pct` is rising but `severity_delta` is falling | Disaggregate — may be two distinct sub-problems |

---

## 3. Rising Trend Severity Matrix

When a trend is classified as Rising, further characterise its urgency:

| Classification | Condition | Recommended action |
|---------------|-----------|-------------------|
| **Rapidly escalating** | Change > +50 % OR severity jumped 2 levels | Flag as priority; generate critical-level solution |
| **Steadily rising** | Change +20 to +50 % OR severity jumped 1 level | Include in top-3 problems for solution generation |
| **Slowly rising** | Change +5 to +20 % with no severity change | Monitor; include in output with lower priority |

---

## 4. Declining Trend Verification Checklist

Before reporting a decline, verify:
- [ ] The problem category is still mentioned in recent news (not just absent)
- [ ] The decline is not due to normalisation artifact (fewer articles)
- [ ] No seasonal explanation (e.g., dry season data vs. wet season)
- [ ] The improvement is corroborated by at least one explicit statement in the news
  (e.g., "authorities report decrease in cases", "flood defences completed")

If fewer than 2 items on the checklist are confirmed, downgrade confidence to ≤ 0.4.

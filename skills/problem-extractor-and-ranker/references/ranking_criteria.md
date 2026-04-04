# Problem Ranking Criteria

A standardised rubric for assigning severity and ranking a list of extracted
problems for downstream solution generation.

---

## 1. Severity Definitions

### critical
> Immediate threat to life, mass displacement, or complete failure of an
> essential service affecting a large population.

Indicators (any one qualifies):
- Reported fatalities or mass casualties
- > 500,000 people directly affected
- Essential service (water, power, healthcare) fully offline for > 48 h
- Declared state of emergency
- Rapid geographic spread (epidemic, wildfire, flood)

### high
> Significant harm or serious disruption to daily life for a large number of people.

Indicators (any one qualifies):
- 100,000–500,000 people affected
- Essential service degraded (not fully offline) for > 1 week
- Major economic disruption (businesses closed, significant crop loss)
- Health harm to many but not mass casualties
- Risk of escalation to critical within 30 days

### medium
> Noticeable negative impact on a moderate population; situation is chronic
> or worsening but not immediately life-threatening.

Indicators (any one qualifies):
- 10,000–100,000 people affected
- Service disruption lasting weeks but with workarounds available
- Moderate economic impact (10–30 % productivity loss in a sector)
- Social unrest without violence

### low
> Limited or localised impact; situation is manageable or affects a small group.

Indicators (all three apply):
- < 10,000 people affected
- No immediate danger to life
- Temporary or easily mitigated disruption

---

## 2. Multi-Factor Ranking Formula

After severity is assigned, rank problems using a composite score:

```
rank_score = (0.5 × normalised_affected_people)
           + (0.3 × severity_weight)
           + (0.2 × urgency_weight)
```

| Factor | Value |
|--------|-------|
| `normalised_affected_people` | `affected_people / max(affected_people in batch)` |
| `severity_weight` | critical=1.0, high=0.75, medium=0.5, low=0.25 |
| `urgency_weight` | 1.0 if acute event, 0.7 if systemic, 0.4 if latent risk |

**Primary sort**: `rank_score` descending.
**Secondary sort** (tie-break): see Section 3.

---

## 3. Tie-Breaking Logic

When two problems have equal `rank_score` (within ±0.02):

1. **Higher severity** wins.
2. If severity also equal: **acute event** beats systemic issue (more urgent).
3. If still tied: **richer evidence** (has `evidence` field populated) wins.
4. Final tie-break: **alphabetical by location** (deterministic).

---

## 4. Cap and Normalisation Rules

- Maximum **10 problems** returned per batch (focus quality over quantity).
- Deduplicate before ranking (see `problem_extraction_guide.md`).
- If all problems have the same `severity`, still rank by `affected_people`.
- Never return a list where every item is `severity=critical` unless
  independently verified by ≥ 2 distinct news sources each.

---

## 5. Severity Escalation Triggers

Upgrade severity by one level if any of the following appear in evidence:

| Trigger phrase | Escalation |
|---------------|-----------|
| "rapidly spreading" / "escalating" | +1 level |
| "state of emergency declared" | → critical immediately |
| "authorities overwhelmed" | +1 level |
| "second week" / "third week" (of disruption) | +1 level if currently medium |
| "children / elderly / hospitals affected" | +1 level |

Downgrade by one level if:
- "partial service restored"
- "situation improving"
- "government response deployed"

# Trend Comparison Framework

A domain-agnostic methodology for comparing problems across time periods
or geographic regions to identify rising, stable, or declining trends.

---

## 1. Comparison Types

### Type A: Temporal Comparison (Same Place, Different Time)
> "Is flooding in [City] getting worse year-over-year?"

| Element | Definition |
|---------|-----------|
| Anchor period | The earlier of the two time windows (baseline) |
| Comparison period | The more recent window |
| Unit of analysis | The problem category, not individual incidents |

**Use when**: The user asks about trends, worsening/improving conditions, or
year-over-year change.

### Type B: Spatial Comparison (Same Topic, Different Place)
> "How do water access problems in City A compare to City B?"

| Element | Definition |
|---------|-----------|
| Reference location | The better-known or baseline location |
| Comparison location | The target location |
| Unit of analysis | The same problem category in both locations |

**Use when**: The user asks to compare two regions or wants to benchmark one
location against another.

### Type C: Multi-Dimensional (Both Time and Space)
> "Has air quality improved more in City A or City B over the past year?"

Combine Type A and Type B. Requires at least 2 × 2 data points.

---

## 2. Step-by-Step Comparison Process

### Step 1: Define the Comparison Axis
Confirm with the user (or infer from query) which type (A, B, or C) applies.
State the axis explicitly in output: `"Comparing flooding in [City] between
2024 and 2025"`.

### Step 2: Collect Data Per Window / Location
Run `search_news` separately for each arm of the comparison:
- Arm 1: `query="[city] [topic] [year1]"`, `time_filter="m"`
- Arm 2: `query="[city] [topic] [year2]"`, `time_filter="m"`

Do **not** mix results from different arms before problem extraction.

### Step 3: Extract Problems Per Arm
Run `extract_problems_tool` independently on each arm's news batch.
This produces two `List[Problem]` sets.

### Step 4: Match Problem Pairs
Match problems across arms by **topic category** (not exact description):
- Identify a shared category label (e.g., "flooding", "air quality", "healthcare")
- A match is valid if both descriptions refer to the same phenomenon in the
  same location (temporal comparison) or the same phenomenon in different
  locations (spatial comparison)
- Unmatched problems are noted as "new" (appeared only in one period/region)

### Step 5: Compute Change Metrics
For each matched pair:

```
people_change_pct = (arm2.affected_people - arm1.affected_people)
                    / arm1.affected_people × 100

severity_delta    = severity_rank(arm2) - severity_rank(arm1)
                    # severity_rank: low=1, medium=2, high=3, critical=4
```

### Step 6: Classify Trend
Apply the classification logic from `trend_signals.md`.

### Step 7: Normalise for Article Volume
If Arm 2 has significantly more articles than Arm 1 (> 2× volume), normalise
problem counts by article volume to avoid false "rising" trends caused purely
by increased news coverage.

```
normalised_affected = raw_affected / num_articles_in_arm
```

### Step 8: Generate Insight Summary
Produce a 3–5 sentence plain-language summary citing specific numbers.
Avoid: "the situation may be worsening". Prefer: "Affected population
increased by 40 % (from 50,000 to 70,000) between 2024 and 2025, and severity
escalated from medium to high, indicating a rising trend."

---

## 3. Normalisation Strategies

| Scenario | Normalisation method |
|----------|---------------------|
| Unequal article counts between arms | Divide `affected_people` by article count per arm |
| Different city sizes | Divide `affected_people` by city population (express as per-capita rate) |
| Seasonal events (e.g., monsoon flooding) | Compare same season across years, not cross-season |
| Event-driven spike (e.g., one major disaster) | Flag as event-driven; note that trend may not be structural |

---

## 4. Confidence Assessment

| Level | Condition |
|-------|-----------|
| High (0.8–1.0) | ≥ 5 articles per arm; clear numeric evidence; no event-driven spike |
| Medium (0.5–0.8) | 3–4 articles per arm; some numeric evidence; possible seasonal factor |
| Low (0.2–0.5) | 1–2 articles per arm; limited numeric data; significant uncertainty |
| Inconclusive (< 0.2) | < 1 article per arm or no matching problem pairs |

Always report confidence in the output's `confidence` field.

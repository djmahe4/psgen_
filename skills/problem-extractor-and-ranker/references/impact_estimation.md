# Impact Estimation Guide

Methods for estimating the number of people affected by a problem and
assessing its broader economic, environmental, and social impact.

---

## 1. Estimating Affected Population

### 1.1 Use Explicit Figures First
If the news snippet contains a number directly, use it:
- "3,000 families displaced" → `affected_people = 3000 × avg_household_size`
  (use 4 if household size unknown)
- "Serves 200,000 residents" → `affected_people = 200000`

### 1.2 Proportional Estimation
When no explicit figure is given:

```
affected_people = population_of_area × exposure_rate
```

| Problem type | Typical exposure rate |
|-------------|----------------------|
| City-wide water supply failure | 80–95 % of city population |
| Localised flooding | 5–20 % of city population |
| Hospital strike | 100 % of current inpatients + 30 % of outpatients |
| School closure | 100 % of enrolled students |
| Power outage (entire grid) | 90 % of city population |
| Air quality crisis | 60–80 % of urban population |
| Road closure | 10–40 % of commuters in corridor |

**When city population is unknown**: use the country's median city population
as a conservative proxy. Do not use national population.

### 1.3 Population Reference Tiers
Use these conservative tiers when no population data is available:

| Area type | Conservative estimate |
|-----------|----------------------|
| Village / rural settlement | 500 – 5,000 |
| Small town | 10,000 – 50,000 |
| Medium city | 100,000 – 500,000 |
| Large city / metro | 1,000,000 – 5,000,000 |
| Mega-city | 5,000,000 – 20,000,000 |

### 1.4 Conservative vs Aggressive Estimation

| Mode | When to use | Multiplier |
|------|-------------|-----------|
| Conservative | Uncertain data, local issue | Use lower bound of tier |
| Moderate (default) | Typical news coverage | Use midpoint |
| Aggressive | Explicitly escalating crisis with multiple sources | Use upper bound |

**Default**: always use **moderate** unless SKILL.md instructs otherwise.

---

## 2. Economic Impact Dimensions

Note economic impact in `evidence` or `description` when present:

| Indicator | Example signal in news |
|-----------|----------------------|
| Business closures | "50 shops shut during strike" |
| Productivity loss | "workers unable to commute" |
| Property damage | "₹200 Cr in flood damage" |
| Healthcare costs | "600 hospitalised, treatment costs mounting" |
| Agricultural loss | "40% of crop destroyed" |

---

## 3. Environmental Impact Dimensions

| Indicator | Severity signal |
|-----------|----------------|
| Water body contamination | Immediate — affects drinking water and ecosystems |
| Air quality index > 150 | High — respiratory harm across population |
| Soil contamination | Medium-long term — agricultural and groundwater risk |
| Deforestation | Long-term — climate and biodiversity |
| Noise pollution | Low-medium unless chronic |

---

## 4. Social Impact Dimensions

| Indicator | Severity signal |
|-----------|----------------|
| Displacement / homelessness | Critical — immediate survival need |
| School disruption | High — long-term developmental harm |
| Mental health crisis | Medium-high — often underreported |
| Social unrest / protest | High — signals systemic failure |
| Loss of livelihoods | High — cascading effects |
| Breakdown of community services | Medium — depends on duration |

---

## 5. Validation Rules

- `affected_people` must be `>= 0`
- If your estimate exceeds the **total population of the referenced area**, cap it at 95 % of that population
- Round to the nearest 100 for estimates < 10,000; nearest 1,000 for 10,000–1,000,000; nearest 10,000 above that
- Never use `999999999` or `1000000000` as a placeholder — use a realistic estimate with a note in `evidence`

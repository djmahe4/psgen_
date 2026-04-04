# Problem Extraction Guide

A domain-agnostic framework for identifying, structuring, and validating
societal problems extracted from news text.

---

## 1. What Qualifies as a "Problem"?

A valid problem must satisfy **all three** of the following:

| Criterion | Description |
|-----------|-------------|
| **Negative condition** | Describes harm, failure, deficiency, or risk — not a neutral event |
| **Affects people or systems** | Has identifiable human, economic, or environmental impact |
| **Actionable** | Could, in principle, be mitigated or resolved by human intervention |

### ✅ Valid problems
- "Contaminated water supply serving 200,000 residents"
- "Chronic power outages causing business closures"
- "Overcrowded public hospitals with 150% bed occupancy"

### ❌ Not valid problems
- "City council held a meeting" (neutral event, no harm)
- "Mayor gave a speech about development" (political activity, no direct harm)
- "New shopping mall opened" (positive event)
- "Weather is hot this summer" (natural condition, not actionable unless it causes harm)

---

## 2. Event vs Systemic Issue

Correctly classifying a problem type improves severity assessment and solution quality.

| Type | Definition | Example | Typical severity |
|------|-----------|---------|-----------------|
| **Acute event** | Sudden, bounded in time; may resolve on its own | Flood, chemical spill, building collapse | high / critical |
| **Systemic issue** | Ongoing, structural, affects people repeatedly | Inadequate drainage causing annual floods, under-funded schools | medium / high |
| **Latent risk** | Not yet causing harm but evidence of future failure | Ageing bridge with no inspections, rising sea levels | low / medium |

**Rule**: If the same problem appears in news across multiple months or years,
classify as **systemic**. If it is a one-time reported event, classify as **acute**.

---

## 3. Extracting Root Causes vs Symptoms

Always try to extract the **root cause**, not just the visible symptom.

| Symptom (surface level) | Root cause (preferred) |
|------------------------|------------------------|
| "Streets flooded after rain" | "Inadequate stormwater drainage capacity" |
| "Long hospital waiting times" | "Shortage of qualified medical staff" |
| "Children not attending school" | "Lack of safe transport to schools" |
| "High crime rates" | "Unemployment and lack of youth services" |

### Extraction rule
If the snippet contains an **effect word** (`caused by`, `due to`, `as a result of`,
`because of`, `leading to`, `after`), follow the causal chain one step deeper.

### When to stop
If the causal chain reaches governance or structural poverty, record that as the
root cause and note it in the `evidence` field. Do not recurse indefinitely.

---

## 4. Field Population Rules

| Field | Rule |
|-------|------|
| `description` | ≤ 200 chars; specific noun phrase + context, no vague adjectives |
| `affected_people` | Integer; use impact estimation guide; never 0 unless truly zero |
| `severity` | Apply severity rubric from ranking_criteria.md |
| `location` | Most specific geographic unit mentioned; include country if ambiguous |
| `evidence` | Verbatim quote or headline fragment supporting the claim; omit if none available |

---

## 5. Deduplication Rules

Two extracted problems are **duplicates** if:
- Their `description` fields share ≥ 6 of the same content words (ignoring stopwords), **OR**
- One description is a subset of the other, **OR**
- They refer to the same root cause even if framed differently

When duplicates are detected: **keep the one with the higher `affected_people`
estimate** and the richer `evidence`.

---

## 6. Rejection Rules

Reject an extracted problem if:
- The description is generic: "poor governance", "lack of infrastructure" (no specificity)
- `affected_people` would require knowledge of the full national population and the issue is truly universal
- The "problem" is actually a proposed solution (e.g., "government plans to build dam")
- The evidence is an opinion piece with no reported facts

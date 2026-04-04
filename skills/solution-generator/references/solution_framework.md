# Solution Design Framework

A domain-agnostic guide for generating realistic, step-based solutions to
societal problems identified by the extractor skill.

---

## 1. Step-by-Step Solution Design Process

### Step 1 — Understand the Problem Fully
Before generating a solution, confirm you have:
- [ ] Root cause (not just the symptom)
- [ ] Affected population size and profile
- [ ] Severity and urgency
- [ ] Geographic and institutional context

### Step 2 — Classify the Problem Domain
Map to one of these domains to anchor solution types:

| Domain | Typical solution levers |
|--------|------------------------|
| Physical infrastructure | Repair, upgrade, new construction, maintenance regime |
| Public health | Treatment, prevention, surveillance, behaviour change |
| Governance / institutions | Policy reform, accountability mechanisms, capacity building |
| Economic | Employment programmes, subsidies, market regulation |
| Environment | Remediation, protection, restoration, monitoring |
| Social services | Facility expansion, staffing, community support |
| Technology / information | Platforms, data systems, digital services |

### Step 3 — Generate Short-Term and Long-Term Components

Every solution should have **both** layers:

| Layer | Time horizon | Purpose |
|-------|-------------|---------|
| **Immediate relief** | 0–3 months | Stop the bleeding; reduce acute harm |
| **Medium-term fix** | 3–18 months | Address proximate cause |
| **Long-term prevention** | 18+ months | Eliminate root cause; build resilience |

> **Rule**: Never propose a solution that is only long-term — always include
> at least one immediate action.

### Step 4 — Identify Stakeholders
List the actors needed to implement each step:

| Stakeholder type | Examples |
|-----------------|---------|
| Primary implementer | Municipal authority, health ministry, transport agency |
| Funder | Local budget, central government grant, development bank, private sector |
| Regulator | Permits, environmental clearance, building codes |
| Community | Residents, civil society, local NGOs |
| Technical experts | Engineers, doctors, data scientists |

### Step 5 — Write Implementation Steps
- Use imperative verb to start each step: "Conduct", "Deploy", "Establish", "Tender"
- Each step should be independently actionable
- Include who does it + what outcome is expected
- Minimum 3 steps, maximum 8 for readability

### Step 6 — Assign Difficulty and Cost
Apply the criteria from `feasibility_checklist.md`.

---

## 2. Short-Term vs Long-Term Solution Patterns

| Problem type | Short-term action | Long-term action |
|-------------|------------------|-----------------|
| Water supply failure | Emergency tanker distribution | Infrastructure upgrade / new pipeline |
| Power outage | Generator deployment for critical facilities | Grid modernisation / renewable energy |
| Flooding | Temporary barriers, evacuation | Stormwater infrastructure, zoning reform |
| Hospital overload | Patient transfer protocols | Capacity expansion, staff recruitment |
| Air pollution | Health advisories, mask distribution | Emission regulation, clean energy transition |
| Road collapse | Traffic diversion, temporary repair | Full reconstruction with better materials |

---

## 3. Solution Anti-Patterns to Avoid

| Anti-pattern | Why it fails | Better alternative |
|-------------|-------------|-------------------|
| "Raise awareness" as the primary step | No direct harm reduction | Pair awareness with a concrete service delivery action |
| "Form a committee to study the issue" | Delays action; no output | "Conduct a 2-week rapid assessment and publish findings" |
| "Invest in technology" without specifics | Vague and expensive | Name the specific technology and use case |
| Single-step solution | Misses complexity | Always include ≥ 3 ordered steps |
| "International best practice" without adaptation | Ignores local constraints | Add "Adapt to local context by..." |
| Assuming unlimited budget | Unrealistic | Acknowledge cost tier in `estimated_cost` |

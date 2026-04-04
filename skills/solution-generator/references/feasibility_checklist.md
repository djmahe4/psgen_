# Solution Feasibility Checklist

Use this checklist before finalising a solution. A solution that fails more
than 2 checks in any category should be revised or have its `difficulty`
upgraded.

---

## Category 1: Technical Feasibility

- [ ] **Proven technology**: Has this approach been successfully implemented
      at a similar scale in any comparable context?
- [ ] **Local capacity**: Are the technical skills required available locally,
      or can they be acquired within the implementation timeline?
- [ ] **Materials / supply chain**: Are required materials or equipment
      accessible within a reasonable lead time?
- [ ] **Infrastructure dependency**: Does the solution require pre-existing
      infrastructure that may not be present (e.g., reliable power grid,
      internet connectivity, trained workforce)?
- [ ] **Data requirements**: If the solution relies on data, is that data
      already collected or collectible within scope?

---

## Category 2: Cost Constraints

- [ ] **Budget order of magnitude stated**: Is the estimated cost range
      provided (even if approximate)?
- [ ] **Proportionality**: Is the estimated cost proportional to the scale of
      the problem (i.e., cost per person affected is reasonable)?
- [ ] **Funding source identified**: Is there a plausible funding pathway
      (government budget, grant, private sector, community contribution)?
- [ ] **Recurrent vs capital costs**: Are ongoing operational costs (staffing,
      maintenance) acknowledged, not just one-time capital investment?
- [ ] **Currency / inflation risk**: For multi-year solutions, is cost
      inflation mentioned or assumed stable?

### Cost Tier Reference

| Tier | Range | Typical `difficulty` |
|------|-------|---------------------|
| Micro | < $50,000 | easy |
| Small | $50k – $500k | easy / medium |
| Medium | $500k – $10M | medium |
| Large | $10M – $100M | hard |
| Mega | > $100M | hard (multi-phase required) |

---

## Category 3: Regulatory & Governance Constraints

- [ ] **Legal authority**: Is there a government body with the legal mandate
      to implement this solution?
- [ ] **Permits / approvals**: Are the required permits realistic to obtain
      within the stated timeline?
- [ ] **Political feasibility**: Is there precedent for this type of
      intervention by the relevant authority?
- [ ] **Land / property**: If physical construction is required, is land
      acquisition a significant barrier?
- [ ] **Community consent**: Does the solution require community buy-in, and
      is that achievable given current trust levels?

---

## Category 4: Scalability

- [ ] **Pilot-ready**: Can the solution be tested at small scale before
      full rollout?
- [ ] **Modular design**: Can it be implemented in phases rather than all
      at once?
- [ ] **Replicable**: Would a successful implementation be transferable to
      other locations with similar problems?
- [ ] **Monitoring built in**: Is there a mechanism to measure effectiveness
      and adjust?

---

## Difficulty Assignment Guide

Count the number of **failed checks** across all categories:

| Failed checks | Assigned `difficulty` |
|--------------|----------------------|
| 0 – 2 | `easy` |
| 3 – 5 | `medium` |
| 6+ | `hard` |

> If any single regulatory or technical check is a hard blocker (e.g.,
> requires constitutional amendment, or no proven technology exists),
> assign `hard` regardless of total count.

# Search Best Practices

A domain-agnostic guide for constructing, expanding, and refining search
queries used by the `news-researcher` skill.

---

## 1. Query Construction Principles

### 1.1 The Three-Part Formula
```
[SUBJECT] + [PROBLEM TYPE] + [TEMPORAL ANCHOR]
```
| Slot | Good example | Bad example |
|------|-------------|-------------|
| Subject | "Lagos water supply" | "water" |
| Problem type | "shortage crisis contamination" | "issue" |
| Temporal anchor | "2025" / "this week" / "latest" | (omit → stale results) |

### 1.2 Always Include at Least One Problem-Type Keyword
Preferred terms (pick 1–2):
`shortage`, `crisis`, `failure`, `outbreak`, `flooding`, `collapse`,
`corruption`, `protest`, `strike`, `blackout`, `pollution`, `displacement`,
`congestion`, `violence`, `poverty`, `delay`, `scandal`

### 1.3 Use the Most Specific Geographic Unit Available
- ✅ "Dharavi, Mumbai" — neighbourhood level
- ✅ "Mumbai, Maharashtra" — city + state
- ⚠️  "India" alone — too broad; expect noisy results

---

## 2. Query Expansion Strategies

### 2.1 Synonym Expansion
Always generate 2–3 synonymous sub-queries:
| Primary term | Synonyms to try |
|-------------|-----------------|
| water shortage | water crisis, water scarcity, water cut, dry taps |
| power outage | electricity failure, blackout, load shedding, grid collapse |
| traffic congestion | gridlock, road blockage, commuter delays |
| healthcare crisis | hospital overload, medicine shortage, patient backlog |

### 2.2 Cause / Effect Expansion
Search both the cause **and** the symptom:
- Cause: "broken drainage pipe flooding"
- Effect: "residents evacuated flood damage"

### 2.3 Temporal Filters
| DuckDuckGo filter | When to use |
|-------------------|-------------|
| `time_filter="d"` | Breaking news; high-severity alerts |
| `time_filter="w"` | Default; captures ongoing issues |
| `time_filter="m"` | Background / trend; chronic issues |

Use `"w"` as the default. Escalate to `"d"` if severity = critical. Use `"m"`
only for trend-comparator calls.

---

## 3. When to Refine vs Broaden

| Situation | Action |
|-----------|--------|
| 0 results returned | **Broaden**: remove location, use only problem keyword |
| > 50 % results off-topic | **Refine**: add more specific keywords |
| Results all > 1 year old | **Refine**: append current year ("2025") |
| All results from a single source | **Diversify**: add `-site:thatdomain.com` if supported |
| High duplication across sub-queries | **Deduplicate**: keep unique by URL + 80-char snippet key |

### Refinement checklist
- [ ] Is the location name spelled correctly and unambiguous?
- [ ] Is there a year anchor in at least one sub-query?
- [ ] Are problem-type keywords present?
- [ ] Are synonymous sub-queries also queued?

---

## 4. Deduplication Strategies

### 4.1 URL Exact Match
Discard any item whose `url` has already been seen in the current batch.

### 4.2 Title Near-Duplicate (Fuzzy)
If two titles share ≥ 80 % of their word tokens (after stop-word removal),
keep only the item with the longer `summary`.

### 4.3 Snippet Fingerprint
Hash the first 80 characters of the `summary` (lowercased, whitespace
normalised). Discard subsequent items with the same hash.

### 4.4 Source Diversity
Cap results from any single domain at 3 items to prevent one outlet
dominating the feed.

---

## 5. Anti-Patterns to Avoid

| Anti-pattern | Why it fails |
|-------------|--------------|
| Single very broad query | Returns generic national news, misses local issues |
| No temporal anchor | Returns results from years ago |
| Querying opinion/editorial terms | "should" / "must" — returns commentary, not facts |
| Mixing unrelated topics in one query | Lowers relevance of all results |
| Re-running identical query in same session | Wastes API quota; hits rate limit |

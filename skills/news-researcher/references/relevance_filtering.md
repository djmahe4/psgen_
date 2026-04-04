# Relevance Filtering Guide

Rules for deciding which retrieved news items are worth passing to the
`problem-extractor-and-ranker` skill. These criteria are domain-agnostic.

---

## 1. Relevance Scoring Criteria

Score each item 0–1 across three dimensions; keep items with **total ≥ 0.5**.

### 1.1 Topical Match (0–0.4)
Does the snippet describe a **concrete negative condition** affecting people
or infrastructure?

| Score | Signal |
|-------|--------|
| 0.4 | Directly names a problem, harm, failure, or crisis |
| 0.3 | Mentions an affected group or place experiencing difficulty |
| 0.2 | Tangentially related (policy debate, upcoming risk) |
| 0.0 | Entirely off-topic (sports, entertainment, advertising) |

### 1.2 Geographic / Thematic Match (0–0.4)
Does the item relate to the queried location or topic?

| Score | Signal |
|-------|--------|
| 0.4 | Exact location named in title or first sentence |
| 0.3 | Region / country mentioned |
| 0.2 | Related city or neighbouring area |
| 0.0 | Different country/domain entirely |

### 1.3 Recency (0–0.2)
How fresh is the content?

| Score | Signal |
|-------|--------|
| 0.2 | Published within the last 7 days |
| 0.1 | Published within the last 30 days |
| 0.0 | No date detectable or clearly > 30 days old |

---

## 2. Mandatory Discard Rules (Override Scoring)

Discard an item **immediately** regardless of score if it matches any of:

| Rule | Pattern |
|------|---------|
| Promotional | Title contains "sponsored", "advertorial", "buy now", "sale" |
| Purely positive | No negative condition, harm, or risk mentioned anywhere |
| Opinion without facts | Only "should", "could", "may" — no reported event |
| Paywall stub | Snippet ≤ 30 words AND contains "subscribe", "log in", "premium" |
| Duplicate fingerprint | Snippet hash already seen in current batch |
| Irrelevant domain | Sports scores, celebrity gossip, stock prices (unless query is financial) |

---

## 3. Noise Filtering Rules

### 3.1 Minimum Snippet Length
Require `len(snippet) >= 80` characters. Shorter snippets lack enough context
for problem extraction.

### 3.2 Keyword Gate
At least one of the following must appear in title **or** snippet (case-insensitive):
```
problem, issue, crisis, shortage, flood, outage, collapse, failure,
corruption, protest, outbreak, pollution, displacement, violence,
accident, strike, delay, scandal, damage, injury, death, loss,
shortage, poverty, crime, drought, fire, disease, conflict, risk
```

### 3.3 Language Check
If the snippet contains > 50 % non-ASCII characters and the query was
English, flag for language mismatch and deprioritise (score × 0.5).

---

## 4. Source Credibility Heuristics

These are heuristics — not a curated allowlist — since sources vary by domain
and region.

| Signal | Interpretation |
|--------|---------------|
| Domain ends in `.gov`, `.edu`, `.org` | Generally higher factual reliability |
| URL contains `/news/` or `/article/` | Likely a news article (not a forum) |
| Title has numeric specificity | "3,000 families displaced" > "many displaced" |
| Multiple named sources / quotes | Corroborated; higher credibility |
| Single anonymous source | Lower confidence; note in evidence field |
| Social media domain (twitter.com, facebook.com) | Use as signal only; do not cite as primary source |
| Outlet known for satire | Discard |

---

## 5. Final Filtering Pipeline (Ordered)

```
1. Apply mandatory discard rules  →  drop items
2. Check keyword gate             →  drop items not passing
3. Score remaining items          →  0.0 – 1.0
4. Keep items with score ≥ 0.5
5. Sort by score descending
6. Cap at max_results (default 10)
7. Apply source diversity cap (max 3 per domain)
```

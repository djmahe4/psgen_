---
skill: news-researcher
version: "1.0"
model: gemini-2.5-flash-latest
tool: search_news, fetch_full_article
triggers:
  - user provides a location or topic
  - agent state has no news_items yet
  - trend_comparator requests a new time window
---

# News Researcher

## Purpose
Gather a high-quality, deduplicated, relevance-filtered set of recent news
articles for a given location or topic.  The researcher expands the user query
into multiple sub-queries, fetches results in parallel, deduplicates by URL
and headline similarity, and optionally fetches full article text for
high-severity snippets.

---

## When to Activate
- State field `news_items` is empty or stale (> 24 h old).
- User query contains a new location not seen in conversation memory.
- Trend comparator requests articles for a second time period.

---

## Step-by-Step Reasoning

1. **Query expansion**  
   Decompose the user input into 2–3 complementary search strings:
   - `"{location} problems 2025"`
   - `"{location} crisis latest news"`
   - `"{location} infrastructure public health issues"`

2. **Parallel search**  
   Fire all sub-queries via `search_news` with `time_filter="w"` (last week).
   Collect raw result lists.

3. **Deduplication**  
   Remove duplicate items where `link` is identical or `title` similarity > 80 %.

4. **Relevance filtering**  
   Drop items whose snippet contains none of:
   {problem, issue, crisis, shortage, flood, crime, health, infrastructure,
    corruption, poverty, violence, disaster, outage}.

5. **Conditional full-article fetch**  
   If `ENABLE_FULL_ARTICLE_FETCH=true` **and** a snippet mentions severity
   keywords (death, casualty, collapse, outbreak), call `fetch_full_article`
   for that URL and replace the snippet with the first 800 chars.

6. **Return**  
   Pass deduplicated, filtered `List[NewsItem]` into agent state `news_items`.

---

## Failure Modes
| Mode | Symptom | Mitigation |
|------|---------|------------|
| Rate limit | `search_news` returns `[]` | Retry with exponential backoff (tenacity) |
| Irrelevant results | All snippets filtered out | Fall back to broader query without location |
| Paywall / 403 | `fetch_full_article` returns `ERROR:` | Log, skip full fetch, use snippet |
| Empty query | Sanitisation strips all chars | Return error to user immediately |

---

## Evaluation Criteria
- At least 3 unique news items returned for any major city.
- < 10 % duplicate rate after dedup.
- No items unrelated to the location returned.
- Full article text fetched only when explicitly enabled.

---

## Example Triggers
- "Show me problems in Chennai"
- "What's happening in Lagos right now?"
- "Compare water issues in Delhi 2024 vs 2025"

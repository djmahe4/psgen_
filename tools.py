"""
LangChain tool definitions for the Problem Statement Generator.

Every tool uses the @tool decorator and structured outputs — no manual JSON parsing.
Tools are designed to be used by the LangGraph agent nodes.

Security: all user-supplied strings pass through sanitize_input() before use.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

from models import Critique, NewsItem, Problem, ProblemWithSolution, Solution

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize(text: str, max_length: int = 300) -> str:
    """Strip injection-prone characters and cap length."""
    if not text:
        return ""
    text = text.strip()[:max_length]
    text = re.sub(r"[^\w\s,.\-()'\":!?]", "", text)
    return text


_ddg = DuckDuckGoSearchRun()


# ---------------------------------------------------------------------------
# 1. search_news
# ---------------------------------------------------------------------------

@tool
def search_news(query: str, max_results: int = 10, time_filter: str = "w") -> List[dict]:
    """
    Search DuckDuckGo for recent news articles matching *query*.

    WHEN TO USE:
        Call this first whenever a fresh news feed is needed for a location or topic.

    WHEN NOT TO USE:
        • Do NOT call repeatedly with the same query in a single run (cache hit).
        • Do NOT use for historical data older than ~1 month; results will be sparse.

    INPUTS:
        query       — search string (location + topic, e.g. "Mumbai water shortage 2025")
        max_results — cap on returned snippets (1–20); default 10
        time_filter — recency filter passed to DuckDuckGo:
                      "d" = last day, "w" = last week (default), "m" = last month

    OUTPUT:
        List of dicts with keys: title, snippet, link, source

    EDGE CASES:
        • If DuckDuckGo is rate-limited, returns an empty list and logs a warning.
        • Very obscure locations may return 0 results — caller should widen query.
    """
    query = _sanitize(query, 200)
    if not query:
        logger.warning("search_news: empty query after sanitization")
        return []

    max_results = max(1, min(max_results, 20))

    try:
        raw: str = _ddg.run(query)
    except Exception as exc:
        logger.warning("search_news: DuckDuckGo error — %s", exc)
        return []

    # DuckDuckGoSearchRun returns a flat string; split on double-newline.
    sections = [s.strip() for s in raw.split("\n\n") if s.strip()]
    items: List[dict] = []
    base_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"

    for i, section in enumerate(sections[:max_results]):
        items.append(
            {
                "title": f"Result {i + 1} — {query[:60]}",
                "snippet": section[:600],
                "link": base_url,
                "source": "DuckDuckGo",
            }
        )

    if not items and raw.strip():
        items.append(
            {
                "title": f"Search results — {query[:60]}",
                "snippet": raw.strip()[:600],
                "link": base_url,
                "source": "DuckDuckGo",
            }
        )

    logger.info("search_news: returned %d items for query '%s'", len(items), query)
    return items


# ---------------------------------------------------------------------------
# 2. fetch_full_article
# ---------------------------------------------------------------------------

@tool
def fetch_full_article(url: str) -> str:
    """
    Attempt to fetch the full text of an article given its URL.

    WHEN TO USE:
        Only when the snippet is ambiguous or a high-severity problem needs deeper
        evidence. Gated by the ENABLE_FULL_ARTICLE_FETCH feature flag in the agent.

    WHEN NOT TO USE:
        • Do NOT call for every article — it is slow and may be rate-limited.
        • Do NOT call for non-HTML URLs (PDFs, paywalled sites).

    INPUTS:
        url — full HTTP/HTTPS URL of the article

    OUTPUT:
        Plain-text content (up to 4 000 chars) or an error message string.

    EDGE CASES:
        • Paywalled sites return their login page text.
        • Timeout after 10 s; returns error string so the caller can continue.
    """
    import urllib.request

    url = _sanitize(url, 500)
    if not url.startswith(("http://", "https://")):
        return "ERROR: invalid URL scheme — only http/https are supported"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; psgen-bot/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read(1_000_000).decode("utf-8", errors="ignore")

        # Very light HTML stripping — remove tags, collapse whitespace
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:4_000]

    except Exception as exc:
        logger.warning("fetch_full_article: failed to fetch %s — %s", url, exc)
        return f"ERROR: could not fetch article ({exc})"


# ---------------------------------------------------------------------------
# 3. extract_problems  (uses .with_structured_output via caller)
# ---------------------------------------------------------------------------

@tool
def extract_problems_tool(news_items: List[dict], context: str) -> List[dict]:
    """
    Identify and structure distinct societal problems from a list of news snippets.

    NOTE: This tool formats the prompt; the LLM call with structured output is
          performed by the agent node (problem_extractor_chain) so the caller
          gets validated Problem objects without manual JSON parsing.

    WHEN TO USE:
        After search_news returns results, before generate_solutions_tool.

    WHEN NOT TO USE:
        • Do NOT call with empty news_items — return [] immediately.
        • Do NOT call more than once for the same batch; deduplication is built-in.

    INPUTS:
        news_items — list of dicts (title, snippet, link, source)
        context    — location or topic string for grounding the extraction

    OUTPUT:
        List of dicts conforming to the Problem schema:
        { description, affected_people, severity, location, evidence }

    EDGE CASES:
        • If all snippets are unrelated to problems, returns [].
        • Severity is always normalised to lowercase by the Problem validator.
    """
    context = _sanitize(context, 200)
    if not news_items:
        return []

    # This function is used for its docstring / metadata by the agent;
    # actual LLM invocation happens via the chain in agent/graph.py.
    # Returning the raw items here allows the agent to pass them to the chain.
    return news_items


# ---------------------------------------------------------------------------
# 4. generate_solutions_tool
# ---------------------------------------------------------------------------

@tool
def generate_solutions_tool(problems: List[dict]) -> List[dict]:
    """
    Generate realistic, step-based solutions for a list of problems.

    NOTE: Actual LLM invocation uses .with_structured_output(Solution) inside
          the agent node; this tool provides metadata and docstring context.

    WHEN TO USE:
        After problems have been extracted and ranked.

    WHEN NOT TO USE:
        • Do NOT call with problems that have severity="low" unless explicitly
          requested — the agent skips low-severity by default.

    INPUTS:
        problems — list of dicts conforming to the Problem schema

    OUTPUT:
        List of dicts conforming to the Solution schema:
        { necessity, difficulty, implementation_steps, estimated_impact,
          estimated_cost, critique }

    EDGE CASES:
        • If a problem description is too vague, the solution will be generic;
          the critic node will flag this with a low realism_score.
    """
    if not problems:
        return []
    return problems  # Passed through; LLM chain runs in agent node.


# ---------------------------------------------------------------------------
# 5. critique_solution_tool
# ---------------------------------------------------------------------------

@tool
def critique_solution_tool(problem: dict, solution: dict) -> dict:
    """
    Critically evaluate a proposed solution against the problem it targets.

    NOTE: Actual LLM invocation uses .with_structured_output(Critique) inside
          the critic node; this tool provides schema context and routing logic.

    WHEN TO USE:
        • After generate_solutions_tool produces an initial solution.
        • The agent re-calls this after each regeneration (max 3 iterations).

    WHEN NOT TO USE:
        • Do NOT call when ENABLE_CRITIC=false.
        • Do NOT call when overall_score >= 7 on a previous critique (good enough).

    INPUTS:
        problem  — dict conforming to Problem schema
        solution — dict conforming to Solution schema

    OUTPUT:
        Dict conforming to Critique schema:
        { realism_score, feasibility_score, cost_effectiveness_score,
          unintended_consequences, improvement_suggestions,
          overall_score, reasoning }

    EDGE CASES:
        • Very brief solutions will score low on realism; the agent will
          regenerate with the improvement_suggestions injected into the prompt.
        • After 3 iterations the loop breaks regardless of score.
    """
    return {"problem": problem, "solution": solution}  # Passed through; LLM chain runs in node.

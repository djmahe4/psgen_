"""
LangGraph agentic workflow for the Problem Statement Generator.

Flow:
  planner → researcher → extractor → solver → critic
                                         ↑_________|  (if score < threshold)

Feature flags (read from env):
  ENABLE_AGENT_MODE          — use this graph instead of linear psgen.py
  ENABLE_CRITIC              — run the critic/regeneration loop
  ENABLE_RAG                 — inject past solutions from vector store
  ENABLE_FULL_ARTICLE_FETCH  — fetch full text for high-severity snippets

Observability:
  LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY  → LangSmith traces
"""
from __future__ import annotations

import logging
import os
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph, add_messages

from models import Critique, NewsItem, Problem, ProblemWithSolution, Solution
from tools import (
    critique_solution_tool,
    extract_problems_tool,
    fetch_full_article,
    generate_solutions_tool,
    search_news,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature flags
# ---------------------------------------------------------------------------
ENABLE_CRITIC = os.getenv("ENABLE_CRITIC", "true").lower() == "true"
ENABLE_RAG = os.getenv("ENABLE_RAG", "false").lower() == "true"
ENABLE_FULL_ARTICLE_FETCH = os.getenv("ENABLE_FULL_ARTICLE_FETCH", "false").lower() == "true"
CRITIC_SCORE_THRESHOLD = int(os.getenv("CRITIC_SCORE_THRESHOLD", "7"))
MAX_ITERATIONS = 3

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """Shared mutable state threaded through every graph node."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    location: str
    news_items: List[dict]
    problems: List[dict]
    solutions: List[dict]
    critiques: List[dict]
    iteration_count: int
    final_results: List[dict]
    reasoning_steps: List[str]  # surfaced in UI


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------

def _make_llm(api_key: str, temperature: float = 0.4) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-latest",
        google_api_key=api_key,
        temperature=temperature,
    )


# ---------------------------------------------------------------------------
# Node: planner
# ---------------------------------------------------------------------------

def planner_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Decide what the agent should do based on the incoming query.
    Adds a planning message to state and returns the enriched location string.
    """
    api_key: str = config["configurable"]["api_key"]
    llm = _make_llm(api_key).with_config(run_name="planner")

    system = SystemMessage(
        content=(
            "You are a planning assistant for a civic problem-analysis tool. "
            "Given the user query, extract:\n"
            "1. The primary location (city, country).\n"
            "2. A concise search query string for DuckDuckGo (max 15 words).\n"
            "Reply ONLY with JSON: {\"location\": \"...\", \"search_query\": \"...\"}"
        )
    )
    human = HumanMessage(content=state["query"])
    response = llm.invoke([system, human])

    import json, re

    raw = response.content.strip()
    # Strip markdown fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
    try:
        plan = json.loads(raw)
        location = plan.get("location", state["query"])
        search_query = plan.get("search_query", f"{location} problems issues")
    except Exception:
        location = state["query"]
        search_query = f"{location} problems issues"

    step = f"📌 Planner: location='{location}', query='{search_query}'"
    logger.info(step)

    return {
        "location": location,
        "query": search_query,
        "reasoning_steps": state.get("reasoning_steps", []) + [step],
        "messages": [AIMessage(content=step)],
    }


# ---------------------------------------------------------------------------
# Node: researcher
# ---------------------------------------------------------------------------

def researcher_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Search DuckDuckGo for news and optionally fetch full articles."""
    location = state["location"]
    query = state["query"]
    api_key: str = config["configurable"]["api_key"]
    max_results: int = config["configurable"].get("max_results", 10)

    # Parallel sub-queries (query expansion)
    sub_queries = [
        f"{location} problems issues 2025",
        f"{location} crisis latest news",
        query,
    ]

    all_items: List[dict] = []
    seen_snippets: set = set()

    for sq in sub_queries:
        results = search_news.invoke({"query": sq, "max_results": max_results // 2 + 1})
        for item in results:
            key = item.get("snippet", "")[:80]
            if key not in seen_snippets:
                seen_snippets.add(key)
                all_items.append(item)

    # Optional full-article fetch for snippets containing severity keywords
    if ENABLE_FULL_ARTICLE_FETCH:
        high_sev_keywords = {"death", "casualty", "collapse", "outbreak", "flood", "disaster"}
        for item in all_items:
            snippet_lower = item.get("snippet", "").lower()
            if any(kw in snippet_lower for kw in high_sev_keywords):
                full_text = fetch_full_article.invoke({"url": item.get("link", "")})
                if not full_text.startswith("ERROR"):
                    item["snippet"] = full_text[:800]

    step = f"🔍 Researcher: fetched {len(all_items)} news items for '{location}'"
    logger.info(step)

    return {
        "news_items": all_items[:max_results],
        "reasoning_steps": state.get("reasoning_steps", []) + [step],
        "messages": [AIMessage(content=step)],
    }


# ---------------------------------------------------------------------------
# Node: extractor
# ---------------------------------------------------------------------------

def extractor_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Extract and rank problems from news items using structured LLM output."""
    api_key: str = config["configurable"]["api_key"]
    news_items = state["news_items"]
    location = state["location"]

    if not news_items:
        step = "⚠️ Extractor: no news items to process"
        return {
            "problems": [],
            "reasoning_steps": state.get("reasoning_steps", []) + [step],
            "messages": [AIMessage(content=step)],
        }

    llm = _make_llm(api_key, temperature=0.3).with_config(run_name="extractor")
    structured_llm = llm.with_structured_output(Problem)

    # Build condensed news text
    news_text = "\n\n".join(
        f"[{i+1}] {it.get('title','')}\n{it.get('snippet','')[:400]}"
        for i, it in enumerate(news_items)
    )

    # RAG injection
    rag_context = ""
    if ENABLE_RAG:
        try:
            from memory.store import retrieve_similar_problems
            past = retrieve_similar_problems(location, k=3)
            if past:
                rag_context = "\n\nPreviously identified similar problems:\n" + "\n".join(
                    f"- {p}" for p in past
                )
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)

    system_prompt = (
        "You are a civic analyst. Extract distinct societal problems from the "
        "news below. For each problem fill ALL fields: description (≤200 chars, "
        "specific), affected_people (realistic integer), severity "
        "(low/medium/high/critical), location, evidence (direct quote or "
        "headline). Focus on the most impactful problems first."
        + rag_context
    )

    few_shot_examples = [
        {
            "news": "Chennai floods displace 200,000 residents after 3 days of heavy rain.",
            "problem": {
                "description": "Seasonal flooding displacing hundreds of thousands of Chennai residents",
                "affected_people": 200000,
                "severity": "critical",
                "location": "Chennai, Tamil Nadu",
                "evidence": "Chennai floods displace 200,000 residents",
            },
        }
    ]

    examples_text = "\n".join(
        f"Example {i+1}:\nNews: {e['news']}\nOutput: {e['problem']}"
        for i, e in enumerate(few_shot_examples)
    )

    full_prompt = (
        f"{system_prompt}\n\n{examples_text}\n\n"
        f"Now process these articles from {location}:\n{news_text}\n\n"
        "List each distinct problem as a separate JSON object matching the "
        "Problem schema. Return them as a JSON array."
    )

    import json as _json

    try:
        # Use raw LLM here to get a list (structured_output works per item)
        raw_llm = _make_llm(api_key, temperature=0.3).with_config(run_name="extractor")
        response = raw_llm.invoke(full_prompt)
        raw_text = response.content.strip()

        # Strip markdown fences
        import re
        raw_text = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`")

        # Parse
        data = _json.loads(raw_text)
        if isinstance(data, dict):
            data = [data]

        problems = []
        seen_descs: set = set()
        for item in data:
            try:
                p = Problem(**item)
                # Dedup by truncated description
                key = p.description[:60]
                if key not in seen_descs:
                    seen_descs.add(key)
                    problems.append(p.model_dump())
            except Exception as ve:
                logger.warning("extractor: validation error — %s", ve)

        # Sort by affected_people descending
        problems.sort(key=lambda x: x.get("affected_people", 0), reverse=True)

        # Store in RAG
        if ENABLE_RAG:
            try:
                from memory.store import store_problems
                store_problems(location, [p["description"] for p in problems])
            except Exception as exc:
                logger.warning("RAG store failed: %s", exc)

        step = f"🧩 Extractor: found {len(problems)} problems in '{location}'"
        logger.info(step)
    except Exception as exc:
        logger.error("extractor_node error: %s", exc)
        problems = []
        step = f"⚠️ Extractor: failed to extract problems — {exc}"

    return {
        "problems": problems,
        "reasoning_steps": state.get("reasoning_steps", []) + [step],
        "messages": [AIMessage(content=step)],
    }


# ---------------------------------------------------------------------------
# Node: solver
# ---------------------------------------------------------------------------

def solver_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Generate solutions for each problem, injecting critique feedback when available."""
    api_key: str = config["configurable"]["api_key"]
    problems = state["problems"]
    critiques = state.get("critiques", [])
    iteration = state.get("iteration_count", 0)

    if not problems:
        step = "⚠️ Solver: no problems to solve"
        return {
            "solutions": [],
            "reasoning_steps": state.get("reasoning_steps", []) + [step],
            "messages": [AIMessage(content=step)],
        }

    raw_llm = _make_llm(api_key, temperature=0.5).with_config(run_name=f"solver-iter-{iteration}")

    import json as _json, re

    solutions: List[dict] = []

    for i, prob in enumerate(problems):
        # Build improvement context from previous critique
        improvement_ctx = ""
        if critiques and i < len(critiques):
            crit = critiques[i]
            suggestions = crit.get("improvement_suggestions", [])
            if suggestions:
                improvement_ctx = (
                    "\n\nPrevious critique score: "
                    + str(crit.get("overall_score", "?"))
                    + "/10. Please address these improvements:\n"
                    + "\n".join(f"- {s}" for s in suggestions)
                )

        prompt = (
            f"Generate a practical solution for this civic problem.\n\n"
            f"Problem: {prob.get('description')}\n"
            f"Location: {prob.get('location')}\n"
            f"Affected people: {prob.get('affected_people'):,}\n"
            f"Severity: {prob.get('severity')}\n"
            f"{improvement_ctx}\n\n"
            "Return a JSON object with keys:\n"
            "  necessity (string), difficulty (easy/medium/hard),\n"
            "  implementation_steps (list of strings, ≥3 concrete steps),\n"
            "  estimated_impact (string), estimated_cost (string)\n"
            "No markdown fences — pure JSON only."
        )

        try:
            response = raw_llm.invoke(prompt)
            raw_text = response.content.strip()
            raw_text = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`")
            sol_data = _json.loads(raw_text)
            sol = Solution(**sol_data)
            solutions.append(sol.model_dump())
        except Exception as exc:
            logger.warning("solver_node: problem %d failed — %s", i, exc)
            solutions.append(
                Solution(
                    necessity="Unable to generate solution",
                    difficulty="medium",
                    implementation_steps=["Consult local authorities", "Gather more data"],
                    estimated_impact="Unknown",
                ).model_dump()
            )

    step = f"💡 Solver (iter {iteration}): generated {len(solutions)} solutions"
    logger.info(step)

    return {
        "solutions": solutions,
        "iteration_count": iteration + 1,
        "reasoning_steps": state.get("reasoning_steps", []) + [step],
        "messages": [AIMessage(content=step)],
    }


# ---------------------------------------------------------------------------
# Node: critic
# ---------------------------------------------------------------------------

def critic_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Score each solution; flag low-scoring ones for regeneration."""
    if not ENABLE_CRITIC:
        return {"critiques": [], "reasoning_steps": state.get("reasoning_steps", [])}

    api_key: str = config["configurable"]["api_key"]
    problems = state["problems"]
    solutions = state["solutions"]

    import json as _json, re

    raw_llm = _make_llm(api_key, temperature=0.2).with_config(run_name="critic")
    critiques: List[dict] = []

    for i, (prob, sol) in enumerate(zip(problems, solutions)):
        prompt = (
            f"Critically evaluate this civic solution:\n\n"
            f"PROBLEM: {prob.get('description')} ({prob.get('location')})\n"
            f"Affected: {prob.get('affected_people'):,}, Severity: {prob.get('severity')}\n\n"
            f"SOLUTION:\n"
            f"  Necessity: {sol.get('necessity')}\n"
            f"  Difficulty: {sol.get('difficulty')}\n"
            f"  Steps: {sol.get('implementation_steps')}\n"
            f"  Impact: {sol.get('estimated_impact')}\n"
            f"  Cost: {sol.get('estimated_cost')}\n\n"
            "Return a JSON object with keys:\n"
            "  realism_score (1-10), feasibility_score (1-10),\n"
            "  cost_effectiveness_score (1-10),\n"
            "  unintended_consequences (list of strings),\n"
            "  improvement_suggestions (list of strings),\n"
            "  overall_score (1-10), reasoning (string ≥50 words)\n"
            "Be honest and critical. No markdown fences."
        )

        try:
            response = raw_llm.invoke(prompt)
            raw_text = response.content.strip()
            raw_text = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`")
            crit_data = _json.loads(raw_text)
            crit = Critique(**crit_data)
            critiques.append(crit.model_dump())
        except Exception as exc:
            logger.warning("critic_node: solution %d failed — %s", i, exc)
            critiques.append(
                Critique(
                    realism_score=5,
                    feasibility_score=5,
                    cost_effectiveness_score=5,
                    overall_score=5,
                    reasoning="Critique generation failed; using default scores.",
                ).model_dump()
            )

    # Attach critiques to solutions
    for i, sol in enumerate(solutions):
        if i < len(critiques):
            sol["critique"] = critiques[i]

    avg_score = (
        sum(c.get("overall_score", 5) for c in critiques) / len(critiques)
        if critiques
        else 5
    )
    step = (
        f"🔎 Critic (iter {state.get('iteration_count', 0)}): "
        f"avg score {avg_score:.1f}/10"
    )
    logger.info(step)

    return {
        "critiques": critiques,
        "solutions": solutions,
        "reasoning_steps": state.get("reasoning_steps", []) + [step],
        "messages": [AIMessage(content=step)],
    }


# ---------------------------------------------------------------------------
# Node: formatter
# ---------------------------------------------------------------------------

def formatter_node(state: AgentState, _config: RunnableConfig) -> Dict[str, Any]:
    """Combine problems + solutions into final ProblemWithSolution list."""
    problems = state.get("problems", [])
    solutions = state.get("solutions", [])

    final: List[dict] = []
    for i, prob in enumerate(problems):
        sol_data = solutions[i] if i < len(solutions) else None
        try:
            p = Problem(**prob)
            s = Solution(**sol_data) if sol_data else None
        except Exception as exc:
            logger.warning("formatter_node: validation error — %s", exc)
            continue

        pws = ProblemWithSolution(
            problem=p,
            solution=s,
            iteration=state.get("iteration_count", 0),
        )
        final.append(pws.model_dump())

    step = f"✅ Formatter: packaged {len(final)} results"
    return {
        "final_results": final,
        "reasoning_steps": state.get("reasoning_steps", []) + [step],
        "messages": [AIMessage(content=step)],
    }


# ---------------------------------------------------------------------------
# Edge conditions
# ---------------------------------------------------------------------------

def _should_regenerate(state: AgentState) -> str:
    """Return 'solver' if critic scores are below threshold, else 'formatter'."""
    if not ENABLE_CRITIC:
        return "formatter"

    iteration = state.get("iteration_count", 0)
    if iteration >= MAX_ITERATIONS:
        return "formatter"

    critiques = state.get("critiques", [])
    if not critiques:
        return "formatter"

    avg = sum(c.get("overall_score", 10) for c in critiques) / len(critiques)
    return "solver" if avg < CRITIC_SCORE_THRESHOLD else "formatter"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Assemble the LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("extractor", extractor_node)
    graph.add_node("solver", solver_node)
    graph.add_node("critic", critic_node)
    graph.add_node("formatter", formatter_node)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "extractor")
    graph.add_edge("extractor", "solver")
    graph.add_edge("solver", "critic")
    graph.add_conditional_edges(
        "critic",
        _should_regenerate,
        {"solver": "solver", "formatter": "formatter"},
    )
    graph.add_edge("formatter", END)

    return graph


def compile_graph():
    """Return a compiled runnable graph."""
    return build_graph().compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_agent(
    query: str,
    api_key: str,
    max_results: int = 10,
) -> Dict[str, Any]:
    """
    Run the full agentic pipeline for a user query.

    Returns a dict with keys:
        final_results   — List[ProblemWithSolution as dict]
        reasoning_steps — List[str] (for UI display)
        messages        — conversation history
    """
    graph = compile_graph()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "query": query,
        "location": "",
        "news_items": [],
        "problems": [],
        "solutions": [],
        "critiques": [],
        "iteration_count": 0,
        "final_results": [],
        "reasoning_steps": [],
    }

    config = RunnableConfig(
        configurable={"api_key": api_key, "max_results": max_results},
        run_name="psgen-agent",
    )

    final_state = graph.invoke(initial_state, config=config)
    return {
        "final_results": final_state.get("final_results", []),
        "reasoning_steps": final_state.get("reasoning_steps", []),
        "messages": final_state.get("messages", []),
    }

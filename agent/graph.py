"""
LangGraph agentic workflow for the Problem Statement Generator — Step 5.

Architecture
============
    START → researcher → extractor → solver → critic → planner
                                                  ↑          │
                               "regenerate" ──────┘          │ "finish"
                                                             ↓
                                                        formatter → END

Design decisions
----------------
* All LLM calls use LCEL chains with ``.with_structured_output()`` — zero
  manual JSON parsing anywhere in this file.
* ``ProblemList`` / ``SolutionList`` wrappers allow a single LLM call to
  return a typed list of structured objects.
* ``planner_node`` is a pure Python function (no LLM) — it reads critique
  scores from state and sets ``next_step`` for the conditional edge.
* ``run_agentic_workflow()`` is the single public entry point.
* Feature flags are read once at import time from environment variables.
* LangSmith tracing is enabled automatically when
  ``LANGCHAIN_TRACING_V2=true`` and ``LANGCHAIN_API_KEY`` are set.

Feature flags (set in .env)
----------------------------
  ENABLE_CRITIC              — run the critic/regeneration loop (default: true)
  ENABLE_RAG                 — inject past solutions from vector store (default: false)
  ENABLE_FULL_ARTICLE_FETCH  — fetch full article text for severe snippets (default: false)
  CRITIC_SCORE_THRESHOLD     — minimum acceptable avg critic score (default: 7)
  MAX_ITERATIONS             — hard cap on solver→critic loops (default: 3)
"""
from __future__ import annotations

import logging
import os
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from models import Critique, Problem, ProblemWithSolution, Solution
from tools import fetch_full_article, search_news

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature flags — read once at import time
# ---------------------------------------------------------------------------
ENABLE_CRITIC: bool = os.getenv("ENABLE_CRITIC", "true").lower() == "true"
ENABLE_RAG: bool = os.getenv("ENABLE_RAG", "false").lower() == "true"
ENABLE_FULL_ARTICLE_FETCH: bool = (
    os.getenv("ENABLE_FULL_ARTICLE_FETCH", "false").lower() == "true"
)
CRITIC_SCORE_THRESHOLD: int = int(os.getenv("CRITIC_SCORE_THRESHOLD", "7"))
MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "3"))

# ---------------------------------------------------------------------------
# Pydantic wrappers for structured list outputs
# ---------------------------------------------------------------------------


class ProblemList(BaseModel):
    """
    Wrapper that lets a single ``.with_structured_output()`` call return
    multiple validated ``Problem`` objects without any manual JSON parsing.
    """

    problems: List[Problem] = Field(
        default_factory=list,
        description=(
            "All distinct societal problems identified from the news batch, "
            "sorted by affected_people descending."
        ),
    )


class SolutionList(BaseModel):
    """
    Wrapper that lets a single ``.with_structured_output()`` call return
    one validated ``Solution`` per problem, preserving order.
    """

    solutions: List[Solution] = Field(
        default_factory=list,
        description=(
            "One solution per input problem, returned in the same order "
            "as the problems list."
        ),
    )


# ---------------------------------------------------------------------------
# Typed agent state
# ---------------------------------------------------------------------------


class AgentState(TypedDict):
    """
    Shared mutable state passed through every graph node.

    Fields
    ------
    messages        Append-only conversation history (LangGraph managed).
    query           The original user query string.
    context         Optional enriched context (e.g. map-selected location).
                    Falls back to ``query`` when not provided.
    news_items      Raw news article dicts from the researcher node.
    problems        Validated ``Problem`` dicts from the extractor node.
    solutions       Validated ``Solution`` dicts from the solver node.
    critiques       Validated ``Critique`` dicts from the critic node.
    iteration_count Number of completed solver→critic cycles.
    final_output    Assembled result dict produced by the formatter node.
    next_step       Routing signal set by planner_node: "regenerate" | "finish".
    """

    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    context: Optional[str]
    news_items: List[dict]
    problems: List[dict]
    solutions: List[dict]
    critiques: List[dict]
    iteration_count: int
    final_output: Optional[dict]
    next_step: str  # "regenerate" | "finish"


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------


def _make_llm(api_key: str, temperature: float = 0.4) -> ChatGoogleGenerativeAI:
    """
    Instantiate ChatGoogleGenerativeAI with Gemini 2.5 Flash.

    LangSmith tracing is activated automatically when the environment
    variables ``LANGCHAIN_TRACING_V2=true`` and ``LANGCHAIN_API_KEY`` are set.
    """
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-latest",
        google_api_key=api_key,
        temperature=temperature,
    )


# ---------------------------------------------------------------------------
# LCEL chain builders
# ---------------------------------------------------------------------------


def _extractor_chain(llm: ChatGoogleGenerativeAI):
    """
    LCEL chain: ChatPromptTemplate | llm.with_structured_output(ProblemList)

    Uses ``.with_structured_output()`` — no JSON parsing, no regex, no try/except
    around raw text.  Gemini returns a validated ``ProblemList`` directly.

    Template variables: ``context``, ``news_text``
    """
    system = (
        "You are a civic analyst. Extract ALL distinct societal problems from "
        "the news articles below.\n\n"
        "Rules:\n"
        "- description: ≤200 chars, specific noun phrase (root cause, not symptom)\n"
        "- affected_people: realistic integer ≥0 (use population tiers when unknown)\n"
        "- severity: exactly one of low / medium / high / critical\n"
        "- location: most specific geographic unit mentioned\n"
        "- evidence: direct quote or headline fragment (omit if unavailable)\n"
        "- Deduplicate: never include the same root cause twice\n"
        "- Sort by affected_people descending\n\n"
        "Few-shot example:\n"
        "Input: 'Chennai floods displace 200,000 residents after 3 days of rain.'\n"
        "Output problem: description='Seasonal flooding displacing hundreds of thousands "
        "of Chennai residents', affected_people=200000, severity='critical', "
        "location='Chennai, Tamil Nadu', evidence='floods displace 200,000 residents'"
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Location/context: {context}\n\nNews articles:\n{news_text}"),
        ]
    )
    return (prompt | llm.with_structured_output(ProblemList)).with_config(
        run_name="extractor-chain"
    )


def _solver_chain(llm: ChatGoogleGenerativeAI):
    """
    LCEL chain: ChatPromptTemplate | llm.with_structured_output(SolutionList)

    Accepts an optional ``improvement_context`` block injected by the solver
    node when iterating after a low critic score.

    Template variables: ``problems_text``, ``improvement_context``
    """
    system = (
        "You are a civic solutions expert. Generate ONE realistic, step-based "
        "solution for EACH problem listed below.\n\n"
        "Rules per solution:\n"
        "- necessity: why urgent; what happens without intervention\n"
        "- difficulty: exactly one of easy / medium / hard\n"
        "- implementation_steps: ≥3 ordered steps, each starting with an imperative "
        "verb naming the responsible actor\n"
        "- estimated_impact: quantified or clearly qualified outcome\n"
        "- estimated_cost: rough range with currency (null if genuinely unknown)\n"
        "- Return solutions in the SAME ORDER as the input problems\n"
        "- Include a short-term action (≤30 days) in step 1\n\n"
        "{improvement_context}"
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Problems to solve:\n{problems_text}"),
        ]
    )
    return (prompt | llm.with_structured_output(SolutionList)).with_config(
        run_name="solver-chain"
    )


def _critic_chain(llm: ChatGoogleGenerativeAI):
    """
    LCEL chain: ChatPromptTemplate | llm.with_structured_output(Critique)

    Called once per (problem, solution) pair.

    Template variables: ``problem_text``, ``solution_text``
    """
    system = (
        "You are an independent policy critic. Evaluate the solution strictly "
        "and honestly — avoid sycophancy.\n\n"
        "Score each dimension 1–10 (5 = neutral / unverified):\n"
        "  realism_score          — proven in comparable real-world contexts?\n"
        "  feasibility_score      — resources, governance, and capacity available locally?\n"
        "  cost_effectiveness_score — benefit proportional to cost and effort?\n\n"
        "overall_score = round((realism + feasibility + cost_effectiveness) / 3)\n\n"
        "Also provide:\n"
        "  unintended_consequences — ≥1 concrete risk or side-effect\n"
        "  improvement_suggestions — ≥1 specific, actionable fix\n"
        "  reasoning               — ≥50 words explaining all scores\n\n"
        "Calibration anchors (realism):\n"
        "  10 = proven in multiple comparable contexts\n"
        "   5 = theoretically sound, limited real-world evidence\n"
        "   1 = relies on technology or capacity that does not exist"
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "PROBLEM:\n{problem_text}\n\nSOLUTION:\n{solution_text}",
            ),
        ]
    )
    return (prompt | llm.with_structured_output(Critique)).with_config(
        run_name="critic-chain"
    )


# ---------------------------------------------------------------------------
# Node: researcher
# ---------------------------------------------------------------------------


def researcher_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Fetch recent news for the query using three expanded sub-queries via
    the ``search_news`` tool from ``tools.py``.

    Optionally calls ``fetch_full_article`` for snippets that contain
    high-severity keywords when ``ENABLE_FULL_ARTICLE_FETCH=true``.

    Reads from state : query, context
    Writes to state  : news_items, messages
    """
    from psgen import sanitize_input  # local import to avoid circular at module level

    api_key: str = config["configurable"]["api_key"]
    max_results: int = int(config["configurable"].get("max_results", 10))

    raw_query = state["query"]
    raw_context = state.get("context") or raw_query

    query = sanitize_input(raw_query, 200)
    context = sanitize_input(raw_context, 200)

    # Query expansion: three complementary sub-queries
    sub_queries: List[str] = [
        f"{context} problems issues 2025",
        f"{context} crisis latest news",
        query,
    ]

    seen_keys: set = set()
    all_items: List[dict] = []
    fetch_per_query = max(1, max_results // 2)

    for sq in sub_queries:
        results: List[dict] = search_news.invoke(
            {"query": sq, "max_results": fetch_per_query}
        )
        for item in results:
            # Deduplicate by first-80-char snippet fingerprint
            key = (item.get("snippet") or "")[:80].strip().lower()
            if key and key not in seen_keys:
                seen_keys.add(key)
                all_items.append(item)

    # Optional full-article fetch for high-severity snippets
    if ENABLE_FULL_ARTICLE_FETCH:
        high_sev_kw = {
            "death", "casualty", "collapse", "outbreak",
            "flood", "disaster", "fatality", "emergency",
        }
        for item in all_items:
            snippet_lower = (item.get("snippet") or "").lower()
            if any(kw in snippet_lower for kw in high_sev_kw):
                full_text: str = fetch_full_article.invoke(
                    {"url": item.get("link", "")}
                )
                if not full_text.startswith("ERROR"):
                    item["snippet"] = full_text[:800]

    trimmed = all_items[:max_results]
    msg = AIMessage(
        content=f"🔍 Researcher: fetched {len(trimmed)} articles for '{context}'"
    )
    logger.info(msg.content)

    return {"news_items": trimmed, "messages": [msg]}


# ---------------------------------------------------------------------------
# Node: extractor
# ---------------------------------------------------------------------------


def extractor_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Extract and rank societal problems from ``news_items`` using the
    ``_extractor_chain`` LCEL chain with ``.with_structured_output(ProblemList)``.

    No manual JSON parsing — Pydantic validation happens inside the chain.

    Reads from state : news_items, context, query
    Writes to state  : problems, messages
    """
    api_key: str = config["configurable"]["api_key"]
    news_items: List[dict] = state["news_items"]
    context: str = state.get("context") or state["query"]

    if not news_items:
        msg = AIMessage(content="⚠️ Extractor: no news items to process")
        return {"problems": [], "messages": [msg]}

    # Build condensed news text (cap each snippet to avoid token overflow)
    news_text = "\n\n".join(
        f"[{i + 1}] {it.get('title', '')}\n{(it.get('snippet') or '')[:500]}"
        for i, it in enumerate(news_items)
    )

    llm = _make_llm(api_key, temperature=0.3)
    chain = _extractor_chain(llm)

    # RAG hook: inject past problems for deduplication (when enabled)
    rag_hint = ""
    if ENABLE_RAG:
        try:
            from memory.store import retrieve_similar_problems  # type: ignore

            past = retrieve_similar_problems(context, k=3)
            if past:
                rag_hint = "\n\nPreviously seen problems (avoid duplicating):\n" + "\n".join(
                    f"- {p}" for p in past
                )
        except Exception as exc:
            logger.debug("RAG retrieval skipped: %s", exc)

    try:
        result: ProblemList = chain.invoke(
            {"context": context + rag_hint, "news_text": news_text}
        )
        problems: List[dict] = [p.model_dump() for p in result.problems]
        # Ensure sorted by impact (extractor prompt requests this, but enforce it)
        problems.sort(key=lambda x: x.get("affected_people", 0), reverse=True)
    except Exception as exc:
        logger.error("extractor_node: chain failed — %s", exc, exc_info=True)
        problems = []

    # RAG hook: store new problems for future sessions
    if ENABLE_RAG and problems:
        try:
            from memory.store import store_problems  # type: ignore

            store_problems(context, [p["description"] for p in problems])
        except Exception as exc:
            logger.debug("RAG store skipped: %s", exc)

    msg = AIMessage(content=f"🧩 Extractor: found {len(problems)} problems")
    logger.info(msg.content)

    return {"problems": problems, "messages": [msg]}


# ---------------------------------------------------------------------------
# Node: solver
# ---------------------------------------------------------------------------


def solver_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Generate one ``Solution`` per extracted problem using the ``_solver_chain``
    LCEL chain with ``.with_structured_output(SolutionList)``.

    When iterating after a low critic score, injects the critic's
    ``improvement_suggestions`` into the prompt via ``improvement_context``.

    No manual JSON parsing — Pydantic validation happens inside the chain.

    Reads from state : problems, critiques, iteration_count
    Writes to state  : solutions, iteration_count, messages
    """
    api_key: str = config["configurable"]["api_key"]
    problems: List[dict] = state["problems"]
    critiques: List[dict] = state.get("critiques", [])
    iteration: int = state.get("iteration_count", 0)

    if not problems:
        msg = AIMessage(content="⚠️ Solver: no problems to solve")
        return {"solutions": [], "messages": [msg]}

    # Build improvement context from previous critiques (if any)
    improvement_lines: List[str] = []
    for i, crit in enumerate(critiques):
        suggestions: List[str] = crit.get("improvement_suggestions", [])
        score: int = crit.get("overall_score", 10)
        if suggestions:
            improvement_lines.append(
                f"Problem {i + 1} — previous critique score: {score}/10. "
                f"You MUST address: {'; '.join(suggestions)}"
            )

    improvement_context: str = (
        "PREVIOUS CRITIQUE FEEDBACK — address every point below:\n"
        + "\n".join(improvement_lines)
        if improvement_lines
        else ""
    )

    problems_text = "\n\n".join(
        "Problem {n}:\n"
        "  Description : {desc}\n"
        "  Location    : {loc}\n"
        "  Affected    : {aff:,}\n"
        "  Severity    : {sev}".format(
            n=i + 1,
            desc=p.get("description", ""),
            loc=p.get("location", ""),
            aff=p.get("affected_people", 0),
            sev=p.get("severity", ""),
        )
        for i, p in enumerate(problems)
    )

    llm = _make_llm(api_key, temperature=0.5)
    chain = _solver_chain(llm)

    _fallback_solution = Solution(
        necessity="Unable to generate solution — please retry.",
        difficulty="medium",
        implementation_steps=[
            "Consult local authorities to scope the problem.",
            "Commission a rapid needs assessment.",
            "Identify and engage relevant stakeholders.",
        ],
        estimated_impact="Unknown — assessment needed.",
    )

    try:
        result: SolutionList = chain.invoke(
            {
                "improvement_context": improvement_context,
                "problems_text": problems_text,
            }
        )
        solutions: List[dict] = [s.model_dump() for s in result.solutions]

        # Pad with fallbacks if the LLM returned fewer solutions than problems
        while len(solutions) < len(problems):
            solutions.append(_fallback_solution.model_dump())

    except Exception as exc:
        logger.error("solver_node: chain failed — %s", exc, exc_info=True)
        solutions = [_fallback_solution.model_dump() for _ in problems]

    msg = AIMessage(
        content=f"💡 Solver (iter {iteration}): generated {len(solutions)} solutions"
    )
    logger.info(msg.content)

    return {
        "solutions": solutions,
        "iteration_count": iteration + 1,
        "messages": [msg],
    }


# ---------------------------------------------------------------------------
# Node: critic
# ---------------------------------------------------------------------------


def critic_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Score every (problem, solution) pair using the ``_critic_chain`` LCEL
    chain with ``.with_structured_output(Critique)``.

    Attaches each ``Critique`` to its corresponding solution dict so the
    formatter can embed it in the final output.

    Skipped entirely (returns empty critiques) when ``ENABLE_CRITIC=false``.

    No manual JSON parsing — Pydantic validation happens inside the chain.

    Reads from state : problems, solutions, iteration_count
    Writes to state  : critiques, solutions (with critique attached), messages
    """
    if not ENABLE_CRITIC:
        return {"critiques": [], "messages": []}

    api_key: str = config["configurable"]["api_key"]
    problems: List[dict] = state["problems"]
    solutions: List[dict] = state["solutions"]
    iteration: int = state.get("iteration_count", 0)

    llm = _make_llm(api_key, temperature=0.2)
    chain = _critic_chain(llm)

    _fallback_critique = Critique(
        realism_score=5,
        feasibility_score=5,
        cost_effectiveness_score=5,
        overall_score=5,
        reasoning="Critique generation failed; default neutral scores assigned.",
    )

    critiques: List[dict] = []

    for prob, sol in zip(problems, solutions):
        problem_text = (
            f"Description : {prob.get('description', '')}\n"
            f"Location    : {prob.get('location', '')}\n"
            f"Affected    : {prob.get('affected_people', 0):,}\n"
            f"Severity    : {prob.get('severity', '')}"
        )
        solution_text = (
            f"Necessity   : {sol.get('necessity', '')}\n"
            f"Difficulty  : {sol.get('difficulty', '')}\n"
            f"Steps       : {sol.get('implementation_steps', [])}\n"
            f"Impact      : {sol.get('estimated_impact', '')}\n"
            f"Cost        : {sol.get('estimated_cost', 'N/A')}"
        )
        try:
            crit: Critique = chain.invoke(
                {"problem_text": problem_text, "solution_text": solution_text}
            )
            critiques.append(crit.model_dump())
        except Exception as exc:
            logger.warning("critic_node: critique failed for one pair — %s", exc)
            critiques.append(_fallback_critique.model_dump())

    # Attach each critique to its solution dict (in-place copy, not mutation)
    updated_solutions: List[dict] = []
    for i, sol in enumerate(solutions):
        updated = dict(sol)
        if i < len(critiques):
            updated["critique"] = critiques[i]
        updated_solutions.append(updated)

    avg: float = (
        sum(c.get("overall_score", 5) for c in critiques) / len(critiques)
        if critiques
        else 5.0
    )
    msg = AIMessage(
        content=(
            f"🔎 Critic (iter {iteration}): "
            f"{len(critiques)} critiques, avg score {avg:.1f}/10"
        )
    )
    logger.info(msg.content)

    return {
        "critiques": critiques,
        "solutions": updated_solutions,
        "messages": [msg],
    }


# ---------------------------------------------------------------------------
# Node: planner  (pure Python — no LLM call)
# ---------------------------------------------------------------------------


def planner_node(state: AgentState, _config: RunnableConfig) -> Dict[str, Any]:
    """
    Pure decision node — reads state and sets ``next_step``.

    No LLM is called.  All routing logic is deterministic:

    Decision tree
    -------------
    1. ``ENABLE_CRITIC`` is false  → "finish"
    2. No critiques in state       → "finish"
    3. ``iteration_count >= MAX_ITERATIONS`` → "finish" (hard cap)
    4. avg(overall_score) < CRITIC_SCORE_THRESHOLD → "regenerate"
    5. Otherwise → "finish"

    Reads from state : critiques, iteration_count
    Writes to state  : next_step, messages
    """
    iteration: int = state.get("iteration_count", 0)
    critiques: List[dict] = state.get("critiques", [])

    if not ENABLE_CRITIC or not critiques:
        decision = "finish"
        reason = "critic disabled or no critiques"
    elif iteration >= MAX_ITERATIONS:
        decision = "finish"
        reason = f"max iterations ({MAX_ITERATIONS}) reached"
    else:
        avg = sum(c.get("overall_score", 10) for c in critiques) / len(critiques)
        if avg < CRITIC_SCORE_THRESHOLD:
            decision = "regenerate"
            reason = f"avg score {avg:.1f} < threshold {CRITIC_SCORE_THRESHOLD}"
        else:
            decision = "finish"
            reason = f"avg score {avg:.1f} ≥ threshold {CRITIC_SCORE_THRESHOLD}"

    msg = AIMessage(
        content=f"📋 Planner (iter {iteration}): {decision} — {reason}"
    )
    logger.info(msg.content)

    return {"next_step": decision, "messages": [msg]}


# ---------------------------------------------------------------------------
# Node: formatter
# ---------------------------------------------------------------------------


def formatter_node(state: AgentState, _config: RunnableConfig) -> Dict[str, Any]:
    """
    Assemble the ``final_output`` dict from validated problems and solutions.

    Every pair is run through ``ProblemWithSolution`` Pydantic validation
    before serialisation, guaranteeing schema consistency.

    Reads from state : problems, solutions, critiques, iteration_count, context, query
    Writes to state  : final_output, messages
    """
    problems: List[dict] = state.get("problems", [])
    solutions: List[dict] = state.get("solutions", [])
    critiques: List[dict] = state.get("critiques", [])

    items: List[dict] = []
    for i, prob_data in enumerate(problems):
        sol_data: Optional[dict] = solutions[i] if i < len(solutions) else None
        try:
            # Validate through Pydantic — catches any schema drift
            pws = ProblemWithSolution(
                problem=Problem(**prob_data),
                solution=Solution(**sol_data) if sol_data else None,
                iteration=state.get("iteration_count", 0),
            )
            items.append(pws.model_dump())
        except Exception as exc:
            logger.warning("formatter_node: validation error at index %d — %s", i, exc)

    avg_score: Optional[float] = None
    if critiques:
        avg_score = round(
            sum(c.get("overall_score", 5) for c in critiques) / len(critiques), 1
        )

    # Collect the reasoning trace from all AIMessages in conversation history
    reasoning_trace: List[str] = [
        m.content
        for m in state.get("messages", [])
        if isinstance(m, AIMessage) and m.content
    ]

    final_output: dict = {
        "results": items,
        "summary": {
            "total_problems": len(items),
            "location": state.get("context") or state.get("query", ""),
            "iterations_used": state.get("iteration_count", 0),
            "average_critique_score": avg_score,
        },
        "reasoning_trace": reasoning_trace,
    }

    msg = AIMessage(
        content=f"✅ Formatter: packaged {len(items)} problem-solution pairs"
    )
    logger.info(msg.content)

    return {"final_output": final_output, "messages": [msg]}


# ---------------------------------------------------------------------------
# Conditional edge function
# ---------------------------------------------------------------------------


def _route_after_planner(state: AgentState) -> Literal["solver", "formatter"]:
    """
    Read ``next_step`` from state (set by ``planner_node``) and return the
    name of the next node for LangGraph's conditional edge.
    """
    return "solver" if state.get("next_step") == "regenerate" else "formatter"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    """
    Assemble the LangGraph ``StateGraph`` without compiling.

    Node map::

        START → researcher → extractor → solver → critic → planner
                                                               │
                                    "regenerate" ─────────────→ solver
                                    "finish"     ─────────────→ formatter → END

    Returns the un-compiled ``StateGraph`` so callers can optionally add
    custom middleware (e.g., ``MemorySaver``) before compiling.
    """
    g = StateGraph(AgentState)

    g.add_node("researcher", researcher_node)
    g.add_node("extractor", extractor_node)
    g.add_node("solver", solver_node)
    g.add_node("critic", critic_node)
    g.add_node("planner", planner_node)
    g.add_node("formatter", formatter_node)

    g.set_entry_point("researcher")

    g.add_edge("researcher", "extractor")
    g.add_edge("extractor", "solver")
    g.add_edge("solver", "critic")
    g.add_edge("critic", "planner")
    g.add_conditional_edges(
        "planner",
        _route_after_planner,
        {"solver": "solver", "formatter": "formatter"},
    )
    g.add_edge("formatter", END)

    return g


def compile_graph():
    """
    Build and compile the LangGraph instance.

    Returns a ``CompiledGraph`` ready for ``.invoke()`` or ``.stream()``.
    """
    return build_graph().compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_agentic_workflow(
    query: str,
    api_key: str,
    context: Optional[str] = None,
    max_results: int = 10,
) -> dict:
    """
    Execute the full agentic workflow for a user query.

    This is the single public entry point for the LangGraph pipeline.
    It sanitizes inputs, constructs the initial state, runs the compiled
    graph, and returns the structured final output.

    Parameters
    ----------
    query : str
        The user's search query — a location, topic, or natural-language
        question (e.g. "What problems are there in Chennai?").
    api_key : str
        Google Gemini API key.
    context : str, optional
        Enriched context string, e.g. the location name selected on the map.
        Falls back to ``query`` when not provided.
    max_results : int
        Maximum number of news articles to retrieve per run (default: 10).

    Returns
    -------
    dict
        Keys:
          ``results``         — ``List[ProblemWithSolution]`` as dicts
          ``summary``         — ``{total_problems, location, iterations_used,
                                   average_critique_score}``
          ``reasoning_trace`` — ``List[str]`` of node step messages for UI display
    """
    from psgen import sanitize_input  # local import — avoids circular at module level

    safe_query = sanitize_input(query or "", 200)
    safe_context = sanitize_input(context or "", 200) or None

    if not safe_query:
        return {
            "results": [],
            "summary": {
                "total_problems": 0,
                "location": "",
                "iterations_used": 0,
                "average_critique_score": None,
            },
            "reasoning_trace": ["❌ Query was empty after sanitization."],
        }

    initial_state: AgentState = {
        "messages": [HumanMessage(content=safe_query)],
        "query": safe_query,
        "context": safe_context or safe_query,
        "news_items": [],
        "problems": [],
        "solutions": [],
        "critiques": [],
        "iteration_count": 0,
        "final_output": None,
        "next_step": "finish",  # planner will overwrite this
    }

    run_config = RunnableConfig(
        configurable={"api_key": api_key, "max_results": max_results},
        run_name="psgen-agentic-workflow",
    )

    try:
        graph = compile_graph()
        final_state: AgentState = graph.invoke(initial_state, config=run_config)
    except Exception as exc:
        logger.error("run_agentic_workflow: graph invocation failed — %s", exc, exc_info=True)
        return {
            "results": [],
            "summary": {
                "total_problems": 0,
                "location": safe_context or safe_query,
                "iterations_used": 0,
                "average_critique_score": None,
            },
            "reasoning_trace": [f"❌ Workflow error: {exc}"],
        }

    output: dict = final_state.get("final_output") or {}
    return {
        "results": output.get("results", []),
        "summary": output.get(
            "summary",
            {
                "total_problems": 0,
                "location": safe_context or safe_query,
                "iterations_used": 0,
                "average_critique_score": None,
            },
        ),
        "reasoning_trace": output.get("reasoning_trace", []),
    }


"""
Pydantic v2 models for data validation and structured LLM outputs.
All models are fully JSON-serializable and optimized for .with_structured_output().
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class NewsItem(BaseModel):
    """A single news article retrieved from search."""

    title: str = Field(
        ...,
        description="Headline of the news article",
        examples=["City faces severe water shortage amid heatwave"],
    )
    snippet: str = Field(
        ...,
        description="Short summary / body excerpt of the article",
        examples=["Residents in the eastern district have been without running water for 72 hours..."],
    )
    link: str = Field(
        ...,
        description="URL pointing to the full article",
        examples=["https://example.com/article/water-shortage"],
    )
    source: Optional[str] = Field(
        None,
        description="Name of the publication or outlet",
        examples=["The Daily Tribune"],
    )


class Problem(BaseModel):
    """A societal problem extracted from news coverage."""

    description: str = Field(
        ...,
        description="Concise but specific description of the problem",
        examples=["Recurring flooding in low-income neighbourhoods due to inadequate storm drains"],
    )
    affected_people: int = Field(
        ...,
        description="Realistic estimate of the number of people directly impacted",
        ge=0,
        examples=[50_000],
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Impact severity: low / medium / high / critical",
        examples=["high"],
    )
    location: str = Field(
        ...,
        description="City, region, or area where the problem occurs",
        examples=["Mumbai, Maharashtra"],
    )
    evidence: Optional[str] = Field(
        None,
        description="Direct quote or headline that supports the problem claim",
        examples=["'Flooding leaves thousands homeless' — The Tribune, 2024-07-12"],
    )

    @field_validator("severity", mode="before")
    @classmethod
    def normalise_severity(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"severity must be one of {sorted(allowed)}, got '{v}'")
        return v


class Critique(BaseModel):
    """Quality assessment of a proposed solution produced by the critic node."""

    realism_score: int = Field(
        ...,
        description="How achievable the solution is given local context (1 = fantasy, 10 = proven elsewhere)",
        ge=1,
        le=10,
        examples=[7],
    )
    feasibility_score: int = Field(
        ...,
        description="Overall feasibility given budget, governance, and capacity constraints (1–10)",
        ge=1,
        le=10,
        examples=[6],
    )
    cost_effectiveness_score: int = Field(
        ...,
        description="Return on investment relative to effort and cost (1–10)",
        ge=1,
        le=10,
        examples=[8],
    )
    unintended_consequences: List[str] = Field(
        default_factory=list,
        description="Potential negative side-effects the solution might cause",
        examples=[["May displace informal vendors", "Could increase traffic congestion"]],
    )
    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="Concrete ways to make the solution stronger",
        examples=[["Add community consultation phase", "Pilot in one ward before scaling"]],
    )
    overall_score: int = Field(
        ...,
        description="Composite score averaging realism, feasibility, and cost-effectiveness (1–10)",
        ge=1,
        le=10,
        examples=[7],
    )
    reasoning: str = Field(
        ...,
        description="One-paragraph explanation of the scores",
        examples=["The plan is realistic but relies on sustained political will..."],
    )


class Solution(BaseModel):
    """Actionable solution for a problem, with critic-loop metadata."""

    necessity: str = Field(
        ...,
        description="Why this solution must be implemented and what happens if it is not",
        examples=["Without intervention, annual flood damage will exceed ₹200 Cr by 2027..."],
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(
        ...,
        description="Implementation difficulty: easy / medium / hard",
        examples=["medium"],
    )
    implementation_steps: List[str] = Field(
        ...,
        description="Ordered list of concrete steps to execute the solution",
        examples=[["Conduct topographic survey", "Tender for drain construction", "Community awareness campaign"]],
    )
    estimated_impact: str = Field(
        ...,
        description="Quantified or qualified expected outcome after implementation",
        examples=["Reduce flood-affected households by ~60 % within 18 months"],
    )
    estimated_cost: Optional[str] = Field(
        None,
        description="Rough cost range (include currency and time horizon where possible)",
        examples=["₹15–25 Cr over 24 months"],
    )
    critique: Optional[Critique] = Field(
        None,
        description="Populated after the critic node evaluates this solution",
    )

    @field_validator("difficulty", mode="before")
    @classmethod
    def normalise_difficulty(cls, v: str) -> str:
        allowed = {"easy", "medium", "hard"}
        v = v.strip().lower()
        if v not in allowed:
            raise ValueError(f"difficulty must be one of {sorted(allowed)}, got '{v}'")
        return v


class ProblemWithSolution(BaseModel):
    """Pairs a problem with its generated (and optionally critiqued) solution."""

    problem: Problem
    solution: Optional[Solution] = None
    iteration: int = Field(
        default=0,
        description="Number of critic–regeneration iterations performed",
        ge=0,
    )


class EvalScore(BaseModel):
    """Output of the LLM-as-judge evaluation."""

    problem_quality: int = Field(..., ge=1, le=10, description="Clarity and specificity of the problem statement")
    solution_realism: int = Field(..., ge=1, le=10, description="How realistic and actionable the solution is")
    hallucination_risk: int = Field(
        ...,
        ge=1,
        le=10,
        description="Likelihood that claims are fabricated (1 = very likely hallucinated, 10 = well-grounded)",
    )
    explanation: str = Field(..., description="Brief justification of all three scores")


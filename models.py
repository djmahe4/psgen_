"""
Pydantic models for data validation and structure.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class NewsItem(BaseModel):
    """Model for a news item."""
    title: str = Field(..., description="Title of the news article")
    snippet: str = Field(..., description="Brief description of the news")
    link: str = Field(..., description="URL to the full article")
    source: Optional[str] = Field(None, description="News source")


class Problem(BaseModel):
    """Model for an extracted problem."""
    description: str = Field(..., description="Description of the problem")
    affected_people: int = Field(..., description="Estimated number of people affected", ge=0)
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    location: str = Field(..., description="Location where the problem exists")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        allowed = ['low', 'medium', 'high', 'critical']
        if v.lower() not in allowed:
            raise ValueError(f'Severity must be one of {allowed}')
        return v.lower()


class Solution(BaseModel):
    """Model for a solution suggestion."""
    necessity: str = Field(..., description="Why this solution is necessary")
    difficulty: str = Field(..., description="Difficulty level: easy, medium, hard")
    implementation_steps: List[str] = Field(..., description="Steps to implement the solution")
    estimated_impact: str = Field(..., description="Expected impact of the solution")
    
    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v):
        allowed = ['easy', 'medium', 'hard']
        if v.lower() not in allowed:
            raise ValueError(f'Difficulty must be one of {allowed}')
        return v.lower()


class ProblemWithSolution(BaseModel):
    """Model combining a problem with its solution."""
    problem: Problem
    solution: Optional[Solution] = None

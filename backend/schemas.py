from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClauseInput(BaseModel):
    text: str
    page: Optional[int] = None  # source page if multi-page contract


class ClauseClassification(BaseModel):
    category: str  # e.g. "non-compete", "liability", "IP assignment"
    confidence: float = Field(ge=0.0, le=1.0)


class ClauseRiskScore(BaseModel):
    clause_text: str
    classification: ClauseClassification
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=10.0)
    explanation: str  # plain-language why this is risky


class AnalysisReport(BaseModel):
    clauses: list[ClauseRiskScore]
    overall_risk_score: float = Field(ge=0.0, le=10.0)
    overall_risk_level: RiskLevel
    negotiation_script: str  # ready-to-use pushback language
    summary: str  # one-paragraph plain-language summary

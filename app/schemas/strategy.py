from datetime import date
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field

from app.schemas.common import Idea, IdeaDraft


class StrategyRequest(BaseModel):
    niche: str = Field(..., min_length=2, max_length=120)
    target_audience: str = Field(..., min_length=2, max_length=200)
    language: str = Field(default="English", min_length=2, max_length=60)
    start_date: Optional[date] = None
    competitor_url: Optional[AnyHttpUrl] = None


class CompetitorAnalysis(BaseModel):
    themes: List[str] = Field(default_factory=list)
    content_pillars: List[str] = Field(default_factory=list)
    engagement_style: List[str] = Field(default_factory=list)
    content_gaps: List[str] = Field(default_factory=list)


class StrategyLLMResponse(BaseModel):
    competitor_analysis: Optional[CompetitorAnalysis] = None
    ideas: List[IdeaDraft]


class StrategyResponse(BaseModel):
    niche: str
    target_audience: str
    language: str
    start_date: Optional[date]
    competitor_url: Optional[AnyHttpUrl]
    competitor_analyzed: bool
    competitor_analysis: Optional[CompetitorAnalysis]
    ideas: List[Idea]

from datetime import date
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field

from app.schemas.common import Idea


class SuggestIdeasRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=500)
    duration_days: int = Field(default=7, ge=1)
    target_audience: Optional[str] = Field(default=None, min_length=2, max_length=200)
    language: Optional[str] = Field(default=None, min_length=2, max_length=60)
    start_date: Optional[date] = None
    competitor_url: Optional[AnyHttpUrl] = None


class SuggestionInferenceLLMResponse(BaseModel):
    niche: str = Field(..., min_length=2, max_length=120)
    target_audience: str = Field(..., min_length=2, max_length=200)
    language: str = Field(..., min_length=2, max_length=60)


class SuggestIdeasResponse(BaseModel):
    query: str
    niche: str
    target_audience: str
    language: str
    duration_days: int
    inferred_target_audience: bool
    inferred_language: bool
    query_suggestions: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    base_ideas: List[Idea]
    suggested_ideas: List[Idea]

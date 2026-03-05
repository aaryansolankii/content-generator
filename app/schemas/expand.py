from typing import List

from pydantic import BaseModel, Field

from app.schemas.common import Idea, IdeaDraft


class ExpandIdeasRequest(BaseModel):
    selected_ideas: List[Idea] = Field(..., min_length=1)
    duration_days: int = Field(..., ge=1)
    language: str = Field(default="English", min_length=2, max_length=60)


class ExpandIdeasLLMResponse(BaseModel):
    expanded_ideas: List[IdeaDraft]


class ExpandIdeasResponse(BaseModel):
    expanded_ideas: List[Idea]

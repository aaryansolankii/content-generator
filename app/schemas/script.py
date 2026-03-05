from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ContentFormat, ContentPillar


class ScriptGenerationRequest(BaseModel):
    idea_id: UUID
    title: str = Field(..., min_length=3, max_length=140)
    format: ContentFormat
    pillar: ContentPillar
    language: str = Field(default="English", min_length=2, max_length=60)
    angle: Optional[str] = Field(default=None, max_length=240)


class GeneratedContent(BaseModel):
    dialogues: List[str] = Field(..., min_length=1, max_length=20)
    scene_breakdown: List[str] = Field(..., min_length=1, max_length=20)
    caption: str = Field(..., min_length=10, max_length=1800)
    cta: str = Field(..., min_length=4, max_length=320)
    hashtags: List[str] = Field(..., min_length=10, max_length=15)

    @field_validator("hashtags")
    @classmethod
    def ensure_hashtags_format(cls, values: List[str]) -> List[str]:
        cleaned = []
        for tag in values:
            normalized = tag.strip().replace(" ", "")
            if not normalized.startswith("#"):
                normalized = f"#{normalized}"
            cleaned.append(normalized)
        return cleaned


class ScriptLLMResponse(BaseModel):
    content: GeneratedContent


class ScriptGenerationResponse(BaseModel):
    content: GeneratedContent

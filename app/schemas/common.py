from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContentFormat(str, Enum):
    REEL = "Reel"
    CAROUSEL = "Carousel"


class ContentPillar(str, Enum):
    EDUCATION = "Education"
    AUTHORITY = "Authority"
    STORY = "Story"
    ENGAGEMENT = "Engagement"


class IdeaDraft(BaseModel):
    title: str = Field(..., min_length=3, max_length=140)
    format: ContentFormat
    pillar: ContentPillar
    description: str = Field(..., min_length=10, max_length=600)

    @field_validator("title", "description")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()


class Idea(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    idea_id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=3, max_length=140)
    format: ContentFormat
    pillar: ContentPillar
    description: str = Field(..., min_length=10, max_length=600)

    @field_validator("title", "description")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()

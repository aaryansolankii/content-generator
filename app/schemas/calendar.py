from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ContentFormat, ContentPillar, Idea

ALLOWED_POSTING_TIMES = {"07:30 AM", "01:00 PM", "07:00 PM"}


class CalendarGenerationRequest(BaseModel):
    selected_ideas: List[Idea] = Field(..., min_length=1)
    duration_days: int = Field(..., ge=1, le=90)
    language: str = Field(default="English", min_length=2, max_length=60)
    start_date: Optional[date] = None


class CalendarItemDraft(BaseModel):
    date: date
    time: str
    idea_index: int = Field(..., ge=1)
    angle: Optional[str] = Field(default=None, max_length=240)
    theme: str = Field(default="", max_length=180)
    hook: str = Field(default="", max_length=320)
    key_visual_direction: str = Field(default="", max_length=500)
    primary_cta: str = Field(default="", max_length=240)
    suggested_hashtags: str = Field(default="", max_length=500)

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in ALLOWED_POSTING_TIMES:
            raise ValueError(f"time must be one of {sorted(ALLOWED_POSTING_TIMES)}")
        return cleaned


class CalendarLLMResponse(BaseModel):
    calendar: List[CalendarItemDraft]


class CalendarSlot(BaseModel):
    week: int = Field(..., ge=1)
    day: int = Field(..., ge=1, le=7)
    date: date
    time: str
    platform: str = Field(default="Instagram")
    idea_id: UUID
    title: str
    format: ContentFormat
    pillar: ContentPillar
    angle: Optional[str] = None
    theme: str
    hook: str
    key_visual_direction: str
    primary_cta: str
    suggested_hashtags: str


class CalendarSheetRow(BaseModel):
    post_date: date
    day: str
    post_format: str
    theme: str
    hook: str
    key_visual_direction: str
    primary_cta: str
    suggested_hashtags: str


class CalendarGenerationResponse(BaseModel):
    expanded_ideas: List[Idea]
    calendar: List[CalendarSlot]
    calendar_sheet: List[CalendarSheetRow]

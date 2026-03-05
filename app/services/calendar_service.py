from __future__ import annotations

import json
from datetime import date, timedelta

from pydantic import BaseModel, Field

from app.schemas.calendar import (
    CalendarGenerationRequest,
    CalendarGenerationResponse,
    CalendarItemDraft,
    CalendarLLMResponse,
    CalendarSheetRow,
    CalendarSlot,
)
from app.schemas.common import Idea
from app.schemas.expand import ExpandIdeasRequest
from app.schemas.strategy import StrategyRequest
from app.services.expansion_service import ExpansionService
from app.services.llm_service import LLMService
from app.services.strategy_service import StrategyService
from app.utils.exceptions import InvalidLLMResponseError

MAX_CALENDAR_DAYS_PER_LLM_CALL = 14


class CalendarContextInference(BaseModel):
    target_audience: str = Field(..., min_length=2, max_length=200)
    language: str = Field(..., min_length=2, max_length=60)


class CalendarService:
    def __init__(
        self,
        llm_service: LLMService,
        expansion_service: ExpansionService,
        strategy_service: StrategyService,
    ) -> None:
        self._llm_service = llm_service
        self._expansion_service = expansion_service
        self._strategy_service = strategy_service

    async def generate_calendar(self, payload: CalendarGenerationRequest) -> CalendarGenerationResponse:
        start_date = payload.start_date or date.today()
        resolved_target_audience, resolved_language = await self._resolve_context(payload)

        base_strategy = await self._strategy_service.generate_strategy(
            StrategyRequest(
                niche=payload.niche,
                target_audience=resolved_target_audience,
                language=resolved_language,
                start_date=start_date,
                competitor_url=payload.competitor_url,
            )
        )
        base_ideas = base_strategy.ideas

        expanded = await self._expansion_service.expand_ideas(
            ExpandIdeasRequest(
                selected_ideas=base_ideas,
                duration_days=payload.duration_days,
                language=resolved_language,
            )
        )
        expanded_ideas = expanded.expanded_ideas
        ideas_by_index: dict[int, Idea] = {index + 1: idea for index, idea in enumerate(expanded_ideas)}

        all_items: list[CalendarItemDraft] = []
        for offset in range(0, payload.duration_days, MAX_CALENDAR_DAYS_PER_LLM_CALL):
            current_days = min(MAX_CALENDAR_DAYS_PER_LLM_CALL, payload.duration_days - offset)
            current_start_date = start_date + timedelta(days=offset)
            chunk_ideas = expanded_ideas[offset: offset + current_days]

            prompt = self._build_prompt(
                ideas=chunk_ideas,
                duration_days=current_days,
                start_date=current_start_date,
                idea_index_start=offset + 1,
            )
            llm_output = await self._llm_service.generate_json(
                prompt=prompt,
                temperature=0.6,
                response_model=CalendarLLMResponse,
            )

            ordered_chunk = self._validate_and_order_chunk(
                items=llm_output.calendar,
                expected_days=current_days,
                chunk_start_date=current_start_date,
            )
            all_items.extend(ordered_chunk)

        ordered_items = sorted(all_items, key=lambda item: item.date)
        self._validate_continuous_dates(
            items=ordered_items,
            expected_days=payload.duration_days,
            start_date=start_date,
        )

        slots: list[CalendarSlot] = []
        for index, item in enumerate(ordered_items):
            if item.idea_index not in ideas_by_index:
                raise InvalidLLMResponseError(
                    "Calendar included idea_index not present in expanded ideas.",
                    details={"idea_index": item.idea_index},
                )

            canonical_idea = ideas_by_index[item.idea_index]
            theme = item.theme.strip() if item.theme else canonical_idea.title
            hook = item.hook.strip() if item.hook else canonical_idea.description[:220]
            key_visual_direction = (
                item.key_visual_direction.strip()
                if item.key_visual_direction
                else f"{canonical_idea.format.value} visual treatment focused on {canonical_idea.pillar.value}."
            )
            primary_cta = (
                item.primary_cta.strip()
                if item.primary_cta
                else "Share your perspective in comments and save this post."
            )
            suggested_hashtags = (
                item.suggested_hashtags.strip()
                if item.suggested_hashtags
                else self._default_hashtags(canonical_idea)
            )
            if not self._is_english_hashtag_string(suggested_hashtags):
                suggested_hashtags = self._default_hashtags(canonical_idea)
            slots.append(
                CalendarSlot(
                    week=(index // 7) + 1,
                    day=(index % 7) + 1,
                    date=item.date,
                    time=item.time,
                    platform="Instagram",
                    idea_id=canonical_idea.idea_id,
                    title=canonical_idea.title,
                    format=canonical_idea.format,
                    pillar=canonical_idea.pillar,
                    angle=item.angle,
                    theme=theme,
                    hook=hook,
                    key_visual_direction=key_visual_direction,
                    primary_cta=primary_cta,
                    suggested_hashtags=suggested_hashtags,
                )
            )

        calendar_sheet = [
            CalendarSheetRow(
                post_date=slot.date,
                day=slot.date.strftime("%A"),
                post_format=slot.format.value,
                theme=slot.theme,
                hook=slot.hook,
                key_visual_direction=slot.key_visual_direction,
                primary_cta=slot.primary_cta,
                suggested_hashtags=slot.suggested_hashtags,
            )
            for slot in slots
        ]

        return CalendarGenerationResponse(
            niche=payload.niche,
            target_audience=resolved_target_audience,
            language=resolved_language,
            base_ideas=base_ideas,
            expanded_ideas=expanded_ideas,
            calendar=slots,
            calendar_sheet=calendar_sheet,
        )

    async def _resolve_context(self, payload: CalendarGenerationRequest) -> tuple[str, str]:
        if payload.target_audience and payload.language:
            return payload.target_audience, payload.language

        prompt = f"""
You are a social media strategy assistant.
Infer missing context from a niche.

Niche: {payload.niche}
Provided target_audience: {payload.target_audience if payload.target_audience else "missing"}
Provided language: {payload.language if payload.language else "missing"}

Rules:
- Keep target_audience specific and practical.
- Choose language based on likely intent and Indian creator context if missing.
- If one field is provided, keep it aligned and infer only missing one.

Return strict JSON only:
{{
  "target_audience": "",
  "language": ""
}}
""".strip()

        inferred = await self._llm_service.generate_json(
            prompt=prompt,
            temperature=0.6,
            response_model=CalendarContextInference,
        )

        return (
            payload.target_audience or inferred.target_audience,
            payload.language or inferred.language,
        )

    def _validate_and_order_chunk(
        self,
        *,
        items: list[CalendarItemDraft],
        expected_days: int,
        chunk_start_date: date,
    ) -> list[CalendarItemDraft]:
        if len(items) != expected_days:
            raise InvalidLLMResponseError(
                "Calendar chunk output length does not match expected days.",
                details={
                    "expected_days": expected_days,
                    "actual_days": len(items),
                    "chunk_start_date": chunk_start_date.isoformat(),
                },
            )

        ordered_items = sorted(items, key=lambda item: item.date)
        expected_dates = [chunk_start_date + timedelta(days=index) for index in range(expected_days)]
        returned_dates = [item.date for item in ordered_items]

        if returned_dates != expected_dates:
            raise InvalidLLMResponseError(
                "Calendar chunk dates are not a continuous sequence from chunk start date.",
                details={
                    "expected_dates": [value.isoformat() for value in expected_dates],
                    "returned_dates": [value.isoformat() for value in returned_dates],
                },
            )

        return ordered_items

    def _validate_continuous_dates(
        self,
        *,
        items: list[CalendarItemDraft],
        expected_days: int,
        start_date: date,
    ) -> None:
        if len(items) != expected_days:
            raise InvalidLLMResponseError(
                "Calendar output length does not match duration_days.",
                details={
                    "expected_days": expected_days,
                    "actual_days": len(items),
                },
            )

        expected_dates = [start_date + timedelta(days=index) for index in range(expected_days)]
        returned_dates = [item.date for item in items]

        if returned_dates != expected_dates:
            raise InvalidLLMResponseError(
                "Calendar dates are not a continuous sequence from start_date.",
                details={
                    "expected_dates": [value.isoformat() for value in expected_dates],
                    "returned_dates": [value.isoformat() for value in returned_dates],
                },
            )

    def _build_prompt(
        self,
        *,
        ideas: list[Idea],
        duration_days: int,
        start_date: date,
        idea_index_start: int,
    ) -> str:
        ideas_payload = [
            {
                "idea_index": idea_index_start + index,
                "idea_id": str(idea.idea_id),
                "title": idea.title,
                "format": idea.format.value,
                "pillar": idea.pillar.value,
            }
            for index, idea in enumerate(ideas)
        ]

        ideas_json = json.dumps(ideas_payload, ensure_ascii=True)

        return f"""
You are an Instagram content calendar strategist.
Map the expanded ideas strategically over the requested number of days.

Inputs:
- Start date: {start_date.isoformat()}
- Duration days: {duration_days}
- Expanded ideas JSON: {ideas_json}

Rules:
- Build exactly one calendar slot per day for {duration_days} consecutive days from start date.
- Reuse ideas when needed, but keep the sequence strategic.
- Rotate pillars thoughtfully.
- Avoid back-to-back repetition of the same format whenever possible.
- Use only these posting times: "07:30 AM", "01:00 PM", "07:00 PM".
- Use idea_index values exactly from provided expanded ideas.
- Include a short optional "angle" to make repeated ideas feel fresh.
- Also include sheet-ready content fields:
  - theme
  - hook
  - key_visual_direction (for editors)
  - primary_cta
  - suggested_hashtags (space-separated hashtags, in English only)

Return strict JSON only in this exact structure:
{{
  "calendar": [
    {{
      "date": "YYYY-MM-DD",
      "time": "07:30 AM",
      "idea_index": 1,
      "angle": "optional",
      "theme": "",
      "hook": "",
      "key_visual_direction": "",
      "primary_cta": "",
      "suggested_hashtags": "#tag1 #tag2"
    }}
  ]
}}
""".strip()

    def _default_hashtags(self, idea: Idea) -> str:
        pillar_tag = f"#{idea.pillar.value.replace(' ', '')}"
        format_tag = f"#{idea.format.value}"
        return f"#ContentCalendar #SocialMediaStrategy #India {pillar_tag} {format_tag}"

    def _is_english_hashtag_string(self, value: str) -> bool:
        tokens = [token for token in value.split() if token]
        if not tokens:
            return False
        return all(token.isascii() and token.startswith("#") for token in tokens)

from __future__ import annotations

import json
from uuid import uuid4

from app.schemas.common import Idea
from app.schemas.expand import ExpandIdeasLLMResponse, ExpandIdeasRequest, ExpandIdeasResponse
from app.services.llm_service import LLMService
from app.utils.exceptions import InvalidLLMResponseError

MAX_EXPANSION_IDEAS_PER_CALL = 45


class ExpansionService:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    async def expand_ideas(self, payload: ExpandIdeasRequest) -> ExpandIdeasResponse:
        expanded_ideas: list[Idea] = []
        existing_titles: list[str] = []

        for offset in range(0, payload.duration_days, MAX_EXPANSION_IDEAS_PER_CALL):
            current_count = min(MAX_EXPANSION_IDEAS_PER_CALL, payload.duration_days - offset)

            prompt = self._build_prompt(
                payload=payload,
                idea_count=current_count,
                existing_titles=existing_titles,
            )
            llm_output = await self._llm_service.generate_json(
                prompt=prompt,
                temperature=0.8,
                response_model=ExpandIdeasLLMResponse,
            )

            if len(llm_output.expanded_ideas) != current_count:
                raise InvalidLLMResponseError(
                    "Expanded ideas length did not match requested count for a batch.",
                    details={
                        "expected_count": current_count,
                        "actual_count": len(llm_output.expanded_ideas),
                    },
                )

            for item in llm_output.expanded_ideas:
                expanded_ideas.append(
                    Idea(
                        idea_id=uuid4(),
                        title=item.title,
                        format=item.format,
                        pillar=item.pillar,
                        description=item.description,
                    )
                )
                existing_titles.append(item.title)

        return ExpandIdeasResponse(expanded_ideas=expanded_ideas)

    def _build_prompt(self, *, payload: ExpandIdeasRequest, idea_count: int, existing_titles: list[str]) -> str:
        selected_payload = [
            {
                "idea_id": str(idea.idea_id),
                "title": idea.title,
                "format": idea.format.value,
                "pillar": idea.pillar.value,
                "description": idea.description,
            }
            for idea in payload.selected_ideas
        ]

        selected_json = json.dumps(selected_payload, ensure_ascii=True)
        existing_titles_json = json.dumps(existing_titles, ensure_ascii=True)

        return f"""
You are an Instagram content strategist.
Expand idea inventory while preserving strategic quality.

Inputs:
- requested_new_ideas_count: {idea_count}
- language: {payload.language}
- selected_ideas JSON: {selected_json}
- already_generated_titles JSON: {existing_titles_json}

Tasks:
1) Analyze selected ideas and infer recurring pattern:
   - format usage
   - pillar mix
   - tone
   - structure
2) Generate exactly {idea_count} NEW ideas.

Rules:
- Avoid repetition and avoid slight rewording of existing ideas.
- Do not duplicate or closely paraphrase titles from already_generated_titles.
- Keep ideas original while maintaining the same strategic style.
- Balance pillars and formats realistically.
- Keep each description concise and practical (1-3 sentences).
- Generate title and description in {payload.language}.
- If language is Hinglish, use natural Hindi-English mixing.
- If language is Hindi, write in Hindi tone (Devanagari preferred).
- If language is English, keep a clear professional tone.

Return strict JSON only in this exact structure:
{{
  "expanded_ideas": [
    {{
      "title": "",
      "format": "Reel" or "Carousel",
      "pillar": "Education" or "Authority" or "Story" or "Engagement",
      "description": ""
    }}
  ]
}}
""".strip()

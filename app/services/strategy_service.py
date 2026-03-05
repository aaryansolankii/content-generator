from __future__ import annotations

import json
import logging
from datetime import date
from uuid import uuid4

from app.schemas.common import Idea
from app.schemas.strategy import StrategyLLMResponse, StrategyRequest, StrategyResponse
from app.services.competitor_service import CompetitorService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class StrategyService:
    def __init__(self, llm_service: LLMService, competitor_service: CompetitorService) -> None:
        self._llm_service = llm_service
        self._competitor_service = competitor_service

    async def generate_strategy(self, payload: StrategyRequest) -> StrategyResponse:
        competitor_content = None
        competitor_analyzed = False

        if payload.competitor_url:
            competitor_content = await self._competitor_service.scrape_content(str(payload.competitor_url))
            competitor_analyzed = competitor_content is not None
            if not competitor_content:
                logger.warning(
                    "Competitor URL provided but content extraction failed: %s",
                    payload.competitor_url,
                )

        prompt = self._build_prompt(payload=payload, competitor_content=competitor_content)
        llm_output = await self._llm_service.generate_json(
            prompt=prompt,
            temperature=0.7,
            response_model=StrategyLLMResponse,
        )

        ideas = [
            Idea(
                idea_id=uuid4(),
                title=item.title,
                format=item.format,
                pillar=item.pillar,
                description=item.description,
            )
            for item in llm_output.ideas
        ]

        return StrategyResponse(
            niche=payload.niche,
            target_audience=payload.target_audience,
            duration_days=payload.duration_days,
            language=payload.language,
            start_date=payload.start_date,
            competitor_url=payload.competitor_url,
            competitor_analyzed=competitor_analyzed,
            competitor_analysis=llm_output.competitor_analysis if competitor_analyzed else None,
            ideas=ideas,
        )

    def _build_prompt(self, *, payload: StrategyRequest, competitor_content: dict | None) -> str:
        competitor_section = "No competitor URL was provided. Set competitor_analysis to null."

        if competitor_content:
            competitor_json = json.dumps(competitor_content, ensure_ascii=True)
            competitor_section = (
                "Competitor content was scraped and must be analyzed.\n"
                "1) Analyze themes.\n"
                "2) Detect content pillars.\n"
                "3) Identify engagement style.\n"
                "4) Detect content gaps and opportunities.\n"
                "5) Generate differentiated ideas based on those gaps.\n"
                f"Competitor Data JSON: {competitor_json}"
            )

        start_date = payload.start_date.isoformat() if isinstance(payload.start_date, date) else "not provided"

        return f"""
You are an Instagram AI content strategist for India-focused creators.
Generate a strategy based on user context.

User context:
- Niche: {payload.niche}
- Target audience: {payload.target_audience}
- Number of ideas: {payload.number_of_ideas}
- Duration days: {payload.duration_days}
- Content language: {payload.language}
- Start date: {start_date}

Competitor handling:
{competitor_section}

Output must be strict JSON only. No markdown. No prose outside JSON.
Return exactly this structure:
{{
  "competitor_analysis": {{
    "themes": ["..."],
    "content_pillars": ["..."],
    "engagement_style": ["..."],
    "content_gaps": ["..."]
  }} OR null,
  "ideas": [
    {{
      "title": "",
      "format": "Reel" or "Carousel",
      "pillar": "Education" or "Authority" or "Story" or "Engagement",
      "description": ""
    }}
  ]
}}

Rules:
- Return exactly {payload.number_of_ideas} ideas.
- Ideas must be original and practically executable.
- Balance pillars across the idea set.
- Keep descriptions concise but specific (1-3 sentences).
- For Indian Instagram audience relevance, include culturally fitting hooks/examples where useful.
- Generate title and description in this language: {payload.language}.
- If language is Hinglish, use natural Hindi-English mixing.
- If language is Hindi, write in Hindi tone (Devanagari preferred).
- If language is English, keep a clear professional tone.
""".strip()

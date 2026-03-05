from __future__ import annotations

from typing import List

from app.schemas.common import ContentFormat
from app.schemas.script import ScriptGenerationRequest, ScriptGenerationResponse, ScriptLLMResponse
from app.services.llm_service import LLMService
from app.utils.exceptions import InvalidLLMResponseError


class ScriptService:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    async def generate_script(self, payload: ScriptGenerationRequest) -> ScriptGenerationResponse:
        prompt = self._build_prompt(payload)

        llm_output = await self._llm_service.generate_json(
            prompt=prompt,
            temperature=0.85,
            response_model=ScriptLLMResponse,
        )

        dialogue_count = len(llm_output.content.dialogues)
        scene_count = len(llm_output.content.scene_breakdown)
        if dialogue_count != scene_count:
            raise InvalidLLMResponseError(
                "dialogues and scene_breakdown must have the same number of items.",
                details={"dialogues": dialogue_count, "scene_breakdown": scene_count},
            )

        llm_output.content.hashtags = self._ensure_english_hashtags(llm_output.content.hashtags, payload)
        return ScriptGenerationResponse(content=llm_output.content)

    def _build_prompt(self, payload: ScriptGenerationRequest) -> str:
        angle_line = payload.angle if payload.angle else "No specific angle provided"

        if payload.format == ContentFormat.REEL:
            format_specific = (
                "Output should feel like short-form video direction with punchy spoken delivery."
            )
        else:
            format_specific = (
                "Output should be carousel-friendly: each dialogue-scene pair should map naturally to slide progression."
            )

        return f"""
You are an Instagram content writer and strategist.
Create publish-ready content in the requested language.

Inputs:
- idea_id: {payload.idea_id}
- title: {payload.title}
- format: {payload.format.value}
- pillar: {payload.pillar.value}
- angle: {angle_line}
- language: {payload.language}

Language rules:
- Generate dialogues, scene_breakdown, caption, and cta in {payload.language}.
- If language is Hinglish, use natural Hindi-English mixing.
- If language is Hindi, write in Hindi tone (Devanagari preferred).
- If language is English, keep a clear professional tone.
- Hashtags must always be in English (ASCII) and start with #.

Structure rules:
- dialogues must come first and contain ordered speaking lines.
- scene_breakdown must map 1:1 to dialogues in the same order.
- caption should summarize and expand on the content.
- cta should drive comments/saves/shares.
- hashtags must be 10 to 15 and relevant to the niche + India context.
- {format_specific}

Return strict JSON only, no markdown:
{{
  "content": {{
    "dialogues": ["Dialogue line 1", "Dialogue line 2"],
    "scene_breakdown": ["Scene 1: ...", "Scene 2: ..."],
    "caption": "",
    "cta": "",
    "hashtags": ["#tag"]
  }}
}}
""".strip()

    def _ensure_english_hashtags(self, hashtags: List[str], payload: ScriptGenerationRequest) -> List[str]:
        if hashtags and all(tag.isascii() for tag in hashtags):
            return hashtags

        format_tag = "#InstagramReel" if payload.format == ContentFormat.REEL else "#InstagramCarousel"
        pillar_tag = f"#{payload.pillar.value.replace(' ', '')}"
        fallback = [
            "#ContentStrategy",
            "#SocialMediaMarketing",
            "#ContentCreation",
            "#CreatorEconomy",
            "#AudienceGrowth",
            "#DigitalMarketing",
            "#IndiaCreators",
            "#EngagementTips",
            "#PersonalBranding",
            "#ContentPlanning",
            format_tag,
            pillar_tag,
        ]
        return fallback

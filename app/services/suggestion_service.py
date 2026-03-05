from __future__ import annotations

from app.schemas.expand import ExpandIdeasRequest
from app.schemas.strategy import StrategyRequest
from app.schemas.suggestion import SuggestIdeasRequest, SuggestIdeasResponse, SuggestionInferenceLLMResponse
from app.services.expansion_service import ExpansionService
from app.services.llm_service import LLMService
from app.services.strategy_service import StrategyService


class SuggestionService:
    def __init__(
        self,
        llm_service: LLMService,
        strategy_service: StrategyService,
        expansion_service: ExpansionService,
    ) -> None:
        self._llm_service = llm_service
        self._strategy_service = strategy_service
        self._expansion_service = expansion_service

    async def suggest_ideas(self, payload: SuggestIdeasRequest) -> SuggestIdeasResponse:
        inferred_context = await self._infer_context(payload)

        inferred_target_audience = payload.target_audience is None
        inferred_language = payload.language is None
        final_target_audience = payload.target_audience or inferred_context.target_audience
        final_language = payload.language or inferred_context.language
        follow_up_questions = self._build_follow_up_questions(payload, inferred_context.niche)
        query_suggestions = self._build_query_suggestions(inferred_context.niche)

        strategy_output = await self._strategy_service.generate_strategy(
            StrategyRequest(
                niche=inferred_context.niche,
                target_audience=final_target_audience,
                language=final_language,
                start_date=payload.start_date,
                competitor_url=payload.competitor_url,
            )
        )

        expanded_output = await self._expansion_service.expand_ideas(
            ExpandIdeasRequest(
                selected_ideas=strategy_output.ideas,
                duration_days=payload.duration_days,
                language=final_language,
            )
        )

        return SuggestIdeasResponse(
            query=payload.query,
            niche=inferred_context.niche,
            target_audience=final_target_audience,
            language=final_language,
            duration_days=payload.duration_days,
            inferred_target_audience=inferred_target_audience,
            inferred_language=inferred_language,
            query_suggestions=query_suggestions,
            follow_up_questions=follow_up_questions,
            base_ideas=strategy_output.ideas,
            suggested_ideas=expanded_output.expanded_ideas,
        )

    async def _infer_context(self, payload: SuggestIdeasRequest) -> SuggestionInferenceLLMResponse:
        target_audience_hint = payload.target_audience if payload.target_audience else "infer from query"
        language_hint = payload.language if payload.language else "infer from query"

        prompt = f"""
You are an Instagram content strategist assistant.
Infer the best content context from a user search intent.

User input query:
{payload.query}

Provided hints:
- target_audience: {target_audience_hint}
- language: {language_hint}

Rules:
- Infer a clear niche.
- Infer a practical target audience if not provided.
- Infer content language if not provided (English/Hindi/Hinglish/Tamil/other as needed).
- Keep values concise and usable for content planning.

Return strict JSON only:
{{
  "niche": "",
  "target_audience": "",
  "language": ""
}}
""".strip()

        return await self._llm_service.generate_json(
            prompt=prompt,
            temperature=0.7,
            response_model=SuggestionInferenceLLMResponse,
        )

    def _build_follow_up_questions(self, payload: SuggestIdeasRequest, niche: str) -> list[str]:
        questions: list[str] = [
            f"For niche '{niche}', do you want beginner, intermediate, or advanced content depth?",
            "Do you prefer mostly Reels, mostly Carousels, or a mixed format plan?",
        ]
        if payload.target_audience is None:
            questions.append(f"For niche '{niche}', who exactly is your primary audience segment?")
        if payload.language is None:
            questions.append("Which output language do you prefer: English, Hindi, Hinglish, Tamil, or other?")
        if "duration_days" not in payload.model_fields_set:
            questions.append("How many days of content ideas do you want?")
        if payload.competitor_url is None:
            questions.append("Do you want to add a competitor/reference URL for style benchmarking?")
        return questions[:5]

    def _build_query_suggestions(self, niche: str) -> list[str]:
        base = niche.strip()
        return [
            f"{base} reel ideas for beginners",
            f"{base} carousel ideas with hooks",
            f"{base} myth-busting content ideas",
            f"{base} story-based content ideas",
            f"{base} 30-day content plan",
        ]

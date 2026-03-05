from functools import lru_cache

from app.config import get_settings
from app.services.calendar_service import CalendarService
from app.services.competitor_service import CompetitorService
from app.services.expansion_service import ExpansionService
from app.services.llm_service import LLMService
from app.services.script_service import ScriptService
from app.services.suggestion_service import SuggestionService
from app.services.strategy_service import StrategyService


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService(settings=get_settings())


@lru_cache
def get_competitor_service() -> CompetitorService:
    return CompetitorService(settings=get_settings())


@lru_cache
def get_strategy_service() -> StrategyService:
    return StrategyService(
        llm_service=get_llm_service(),
        competitor_service=get_competitor_service(),
    )


@lru_cache
def get_calendar_service() -> CalendarService:
    return CalendarService(
        llm_service=get_llm_service(),
        expansion_service=get_expansion_service(),
        strategy_service=get_strategy_service(),
    )


@lru_cache
def get_expansion_service() -> ExpansionService:
    return ExpansionService(llm_service=get_llm_service())


@lru_cache
def get_script_service() -> ScriptService:
    return ScriptService(llm_service=get_llm_service())


@lru_cache
def get_suggestion_service() -> SuggestionService:
    return SuggestionService(
        llm_service=get_llm_service(),
        strategy_service=get_strategy_service(),
        expansion_service=get_expansion_service(),
    )

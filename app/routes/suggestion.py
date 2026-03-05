from fastapi import APIRouter, Depends

from app.schemas.suggestion import SuggestIdeasRequest, SuggestIdeasResponse
from app.services.dependencies import get_suggestion_service
from app.services.suggestion_service import SuggestionService

router = APIRouter(tags=["Suggestions"])


@router.post("/suggest-ideas", response_model=SuggestIdeasResponse)
async def suggest_ideas(
    payload: SuggestIdeasRequest,
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
) -> SuggestIdeasResponse:
    return await suggestion_service.suggest_ideas(payload)

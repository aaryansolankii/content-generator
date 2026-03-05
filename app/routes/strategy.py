from fastapi import APIRouter, Depends

from app.schemas.strategy import StrategyRequest, StrategyResponse
from app.services.dependencies import get_strategy_service
from app.services.strategy_service import StrategyService

router = APIRouter(tags=["Strategy"])


@router.post("/generate-ideas", response_model=StrategyResponse)
async def generate_ideas(
    payload: StrategyRequest,
    strategy_service: StrategyService = Depends(get_strategy_service),
) -> StrategyResponse:
    return await strategy_service.generate_strategy(payload)

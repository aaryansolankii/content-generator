from fastapi import APIRouter, Depends

from app.schemas.calendar import CalendarGenerationRequest, CalendarGenerationResponse
from app.services.calendar_service import CalendarService
from app.services.dependencies import get_calendar_service

router = APIRouter(tags=["Calendar"])


@router.post("/generate-calendar", response_model=CalendarGenerationResponse)
async def generate_calendar(
    payload: CalendarGenerationRequest,
    calendar_service: CalendarService = Depends(get_calendar_service),
) -> CalendarGenerationResponse:
    return await calendar_service.generate_calendar(payload)

from fastapi import APIRouter, Depends

from app.schemas.script import ScriptGenerationRequest, ScriptGenerationResponse
from app.services.dependencies import get_script_service
from app.services.script_service import ScriptService

router = APIRouter(tags=["Script"])


@router.post("/generate-script", response_model=ScriptGenerationResponse)
async def generate_script(
    payload: ScriptGenerationRequest,
    script_service: ScriptService = Depends(get_script_service),
) -> ScriptGenerationResponse:
    return await script_service.generate_script(payload)

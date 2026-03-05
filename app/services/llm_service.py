from __future__ import annotations

import logging
from typing import Any, Type, TypeVar

import httpx
from pydantic import BaseModel

from app.config import Settings
from app.utils.exceptions import ExternalServiceError, InvalidLLMResponseError
from app.utils.json_utils import parse_json_response

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._endpoint = (
            f"{self._settings.gemini_api_base_url}/models/"
            f"{self._settings.gemini_model}:generateContent"
        )

    async def generate_json(self, *, prompt: str, temperature: float, response_model: Type[T]) -> T:
        last_error: Exception | None = None

        for attempt in range(1, 3):
            raw_text = await self._generate_raw(prompt=prompt, temperature=temperature)
            try:
                parsed = parse_json_response(raw_text)
                return response_model.model_validate(parsed)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning(
                    "Gemini returned invalid JSON payload. attempt=%s model=%s error=%s",
                    attempt,
                    self._settings.gemini_model,
                    exc,
                )
                if attempt == 2:
                    break

        raise InvalidLLMResponseError(
            "Gemini returned an invalid JSON response after one retry.",
            details=str(last_error) if last_error else None,
        )

    async def _generate_raw(self, *, prompt: str, temperature: float) -> str:
        if not self._settings.gemini_api_key:
            raise ExternalServiceError("GEMINI_API_KEY is not configured.")

        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }

        params = {"key": self._settings.gemini_api_key}

        try:
            async with httpx.AsyncClient(timeout=self._settings.gemini_timeout_seconds) as client:
                response = await client.post(self._endpoint, params=params, json=payload)
        except httpx.TimeoutException as exc:
            raise ExternalServiceError("Gemini request timed out.", details=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceError("Gemini request failed.", details=str(exc)) from exc

        if response.status_code >= 400:
            raise ExternalServiceError(
                "Gemini API returned an error response.",
                details={"status_code": response.status_code, "body": response.text},
            )

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise ExternalServiceError(
                "Gemini API returned no candidates.",
                details=data,
            )

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )
        if not parts:
            raise ExternalServiceError(
                "Gemini API candidate did not include content parts.",
                details=data,
            )

        text = parts[0].get("text")
        if not text:
            raise ExternalServiceError(
                "Gemini API candidate did not include text output.",
                details=data,
            )

        return text

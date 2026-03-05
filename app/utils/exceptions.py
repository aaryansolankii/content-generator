from __future__ import annotations

from typing import Any, Optional


class AppException(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "APP_ERROR",
        status_code: int = 400,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ExternalServiceError(AppException):
    def __init__(self, message: str, *, details: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details=details,
        )


class InvalidLLMResponseError(AppException):
    def __init__(self, message: str, *, details: Optional[Any] = None) -> None:
        super().__init__(
            message=message,
            code="INVALID_LLM_RESPONSE",
            status_code=500,
            details=details,
        )

"""
Error handling for Trello MCP Server.

Normalizes Trello API errors into MCP-compatible format:
- error_code
- error_message
- retryable
- original_provider_error
"""

from typing import Any, Optional


class TrelloError(Exception):
    """Base error for Trello operations."""

    def __init__(
        self,
        message: str,
        error_code: str = "TRELLO_ERROR",
        retryable: bool = False,
        original_error: Optional[Any] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.retryable = retryable
        self.original_error = original_error
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "error_code": self.error_code,
            "error_message": self.message,
            "retryable": self.retryable,
            "original_provider_error": str(self.original_error)
            if self.original_error
            else None,
        }


class TrelloAuthError(TrelloError):
    def __init__(
        self,
        message: str = "API key or token invalid",
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            retryable=True,
            original_error=original_error,
        )


class TrelloNotFoundError(TrelloError):
    def __init__(
        self,
        message: str = "Resource not found",
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            retryable=False,
            original_error=original_error,
        )


class TrelloPermissionError(TrelloError):
    def __init__(
        self,
        message: str = "Permission denied",
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            retryable=False,
            original_error=original_error,
        )


class TrelloRateLimitError(TrelloError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT",
            retryable=True,
            original_error=original_error,
        )


class TrelloValidationError(TrelloError):
    def __init__(
        self,
        message: str,
        original_error: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            retryable=False,
            original_error=original_error,
        )


def normalize_trello_error(
    exc: Exception, status_code: Optional[int] = None
) -> TrelloError:
    """Map Trello HTTP / transport errors to standardized TrelloError subclasses."""
    error_str = str(exc).lower()
    code = status_code
    if code is None:
        if "401" in error_str:
            code = 401
        elif "403" in error_str:
            code = 403
        elif "404" in error_str:
            code = 404
        elif "429" in error_str:
            code = 429
        elif "500" in error_str or "502" in error_str or "503" in error_str:
            code = 500

    if code == 401 or ("invalid" in error_str and "token" in error_str):
        return TrelloAuthError(
            message="API key or token invalid", original_error=exc
        )
    if code == 403 or "permission" in error_str or "forbidden" in error_str:
        return TrelloPermissionError(message="Permission denied", original_error=exc)
    if code == 404 or "not found" in error_str:
        return TrelloNotFoundError(message="Resource not found", original_error=exc)
    if code == 429 or "rate" in error_str or "throttle" in error_str:
        return TrelloRateLimitError(message="Rate limit exceeded", original_error=exc)
    if code in (500, 502, 503):
        return TrelloError(
            message="Trello API server error",
            error_code="PROVIDER_ERROR",
            retryable=True,
            original_error=exc,
        )
    return TrelloError(
        message=str(exc),
        error_code="UNKNOWN_ERROR",
        retryable=False,
        original_error=exc,
    )

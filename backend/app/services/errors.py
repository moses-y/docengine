"""Transport-agnostic error types raised by the service layer.

`app.main` installs a single exception handler that maps each of these to an
HTTP status code and the uniform `{"error": {...}}` envelope described in the
PRD (§4.5), so services never import FastAPI.
"""

from __future__ import annotations


class ApiError(Exception):
    status_code: int = 400
    code: str = "bad_request"

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


class NotFoundError(ApiError):
    status_code = 404
    code = "not_found"


class ForbiddenError(ApiError):
    status_code = 403
    code = "forbidden"


class UnauthorizedError(ApiError):
    status_code = 401
    code = "unauthorized"


class ConflictError(ApiError):
    status_code = 409
    code = "conflict"


class ValidationFailedError(ApiError):
    status_code = 422
    code = "validation_failed"


class PayloadTooLargeError(ApiError):
    status_code = 413
    code = "payload_too_large"


class UnsupportedMediaTypeError(ApiError):
    status_code = 415
    code = "unsupported_media_type"

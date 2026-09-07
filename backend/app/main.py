"""ASGI application entrypoint: wires config, logging, CORS, routers, and the
single exception handler that turns `app.services.errors.ApiError` into the
uniform `{"error": {...}}` envelope (PRD §4.5) for every router at once.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging_conf import RequestIdMiddleware, configure_logging, get_logger
from app.routers import attachments, auth, documents, shares
from app.services.errors import ApiError

configure_logging()
logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(title="DocEngine API", version="1.0.0")

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(shares.router)
app.include_router(attachments.router)


@app.exception_handler(ApiError)
async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    logger.info(
        "api_error",
        code=exc.code,
        message=exc.message,
        path=request.url.path,
        status=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "field": exc.field}},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first.get("loc", ()) if p != "body") or None
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_failed",
                "message": first.get("msg", "Invalid request"),
                "field": field,
            }
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "Something went wrong on our end.",
                "field": None,
            }
        },
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

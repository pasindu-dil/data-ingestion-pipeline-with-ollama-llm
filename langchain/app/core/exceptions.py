"""Domain errors, translated to HTTP responses in one place."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 500


class ModelNotAllowedError(AppError):
    status_code = 400


class UnknownSourceError(AppError):
    status_code = 400


class QueryGenerationError(AppError):
    """The LLM never produced a valid, executable query."""

    status_code = 422


class InvalidSQLError(ValueError):
    """Raised by the validator when generated SQL breaks a safety rule."""


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

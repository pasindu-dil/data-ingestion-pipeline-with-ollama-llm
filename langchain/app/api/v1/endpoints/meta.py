from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_app_settings, get_registry
from app.core.config import Settings
from app.schemas.query import ModelsResponse
from app.services.backend import BackendRegistry

router = APIRouter(tags=["meta"])


@router.get("/models", response_model=ModelsResponse)
def models(
    settings: Settings = Depends(get_app_settings),
    registry: BackendRegistry = Depends(get_registry),
) -> dict[str, Any]:
    return {
        "default": settings.default_model,
        "allowed": settings.allowed_models,
        "sources": registry.names,
        "default_source": registry.default,
    }


@router.get("/schema")
def schema(
    source: str | None = None,
    refresh: bool = False,
    registry: BackendRegistry = Depends(get_registry),
) -> dict[str, str]:
    b = registry.get(source)
    return {"source": b.name, "language": b.language, "schema": b.schema.get(force=refresh)}

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_health_service
from app.services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get("/health")
def health(svc: HealthService = Depends(get_health_service)) -> dict[str, Any]:
    status = svc.check()
    if not all(status.values()):
        raise HTTPException(status_code=503, detail=status)
    return {"status": "ok", **status}

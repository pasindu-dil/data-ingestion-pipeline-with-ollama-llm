from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import ui
from app.api.v1.endpoints import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.container import build_container
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    container = build_container(settings)
    container.registry.warm_up()
    app.state.container = container
    yield
    container.registry.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Offline Text-to-SQL (ClickHouse)", version="2.0.0", lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(health.router)  # /health (unversioned, for probes)
    app.include_router(api_router, prefix="/api/v1")  # /api/v1/ask, /models, /schema
    app.include_router(ui.router)  # /
    return app


app = create_app()

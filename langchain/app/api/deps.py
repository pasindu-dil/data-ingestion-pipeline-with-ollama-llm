"""FastAPI dependencies. Tests can override these via app.dependency_overrides."""

from fastapi import Request

from app.core.config import Settings
from app.core.container import Container
from app.services.backend import BackendRegistry
from app.services.health_service import HealthService
from app.services.query_service import QueryService


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


def get_query_service(request: Request) -> QueryService:
    return get_container(request).query_service


def get_registry(request: Request) -> BackendRegistry:
    return get_container(request).registry


def get_health_service(request: Request) -> HealthService:
    return get_container(request).health_service


def get_app_settings(request: Request) -> Settings:
    return get_container(request).settings

"""A Backend bundles everything that differs per datastore (Strategy pattern)."""

from dataclasses import dataclass
from typing import Protocol

from app.core.exceptions import UnknownSourceError
from app.repositories.base import QueryExecutor
from app.services.schema_service import SchemaService


class QueryValidator(Protocol):
    def validate(self, raw: str, limit: int) -> str: ...


@dataclass
class Backend:
    name: str  # "clickhouse" | "elasticsearch"  (the `source` API value)
    language: str  # shown to the LLM, e.g. "ClickHouse SQL" or "ES|QL"
    rules: str  # dialect-specific prompt rules
    schema: SchemaService
    validator: QueryValidator
    repo: QueryExecutor


class BackendRegistry:
    def __init__(self, backends: dict[str, Backend], default: str):
        if default not in backends:
            raise ValueError(f"DEFAULT_SOURCE '{default}' is not configured: {list(backends)}")
        self._backends = backends
        self.default = default

    @property
    def names(self) -> list[str]:
        return list(self._backends)

    def all(self) -> list[Backend]:
        return list(self._backends.values())

    def get(self, name: str | None = None) -> Backend:
        name = name or self.default
        try:
            return self._backends[name]
        except KeyError:
            raise UnknownSourceError(
                f"Unknown source '{name}'. Choose one of: {self.names}"
            ) from None

    def warm_up(self) -> None:
        for b in self._backends.values():
            b.schema.get(force=True)  # fail fast if a datastore is unusable

    def close(self) -> None:
        for b in self._backends.values():
            b.repo.close()

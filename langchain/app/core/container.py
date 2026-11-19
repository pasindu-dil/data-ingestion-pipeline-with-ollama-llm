"""Composition root: the only place where concrete classes are wired together."""

from dataclasses import dataclass

from app.core.config import Settings
from app.repositories.clickhouse_repo import ClickHouseRepository
from app.repositories.elasticsearch_repo import ElasticsearchRepository
from app.services.backend import Backend, BackendRegistry
from app.services.context_service import ContextService
from app.services.dialects import CLICKHOUSE_RULES, ESQL_RULES
from app.services.esql_validator import EsqlValidator
from app.services.health_service import HealthService
from app.services.llm_service import OllamaQueryGenerator
from app.services.query_service import QueryService
from app.services.schema_service import SchemaService
from app.services.sql_validator import SqlValidator


@dataclass
class Container:
    settings: Settings
    registry: BackendRegistry
    query_service: QueryService
    health_service: HealthService


def _clickhouse(s: Settings) -> Backend:
    repo = ClickHouseRepository.connect(s)
    return Backend(
        "clickhouse",
        "ClickHouse SQL",
        CLICKHOUSE_RULES,
        SchemaService(repo.describe_schema, s.schema_ttl_seconds),
        SqlValidator(),
        repo,
    )


def _elasticsearch(s: Settings) -> Backend:
    repo = ElasticsearchRepository.connect(s)
    return Backend(
        "elasticsearch",
        "ES|QL (Elasticsearch)",
        ESQL_RULES,
        SchemaService(repo.describe_schema, s.schema_ttl_seconds),
        EsqlValidator(s.es_index_patterns),
        repo,
    )


def build_container(settings: Settings) -> Container:
    backends: dict[str, Backend] = {}
    if settings.clickhouse_enabled:
        backends["clickhouse"] = _clickhouse(settings)
    if settings.elasticsearch_enabled:
        backends["elasticsearch"] = _elasticsearch(settings)
    if not backends:
        raise RuntimeError("No data source configured: set CH_HOST+CH_DB and/or ES_URL+ES_INDICES")

    registry = BackendRegistry(backends, settings.default_source or next(iter(backends)))
    query_service = QueryService(
        settings=settings,
        registry=registry,
        context_service=ContextService(settings.context_dir),
        generator=OllamaQueryGenerator(settings.ollama_url),
    )
    return Container(
        settings, registry, query_service, HealthService(registry, settings.ollama_url)
    )

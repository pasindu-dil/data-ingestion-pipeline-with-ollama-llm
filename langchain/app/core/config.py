"""Typed, validated settings. A datastore is enabled when its settings are present."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    # shared
    connect_attempts: int = 30
    connect_delay: int = 3
    max_execution_time: int = 30  # seconds, enforced server-side per query
    default_source: str | None = None  # defaults to the first enabled backend

    # ClickHouse (enabled when CH_HOST and CH_DB are set)
    ch_host: str | None = None
    ch_user: str = "default"
    ch_password: str = ""
    ch_db: str = ""  # one database or comma separated list, e.g. "otel,logs"

    # Elasticsearch (enabled when ES_URL and ES_INDICES are set)
    es_url: str | None = None
    es_indices: str = ""  # comma separated index patterns, e.g. "logs-*,app-*"
    es_api_key: str | None = None
    es_user: str | None = None
    es_password: str | None = None
    es_verify_certs: bool = True
    es_ca_certs: str | None = None

    # Ollama / LLM
    ollama_url: str
    default_model: str = Field(validation_alias=AliasChoices("MODEL", "default_model"))
    models: str = ""  # comma separated allowlist; empty -> only default model

    # Behaviour
    schema_ttl_seconds: int = 300
    default_row_limit: int = 1000
    max_row_limit: int = 10000
    context_dir: str = "/app/context"
    map_sample_rows: int = 10000
    map_max_keys: int = 40
    log_level: str = "INFO"

    @staticmethod
    def _split(v: str) -> list[str]:
        return [x.strip() for x in v.split(",") if x.strip()]

    @property
    def databases(self) -> list[str]:
        return self._split(self.ch_db)

    @property
    def es_index_patterns(self) -> list[str]:
        return self._split(self.es_indices)

    @property
    def clickhouse_enabled(self) -> bool:
        return bool(self.ch_host and self.databases)

    @property
    def elasticsearch_enabled(self) -> bool:
        return bool(self.es_url and self.es_index_patterns)

    @property
    def allowed_models(self) -> list[str]:
        return self._split(self.models) or [self.default_model]


@lru_cache
def get_settings() -> Settings:
    return Settings()

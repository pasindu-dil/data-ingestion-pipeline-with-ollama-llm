"""All Elasticsearch access lives here. Queries are ES|QL (needs ES 8.14+ / 9.x).
ES|QL has no write commands, so it is read-only by construction."""

import logging
import time
from typing import Any

from elasticsearch import Elasticsearch

from app.core.config import Settings
from app.repositories.base import RawResult

log = logging.getLogger(__name__)


def flatten_properties(props: dict[str, Any], prefix: str, out: dict[str, str]) -> None:
    """Turn a nested mapping into {"a.b.c": "type"}."""
    for name, spec in props.items():
        path = f"{prefix}{name}"
        if "properties" in spec:
            flatten_properties(spec["properties"], f"{path}.", out)
        else:
            out[path] = spec.get("type", "object")


class ElasticsearchRepository:
    def __init__(self, client: Elasticsearch, patterns: list[str], timeout: int):
        self._client = client
        self._patterns = patterns
        self._timeout = timeout

    @classmethod
    def connect(cls, s: Settings) -> "ElasticsearchRepository":
        
        kwargs: dict[str, Any] = {"verify_certs": s.es_verify_certs}
        if s.es_ca_certs:
            kwargs["ca_certs"] = s.es_ca_certs
        if s.es_api_key:
            kwargs["api_key"] = s.es_api_key
        elif s.es_user:
            kwargs["basic_auth"] = (s.es_user, s.es_password or "")
        client = Elasticsearch(s.es_url, **kwargs)
        last: Exception | None = None
        for i in range(1, s.connect_attempts + 1):
            try:
                client.info()
                return cls(client, s.es_index_patterns, s.max_execution_time)
            except Exception as e:
                last = e
                log.warning("Elasticsearch not ready (%d/%d): %s", i, s.connect_attempts, e)
                time.sleep(s.connect_delay)
        raise RuntimeError(f"Elasticsearch unreachable after {s.connect_attempts} attempts: {last}")

    def ping(self) -> None:
        self._client.info()  # raises on failure (client.ping() would swallow errors)

    def close(self) -> None:
        self._client.close()

    def describe_schema(self) -> str:
        """One block per configured index pattern, with the union of fields of its indices."""
        blocks = []
        for pattern in self._patterns:
            resp = self._client.indices.get_mapping(index=pattern)
            mappings = getattr(resp, "body", resp)
            fields: dict[str, str] = {}
            for index_mapping in mappings.values():
                flatten_properties(
                    index_mapping.get("mappings", {}).get("properties", {}), "", fields
                )
            lines = [f"  {name} {typ}" for name, typ in sorted(fields.items())]
            blocks.append(f"INDEX {pattern} (\n" + ",\n".join(lines) + "\n)")
        return "\n".join(blocks)

    def execute_readonly(self, query: str) -> RawResult:
        res = self._client.options(request_timeout=self._timeout).esql.query(
            query=query, format="json"
        )
        body = getattr(res, "body", res)
        return RawResult(
            columns=[c["name"] for c in body["columns"]],
            rows=[tuple(r) for r in body["values"]],
        )

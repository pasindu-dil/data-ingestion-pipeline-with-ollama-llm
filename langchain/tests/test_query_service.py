from types import SimpleNamespace

import pytest
from app.core.exceptions import ModelNotAllowedError, QueryGenerationError, UnknownSourceError
from app.repositories.base import RawResult
from app.services.backend import Backend, BackendRegistry
from app.services.esql_validator import EsqlValidator
from app.services.query_service import QueryService
from app.services.sql_validator import SqlValidator


class FakeGen:
    def __init__(self, outputs):
        self.outputs, self.calls = list(outputs), []

    def generate(self, **kw):
        self.calls.append(kw)
        return self.outputs.pop(0)


class FakeRepo:
    def execute_readonly(self, q):
        return RawResult(["n"], [(1,)])


def backend(name, language, validator):
    return Backend(
        name,
        language,
        "rules",
        SimpleNamespace(get=lambda force=False: f"{name}-schema"),
        validator,
        FakeRepo(),
    )


def make(outputs):
    reg = BackendRegistry(
        {
            "clickhouse": backend("clickhouse", "ClickHouse SQL", SqlValidator()),
            "elasticsearch": backend("elasticsearch", "ES|QL", EsqlValidator(["logs-*"])),
        },
        default="clickhouse",
    )
    settings = SimpleNamespace(default_model="m", allowed_models=["m"], default_row_limit=100)
    ctx = SimpleNamespace(load=lambda source: ("", ""))
    gen = FakeGen(outputs)
    return QueryService(settings=settings, registry=reg, context_service=ctx, generator=gen), gen


def test_default_source_is_used():
    svc, gen = make(["SELECT 1 FROM db.t"])
    out = svc.ask("how many?", None, None, None, 2)
    assert (
        out.source == "clickhouse"
        and out.attempts == 1
        and gen.calls[0]["language"] == "ClickHouse SQL"
    )


def test_routes_to_elasticsearch_with_its_prompt_and_schema():
    svc, gen = make(["FROM logs-* | STATS c = COUNT(*)"])
    out = svc.ask("how many?", "elasticsearch", None, None, 2)
    assert out.source == "elasticsearch" and out.sql.endswith("| LIMIT 100")
    assert gen.calls[0]["language"] == "ES|QL" and gen.calls[0]["schema"] == "elasticsearch-schema"


def test_self_correction_feeds_error_back():
    svc, gen = make(["FROM secret-* | LIMIT 1", "FROM logs-* | LIMIT 1"])
    out = svc.ask("how many?", "elasticsearch", None, None, 2)
    assert out.attempts == 2 and "not allowed" in gen.calls[1]["question"]


def test_gives_up_after_retries():
    svc, _ = make(["DROP TABLE x"] * 3)
    with pytest.raises(QueryGenerationError):
        svc.ask("how many?", "clickhouse", None, None, 2)


def test_model_allowlist_and_unknown_source():
    svc, _ = make([])
    with pytest.raises(ModelNotAllowedError):
        svc.ask("how many?", None, "evil", None, 0)
    with pytest.raises(UnknownSourceError):
        svc.ask("how many?", "mongo", None, None, 0)

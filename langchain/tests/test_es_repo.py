from types import SimpleNamespace

from app.repositories.elasticsearch_repo import ElasticsearchRepository, flatten_properties


def test_flatten_nested_properties():
    out: dict[str, str] = {}
    flatten_properties(
        {
            "@timestamp": {"type": "date"},
            "log": {"properties": {"level": {"type": "keyword"}}},
            "message": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
        },
        "",
        out,
    )
    assert out == {"@timestamp": "date", "log.level": "keyword", "message": "text"}


class FakeIndices:
    def get_mapping(self, index):
        return SimpleNamespace(
            body={
                "logs-2024.01": {"mappings": {"properties": {"a": {"type": "keyword"}}}},
                "logs-2024.02": {"mappings": {"properties": {"b": {"type": "long"}}}},
            }
        )


class FakeEsql:
    def query(self, query, format):
        assert format == "json"
        return SimpleNamespace(
            body={"columns": [{"name": "n", "type": "long"}], "values": [[1], [2]]}
        )


class FakeClient:
    indices = FakeIndices()
    esql = FakeEsql()

    def options(self, **kw):
        return self


def test_describe_schema_merges_indices_per_pattern():
    text = ElasticsearchRepository(FakeClient(), ["logs-*"], 30).describe_schema()
    assert text.startswith("INDEX logs-* (") and "a keyword" in text and "b long" in text


def test_execute_maps_columns_and_rows():
    res = ElasticsearchRepository(FakeClient(), ["logs-*"], 30).execute_readonly("FROM logs-*")
    assert res.columns == ["n"] and res.rows == [(1,), (2,)]

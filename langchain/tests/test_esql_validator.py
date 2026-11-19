import pytest
from app.core.exceptions import InvalidSQLError
from app.services.esql_validator import EsqlValidator

v = EsqlValidator(["logs-*", "app-*"])


def test_adds_limit_and_strips_fences():
    out = v.validate("```esql\nFROM logs-* | WHERE x == 1\n```", 50)
    assert out.endswith("| LIMIT 50") and "```" not in out


def test_keeps_existing_limit():
    q = "FROM logs-* | LIMIT 5"
    assert v.validate(q, 50) == q


def test_narrower_pattern_and_multiple_indices_ok():
    v.validate("FROM logs-app*,app-1 | LIMIT 1", 10)


@pytest.mark.parametrize(
    "q",
    [
        "FROM secrets-* | LIMIT 1",  # index not allowed
        "FROM *",  # too broad
        "FROM logs-*,secret | LIMIT 1",  # one bad index in the list
        "ROW a = 1",  # not a FROM query
        "FROM logs-* | LOOKUP JOIN x ON y",  # can reach other indices
        "FROM logs-* | ENRICH policy",
    ],
)
def test_rejects(q):
    with pytest.raises(InvalidSQLError):
        v.validate(q, 10)

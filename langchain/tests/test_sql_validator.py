import pytest
from app.core.exceptions import InvalidSQLError
from app.services.sql_validator import SqlValidator

v = SqlValidator()


def test_adds_limit_and_strips_fences():
    out = v.validate("```sql\nSELECT 1 FROM db.t;\n```", 50)
    assert out.endswith("LIMIT 50") and "```" not in out


def test_keeps_existing_limit():
    assert v.validate("SELECT 1 FROM db.t LIMIT 5", 50) == "SELECT 1 FROM db.t LIMIT 5"


def test_union_allowed():
    v.validate("SELECT 1 UNION ALL SELECT 2", 10)


@pytest.mark.parametrize(
    "sql", ["DROP TABLE db.t", "INSERT INTO db.t VALUES (1)", "SELECT 1; SELECT 2"]
)
def test_rejects_non_select_or_multi(sql):
    with pytest.raises(InvalidSQLError):
        v.validate(sql, 10)

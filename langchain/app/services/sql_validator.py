import re

import sqlglot
from sqlglot import exp

from app.core.exceptions import InvalidSQLError

_FENCE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE)


class SqlValidator:
    """Validates that LLM output is a single SELECT and adds a LIMIT if missing.
    The SQL text is kept exactly as written (only validated, never re-generated)."""

    def validate(self, raw_sql: str, limit: int) -> str:
        sql = _FENCE.sub("", raw_sql.strip()).strip().rstrip(";").strip()
        statements = [s for s in sqlglot.parse(sql, read="clickhouse") if s is not None]
        if len(statements) != 1:
            raise InvalidSQLError("Exactly one statement is allowed")
        tree = statements[0]
        if not isinstance(tree, (exp.Select, exp.Union)):
            raise InvalidSQLError("Only SELECT statements are allowed")
        if tree.args.get("limit") is None:
            sql = f"{sql}\nLIMIT {limit}"
        return sql

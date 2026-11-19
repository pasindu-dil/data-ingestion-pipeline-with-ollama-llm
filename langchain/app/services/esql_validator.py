import fnmatch
import re

from app.core.exceptions import InvalidSQLError

_FENCE = re.compile(r"^```(?:esql|sql)?\s*|\s*```$", re.IGNORECASE)
_FROM = re.compile(r"^\s*FROM\s+([^\s|]+)", re.IGNORECASE)
_LIMIT = re.compile(r"\|\s*LIMIT\s+\d+", re.IGNORECASE)
# commands that can pull data from indices outside the FROM clause
_FORBIDDEN = re.compile(r"\b(LOOKUP|ENRICH)\b", re.IGNORECASE)


class EsqlValidator:
    """Keeps generated ES|QL inside the configured index patterns and adds a LIMIT."""

    def __init__(self, allowed_patterns: list[str]):
        self._allowed = allowed_patterns

    def validate(self, raw: str, limit: int) -> str:
        q = _FENCE.sub("", raw.strip()).strip().rstrip(";").strip()
        m = _FROM.match(q)
        if not m:
            raise InvalidSQLError("ES|QL query must start with FROM <index>")
        for idx in m.group(1).strip("\"'`").split(","):
            idx = idx.strip("\"'`")
            if not any(fnmatch.fnmatch(idx, p) for p in self._allowed):
                raise InvalidSQLError(f"Index '{idx}' is not allowed. Allowed: {self._allowed}")
        if _FORBIDDEN.search(q):
            raise InvalidSQLError("LOOKUP and ENRICH are not allowed")
        if not _LIMIT.search(q):
            q = f"{q}\n| LIMIT {limit}"
        return q

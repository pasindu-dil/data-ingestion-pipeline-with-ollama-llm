from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class RawResult:
    columns: list[str]
    rows: list[tuple[Any, ...]]


class QueryExecutor(Protocol):
    """What the rest of the app needs from any datastore."""

    def execute_readonly(self, query: str) -> RawResult: ...
    def describe_schema(self) -> str: ...
    def ping(self) -> None: ...
    def close(self) -> None: ...

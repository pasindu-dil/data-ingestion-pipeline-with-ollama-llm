"""All ClickHouse access lives here. Nothing else imports clickhouse_connect."""

import logging
import time
from dataclasses import dataclass

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from app.core.config import Settings
from app.repositories.base import RawResult

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ColumnInfo:
    database: str
    table: str
    name: str
    type: str
    comment: str


class ClickHouseRepository:
    def __init__(
        self,
        client: Client,
        databases: list[str],
        map_sample_rows: int,
        map_max_keys: int,
        max_execution_time: int,
    ):
        self._client = client
        self._dbs = databases
        self._map_sample_rows = map_sample_rows
        self._map_max_keys = map_max_keys
        self._max_execution_time = max_execution_time

    @classmethod
    def connect(cls, s: Settings) -> "ClickHouseRepository":
        """Wait for ClickHouse to come up (it can take a while on first start)."""
        last: Exception | None = None
        for i in range(1, s.connect_attempts + 1):
            try:
                # autogenerate_session_id=False lets one client be shared across threads
                client = clickhouse_connect.get_client(
                    host=s.ch_host,
                    username=s.ch_user,
                    password=s.ch_password,
                    database=s.databases[0],
                    autogenerate_session_id=False,
                )
                return cls(
                    client, s.databases, s.map_sample_rows, s.map_max_keys, s.max_execution_time
                )
            except Exception as e:
                last = e
                log.warning("ClickHouse not ready (%d/%d): %s", i, s.connect_attempts, e)
                time.sleep(s.connect_delay)
        raise RuntimeError(f"ClickHouse unreachable after {s.connect_attempts} attempts: {last}")

    def ping(self) -> None:
        self._client.query("SELECT 1")

    def close(self) -> None:
        self._client.close()

    def fetch_columns(self) -> list[ColumnInfo]:
        rows = self._client.query(
            "SELECT database, table, name, type, comment FROM system.columns "
            "WHERE database IN {dbs:Array(String)} ORDER BY database, table, position",
            parameters={"dbs": self._dbs},
        ).result_rows
        return [ColumnInfo(*r) for r in rows]

    def sample_map_keys(self, db: str, table: str, col: str) -> list[str]:
        """Map keys are not in system.columns, so sample the table to find the common ones."""
        try:
            rows = self._client.query(
                f"SELECT arrayJoin(mapKeys(`{col}`)) AS k, count() AS c "
                f"FROM (SELECT `{col}` FROM `{db}`.`{table}` LIMIT {self._map_sample_rows}) "
                f"GROUP BY k ORDER BY c DESC LIMIT {self._map_max_keys}"
            ).result_rows
            return [r[0] for r in rows]
        except Exception as e:
            log.warning("could not sample keys of %s.%s.%s: %s", db, table, col, e)
            return []

    def describe_schema(self) -> str:
        tables: dict[str, list[str]] = {}
        for c in self.fetch_columns():
            notes = [c.comment] if c.comment else []
            if c.type.startswith("Map("):
                keys = self.sample_map_keys(c.database, c.table, c.name)
                if keys:
                    notes.append("keys seen: " + ", ".join(keys))
            line = f"  {c.name} {c.type}"
            if notes:
                line += "  -- " + "; ".join(notes)
            tables.setdefault(f"{c.database}.{c.table}", []).append(line)
        return "\n".join(f"TABLE {t} (\n" + ",\n".join(cols) + "\n)" for t, cols in tables.items())

    def execute_readonly(self, query: str) -> RawResult:
        """Defence in depth: besides the SQL validator, ClickHouse itself refuses writes.
        readonly=2 forbids writes/DDL but still allows per-query settings."""
        res = self._client.query(
            query, settings={"readonly": 2, "max_execution_time": self._max_execution_time}
        )
        return RawResult(columns=list(res.column_names), rows=[tuple(r) for r in res.result_rows])

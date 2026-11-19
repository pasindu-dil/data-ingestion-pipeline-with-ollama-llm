from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    source: str | None = None  # "clickhouse" | "elasticsearch"; None -> default source
    model: str | None = None
    limit: int | None = Field(None, ge=1, le=10000)  # None -> DEFAULT_ROW_LIMIT
    retries: int = Field(2, ge=0, le=5)


class AskResponse(BaseModel):
    sql: str  # the generated query (SQL or ES|QL)
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    attempts: int
    model: str
    source: str


class ModelsResponse(BaseModel):
    default: str
    allowed: list[str]
    sources: list[str]
    default_source: str

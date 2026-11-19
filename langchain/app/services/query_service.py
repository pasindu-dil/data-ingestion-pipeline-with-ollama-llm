"""Use case: natural-language question -> validated query -> rows, with self-correcting retries."""

import logging
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.core.exceptions import ModelNotAllowedError, QueryGenerationError
from app.services.backend import BackendRegistry
from app.services.context_service import ContextService
from app.services.llm_service import QueryGenerator
from app.utils.serialization import to_json

log = logging.getLogger(__name__)


@dataclass
class QueryOutcome:
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    attempts: int
    model: str
    source: str


class QueryService:
    def __init__(
        self,
        *,
        settings: Settings,
        registry: BackendRegistry,
        context_service: ContextService,
        generator: QueryGenerator,
    ):
        self._s = settings
        self._registry = registry
        self._context = context_service
        self._generator = generator

    def ask(
        self, question: str, source: str | None, model: str | None, limit: int | None, retries: int
    ) -> QueryOutcome:
        model = model or self._s.default_model
        if model not in self._s.allowed_models:
            raise ModelNotAllowedError(
                f"Model not allowed. Choose one of: {self._s.allowed_models}"
            )
        backend = self._registry.get(source)
        limit = limit or self._s.default_row_limit

        schema = backend.schema.get()
        notes, examples = self._context.load(backend.name)
        prompt_question = question
        last_error = "No query produced"

        for attempt in range(1, retries + 2):
            raw = self._generator.generate(
                model=model,
                language=backend.language,
                rules=backend.rules,
                schema=schema,
                notes=notes,
                examples=examples,
                question=prompt_question,
            )
            try:
                query = backend.validator.validate(raw, limit)
                res = backend.repo.execute_readonly(query)
                return QueryOutcome(
                    sql=query,
                    columns=res.columns,
                    rows=[[to_json(c) for c in r] for r in res.rows],
                    row_count=len(res.rows),
                    attempts=attempt,
                    model=model,
                    source=backend.name,
                )
            except Exception as e:  # feed the error back so the model can self-correct
                last_error = str(e)
                log.info("attempt %d failed: %s", attempt, e)
                prompt_question = (
                    f"{question}\n\nPrevious query:\n{raw}\nError: {e}\nFix the query."
                )
        raise QueryGenerationError(f"Could not produce a valid query: {last_error}")

from functools import lru_cache
from typing import Protocol

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama

SYSTEM_PROMPT = (
    "You are an expert in {language}. Using ONLY the schema below, write one "
    "read-only {language} query that answers the question.\n"
    "Rules:\n"
    "{rules}\n"
    "- Follow the style of the examples.\n"
    "- Return only the query, no markdown, no explanation.\n\n"
    "SCHEMA:\n{schema}\n\nNOTES:\n{notes}\n\nEXAMPLES:\n{examples}"
)


class QueryGenerator(Protocol):
    """Interface QueryService depends on, so tests can swap in a fake."""

    def generate(
        self,
        *,
        model: str,
        language: str,
        rules: str,
        schema: str,
        notes: str,
        examples: str,
        question: str,
    ) -> str: ...


class OllamaQueryGenerator:
    def __init__(self, base_url: str):
        self._base_url = base_url
        self._prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_PROMPT), ("human", "{question}")]
        )
        self._chain = lru_cache(maxsize=8)(self._build_chain)

    def _build_chain(self, model: str) -> Runnable[dict[str, str], str]:
        llm = ChatOllama(model=model, base_url=self._base_url, temperature=0)
        return self._prompt | llm | StrOutputParser()

    def generate(
        self,
        *,
        model: str,
        language: str,
        rules: str,
        schema: str,
        notes: str,
        examples: str,
        question: str,
    ) -> str:
        result: str = self._chain(model).invoke(
            {
                "language": language,
                "rules": rules,
                "schema": schema,
                "notes": notes,
                "examples": examples,
                "question": question,
            }
        )
        return result

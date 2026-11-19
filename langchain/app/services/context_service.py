import json
import os


class ContextService:
    """notes.txt (free text hints) and examples.json (question -> query pairs).
    Looked up in CONTEXT_DIR/<source>/ first. ClickHouse also falls back to the
    old flat layout (CONTEXT_DIR/notes.txt) so existing mounts keep working."""

    def __init__(self, context_dir: str):
        self._dir = context_dir

    def _candidates(self, source: str, filename: str) -> list[str]:
        paths = [os.path.join(self._dir, source, filename)]
        if source == "clickhouse":
            paths.append(os.path.join(self._dir, filename))
        return paths

    def _first_existing(self, source: str, filename: str) -> str | None:
        return next((p for p in self._candidates(source, filename) if os.path.isfile(p)), None)

    def load(self, source: str) -> tuple[str, str]:
        notes, examples = "", ""
        if p := self._first_existing(source, "notes.txt"):
            with open(p, encoding="utf-8") as f:
                notes = f.read().strip()
        if p := self._first_existing(source, "examples.json"):
            with open(p, encoding="utf-8") as f:
                items = json.load(f)
            examples = "\n\n".join(
                f"Question: {i['question']}\nQuery:\n{i['sql'].strip()}" for i in items
            )
        return notes, examples

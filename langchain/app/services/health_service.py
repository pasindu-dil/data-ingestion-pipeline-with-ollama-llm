import urllib.request

from app.services.backend import BackendRegistry


class HealthService:
    def __init__(self, registry: BackendRegistry, ollama_url: str):
        self._registry = registry
        self._ollama_url = ollama_url

    def check(self) -> dict[str, bool]:
        status: dict[str, bool] = {}
        for b in self._registry.all():
            try:
                b.repo.ping()
                status[b.name] = True
            except Exception:
                status[b.name] = False
        try:
            urllib.request.urlopen(f"{self._ollama_url}/api/tags", timeout=3).read()
            status["ollama"] = True
        except Exception:
            status["ollama"] = False
        return status

from types import SimpleNamespace

from app.core.exceptions import UnknownSourceError
from app.main import create_app
from app.services.query_service import QueryOutcome
from fastapi.testclient import TestClient


def make_client():
    app = create_app()  # TestClient without `with` skips lifespan -> no datastore needed
    backend = SimpleNamespace(
        name="elasticsearch",
        language="ES|QL",
        schema=SimpleNamespace(get=lambda force=False: "INDEX logs-* ()"),
    )

    def get(name=None):
        if name not in (None, "elasticsearch"):
            raise UnknownSourceError("Unknown source")
        return backend

    registry = SimpleNamespace(names=["elasticsearch"], default="elasticsearch", get=get)
    settings = SimpleNamespace(default_model="m", allowed_models=["m"])
    qs = SimpleNamespace(
        ask=lambda q, s, m, limit, r: QueryOutcome(
            "FROM x", ["n"], [[1]], 1, 1, "m", "elasticsearch"
        )
    )
    health = SimpleNamespace(check=lambda: {"elasticsearch": True, "ollama": False})
    app.state.container = SimpleNamespace(
        settings=settings, registry=registry, query_service=qs, health_service=health
    )
    return TestClient(app)


def test_ask_models_schema_ui():
    c = make_client()
    r = c.post("/api/v1/ask", json={"question": "how many rows?", "source": "elasticsearch"}).json()
    assert r["row_count"] == 1 and r["source"] == "elasticsearch"
    m = c.get("/api/v1/models").json()
    assert m["sources"] == ["elasticsearch"] and m["default_source"] == "elasticsearch"
    assert c.get("/api/v1/schema?source=elasticsearch").json()["schema"].startswith("INDEX")
    assert "Text to Query" in c.get("/").text


def test_unknown_source_is_400():
    assert make_client().get("/api/v1/schema?source=mongo").status_code == 400


def test_health_503_when_dependency_down():
    assert make_client().get("/health").status_code == 503

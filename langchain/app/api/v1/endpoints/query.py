from fastapi import APIRouter, Depends

from app.api.deps import get_query_service
from app.schemas.query import AskRequest, AskResponse
from app.services.query_service import QueryOutcome, QueryService

router = APIRouter(tags=["query"])


# plain `def` endpoints run in FastAPI's threadpool, so the blocking LLM and
# datastore calls don't freeze the event loop
@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, service: QueryService = Depends(get_query_service)) -> QueryOutcome:
    return service.ask(req.question, req.source, req.model, req.limit, req.retries)

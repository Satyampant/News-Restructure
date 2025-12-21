from typing import Optional
from fastapi import APIRouter, Query, Depends
from src.interfaces.rest.schemas.responses import QueryResponse
from src.application.use_cases.execute_query import ExecuteQueryUseCase
from src.interfaces.rest.dependencies import get_execute_query_use_case

router = APIRouter()

@router.get("/query", response_model=QueryResponse)
async def query_articles(
    q: str = Query(..., description="Natural language query"),
    top_k: int = Query(10, ge=1, le=50),
    filter_by_sentiment: Optional[str] = Query(None),
    use_case: ExecuteQueryUseCase = Depends(get_execute_query_use_case)
):
    """Search articles using natural language query."""
    result = use_case.execute(q, top_k, filter_by_sentiment)
    
    return QueryResponse(
        query=q,
        results_count=len(result.get("articles", [])),
        articles=result.get("articles", []),
        stats=result.get("stats", {})
    )
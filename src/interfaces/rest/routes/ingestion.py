from fastapi import APIRouter, HTTPException, Depends
from src.interfaces.rest.schemas.requests import ArticleInput
from src.interfaces.rest.schemas.responses import IngestResponse
from src.application.use_cases.process_article import ProcessArticleUseCase
from src.domain.models.article import NewsArticle

from src.interfaces.rest.dependencies import get_process_article_use_case

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_article(
    article_input: ArticleInput,
    use_case: ProcessArticleUseCase = Depends(get_process_article_use_case)
):
    """Ingest a financial news article."""
    try:
        article = NewsArticle(
            id=article_input.id,
            title=article_input.title,
            content=article_input.content,
            source=article_input.source,
            timestamp=article_input.timestamp
        )
        
        # Add raw_text if present in input, though strictly domain model might not have it defined in Phase 1
        # adhering to the snippet which constructs NewsArticle directly.
        
        result = use_case.execute(article)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        final_stats = result.get("stats", {})

        return IngestResponse(
            success=True,
            article_id=article.id,
            message="Article processed successfully",
            is_duplicate=final_stats.get("is_duplicate", False),
            duplicates_found=final_stats.get("duplicates_found", 0),
            entities_extracted=final_stats.get("entities_extracted", {}),
            stocks_impacted=final_stats.get("stocks_impacted", 0),
            
            # Map optional fields
            sentiment_classification=final_stats.get("sentiment_classification"),
            sentiment_confidence=final_stats.get("sentiment_confidence"),
            signal_strength=final_stats.get("sentiment_signal_strength"),
            
            stats=final_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
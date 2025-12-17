from fastapi import APIRouter, HTTPException, Depends
from src.infrastructure.storage.mongodb.article_repository import ArticleRepository

router = APIRouter()

@router.get("/article/{article_id}")
async def get_article(
    article_id: str,
    repo: ArticleRepository = Depends()
):
    """Retrieve article by ID with full analysis."""
    article = repo.get_article_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Construct response matching the legacy API contract where possible
    response = {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "source": article.source,
        "timestamp": article.timestamp,
        "entities": getattr(article, "entities", None),
        "impacted_stocks": getattr(article, "impacted_stocks", None),
        "sentiment": getattr(article, "sentiment", None),
        "cross_impacts": getattr(article, "cross_impacts", [])
    }

    # Add rich entity data if available
    if hasattr(article, "entities_rich") and article.entities_rich:
        response["entities_rich"] = article.entities_rich
    
    # Add sentiment details
    if hasattr(article, "sentiment") and article.sentiment:
        sentiment_data = article.sentiment
        if isinstance(sentiment_data, dict):
            breakdown = sentiment_data.get("sentiment_breakdown", {})
            if breakdown and "key_factors" in breakdown:
                response["sentiment_key_factors"] = breakdown["key_factors"]

    return response

@router.get("/article/{article_id}/sentiment")
async def get_article_sentiment(
    article_id: str,
    repo: ArticleRepository = Depends()
):
    """Get sentiment analysis details."""
    article = repo.get_article_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    if not hasattr(article, "sentiment") or not article.sentiment:
        raise HTTPException(status_code=404, detail="No sentiment data for article")

    return article.sentiment
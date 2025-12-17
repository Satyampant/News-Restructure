from fastapi import APIRouter, Depends
from src.infrastructure.storage.mongodb.article_repository import ArticleRepository
from src.infrastructure.storage.mongodb.queries import (
    build_sentiment_aggregation_pipeline,
    build_supply_chain_aggregation_pipeline
)

router = APIRouter()

@router.get("/stats")
async def get_stats(repo: ArticleRepository = Depends()):
    """Retrieve system statistics."""
    # Using the repository to access the underlying collection for aggregations
    # Note: In a stricter repository pattern, these would be methods on the repository itself,
    # but strictly following the migration plan snippet which imports the pipeline builders here.
    
    try:
        # Assuming ArticleRepository exposes the collection or a method to execute pipelines
        collection = repo.collection
        
        # Execute sentiment aggregation
        sentiment_pipeline = build_sentiment_aggregation_pipeline()
        sentiment_stats = list(collection.aggregate(sentiment_pipeline))
        
        # Execute supply chain aggregation
        supply_chain_pipeline = build_supply_chain_aggregation_pipeline()
        supply_chain_stats = list(collection.aggregate(supply_chain_pipeline))
        
        # Get total count
        total_articles = collection.count_documents({})
        
        return {
            "total_articles": total_articles,
            "sentiment_stats": sentiment_stats,
            "supply_chain_stats": supply_chain_stats
        }
    except Exception as e:
        # In case of database errors, return minimal stats or raise
        return {
            "error": str(e),
            "total_articles": 0
        }
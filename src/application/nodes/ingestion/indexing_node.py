from src.application.workflows.state import NewsIntelligenceState
from src.infrastructure.storage.mongodb.article_repository import ArticleRepository
from src.infrastructure.storage.vector.chroma_client import ChromaDBClient
import logging

logger = logging.getLogger(__name__)

class IndexingNode:
    """Persists processed article to databases."""
    
    def __init__(
        self,
        article_repo: ArticleRepository,
        vector_store: ChromaDBClient
    ):
        self.repo = article_repo
        self.vector = vector_store
        
    def process(self, state: NewsIntelligenceState) -> dict:
        """Execute indexing logic."""
        article = state["current_article"]
        article_embedding = state.get("article_embedding")
        
        # Insert into MongoDB
        mongo_id = self.repo.insert_article(article)
        
        # Index in ChromaDB
        if article_embedding:
            self.vector.index_article(
                article_id=article.id, 
                embedding=article_embedding
            )
        else:
            logger.warning(f"Skipping vector indexing for article {article.id}: No embedding provided.")
        
        stats = {
            "indexed": True,
            "indexed_in_mongo": bool(mongo_id),
            "indexed_in_chroma": article_embedding is not None,
            "embedding_reused": article_embedding is not None,
        }
        
        return {
            "articles": [article],
            "stats": stats
        }
from src.application.workflows.state import NewsIntelligenceState
from src.infrastructure.storage.mongodb.article_repository import ArticleRepository
from src.infrastructure.storage.vector.chroma_client import ChromaDBClient

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
            self.vector.index_article(article, embedding=article_embedding)
        else:
            # Fallback computation if missing (should be caught earlier, but safe to keep)
            self.vector.index_article(article)
        
        stats = {
            "indexed": True,
            "indexed_in_mongo": bool(mongo_id),
            "indexed_in_chroma": True,
            "embedding_reused": article_embedding is not None,
            # Note: repository might not expose total count directly for performance
            # ignoring article_count() to keep node logic pure
        }
        
        return {
            "articles": [article],
            "stats": stats
        }
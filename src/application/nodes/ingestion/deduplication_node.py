from src.application.workflows.state import NewsIntelligenceState
from src.application.agents.deduplication_agent import DeduplicationAgent
from src.infrastructure.storage.mongodb.article_repository import ArticleRepository
from src.infrastructure.storage.vector.chroma_client import ChromaDBClient

class DeduplicationNode:
    """Finds and consolidates duplicate articles."""
    
    def __init__(
        self,
        dedup_agent: DeduplicationAgent,
        article_repo: ArticleRepository,
        vector_store: ChromaDBClient
    ):
        self.dedup = dedup_agent
        self.repo = article_repo
        self.vector = vector_store
    
    def process(self, state: NewsIntelligenceState) -> dict:
        """Execute deduplication logic."""
        article = state["current_article"]
        embedding = state["article_embedding"]
        
        if not embedding:
            # Fallback if embedding missing (though IngestionNode guarantees it)
            return {"duplicates": [], "stats": {"error": "Missing embedding"}}

        # Find duplicates using vector search + MongoDB hydration
        duplicate_ids = self.dedup.find_duplicates(
            article,
            embedding,
            self.vector,
            self.repo
        )
        
        stats = {
            "is_duplicate": False, 
            "duplicates_found": 0,
            "deduplication_method": "vector_search_with_mongodb_hydration"
        }

        if duplicate_ids:
            # Consolidate
            duplicates = self.repo.get_articles_by_ids(duplicate_ids)
            duplicates.append(article)
            consolidated = self.dedup.consolidate(duplicates)
            
            stats.update({
                "is_duplicate": True,
                "duplicates_found": len(duplicate_ids)
            })
            
            return {
                "current_article": consolidated,
                "duplicates": duplicate_ids,
                "stats": stats
            }
        
        return {
            "duplicates": [],
            "stats": stats
        }
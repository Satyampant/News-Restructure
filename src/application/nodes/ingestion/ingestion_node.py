from datetime import datetime
from src.application.workflows.state import NewsIntelligenceState
from src.infrastructure.storage.vector.embeddings import EmbeddingService

class IngestionNode:
    """Validates article and generates embedding."""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
    
    def process(self, state: NewsIntelligenceState) -> dict:
        """Execute ingestion logic."""
        article = state.get("current_article")
        
        if not article:
            return {"error": "No article provided"}
        
        # Validate required fields
        if not all([article.id, article.title, article.content, article.source]):
            return {"error": "Missing required fields"}
        
        # Ensure timestamp is datetime
        if isinstance(article.timestamp, str):
            article.timestamp = datetime.fromisoformat(article.timestamp)
        
        # Generate embedding
        text = f"{article.title}. {article.content}"
        embedding = self.embedding_service.create_embedding(text)
        
        return {
            "current_article": article,
            "article_embedding": embedding,
            "stats": {
                "ingestion_time": datetime.now().isoformat(),
                "article_id": article.id,
                "embedding_computed": True
            }
        }
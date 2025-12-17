from typing import List, Optional, Any
from src.configuration.loader import get_config
from src.domain.models.article import NewsArticle
from src.domain.services.deduplication_logic import DeduplicationService
from src.infrastructure.storage.vector.chroma_client import ChromaDBClient
from src.infrastructure.storage.mongodb.article_repository import ArticleRepository

class DeduplicationAgent:
    """
    Orchestrates the deduplication process:
    1. Retrieval (Vector Store)
    2. Hydration (MongoDB)
    3. Verification (Domain Service)
    """

    def __init__(
        self,
        service: Optional[DeduplicationService] = None,
        candidate_pool_size: int = 10
    ):
        config = get_config()
        
        self.service = service or DeduplicationService(
            model_name=config.deduplication.cross_encoder_model,
            threshold=config.deduplication.cross_encoder_threshold
        )
        self.min_similarity = config.deduplication.bi_encoder_threshold
        self.candidate_pool_size = candidate_pool_size
        
        print(f"✓ DeduplicationAgent initialized (MongoDB Hydration)")

    def find_duplicates(
        self,
        article: NewsArticle,
        article_embedding: List[float],
        vector_store: ChromaDBClient,
        article_repo: ArticleRepository
    ) -> List[str]:
        """
        Retrieves candidates via vector search, hydrates from MongoDB, 
        then verifies duplicates using cross-encoder.
        """
        # Step 1: Retrieve candidate IDs from ChromaDB (vector search only)
        # Note: Adapting to ChromaDBClient.search interface
        candidates = vector_store.search(
            query_embedding=article_embedding,
            top_k=self.candidate_pool_size
        )
        
        if not candidates:
            return []
        
        # Step 2: Extract candidate IDs and filter by similarity threshold
        candidate_ids = []
        for c in candidates:
            # Handle potential dictionary structure from search result
            # Assuming keys 'article_id'/'id' and 'similarity'/'score'
            c_id = c.get("article_id") or c.get("id")
            score = c.get("similarity") or c.get("score", 0.0)
            
            if c_id and c_id != article.id and score >= self.min_similarity:
                candidate_ids.append(c_id)
        
        if not candidate_ids:
            return []
        
        # Step 3: Hydrate candidates from MongoDB (fetch full text)
        # Assuming Repo has get_articles_by_ids as implied by migration plan Phase 5
        candidate_articles = article_repo.get_articles_by_ids(candidate_ids)
        
        if not candidate_articles:
            return []
        
        # Step 4: Run Cross-Encoder verification via Domain Service
        duplicate_ids = self.service.identify_duplicates(article, candidate_articles)
        
        return duplicate_ids

    def consolidate(self, articles: List[NewsArticle]) -> NewsArticle:
        """
        Merges duplicates using domain service logic.
        """
        return self.service.consolidate_duplicates(articles)
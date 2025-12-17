"""
Query Processor Agent with Broad Filter Optimization.
Refactored from app/agents/query_processor.py.
"""

from typing import List, Dict, Any, Optional, Tuple

from src.domain.models.article import NewsArticle
from src.domain.models.query import QueryRouting
from src.domain.models.entities import QueryIntent
from src.infrastructure.storage.mongodb.article_repository import ArticleRepository
from src.infrastructure.storage.vector.chroma_client import ChromaDBClient
from src.application.agents.query_router_agent import QueryRouterAgent
from src.configuration.loader import get_config


class QueryProcessorAgent:
    """
    Two-step query processing with adaptive strategy selection:
    
    STRATEGY A (Small result set <= max_filter_ids):
    MongoDB Filter -> Vector Search
    - Filter articles in MongoDB first
    - Then perform vector search on filtered IDs
    
    STRATEGY B (Large result set > max_filter_ids):
    Vector Search -> MongoDB Validation (Inverted)
    - Perform unrestricted vector search first
    - Then validate results against MongoDB filters
    """
    
    def __init__(
        self,
        article_repo: ArticleRepository,
        vector_store: ChromaDBClient,
        query_router: QueryRouterAgent,
        config: Optional[Any] = None
    ):
        self.article_repo = article_repo
        self.vector_store = vector_store
        self.query_router = query_router
        self.config = config or get_config()
        
        # Threshold for strategy selection
        self.max_filter_ids = self.config.mongodb.max_filter_ids
        
        print(f"✓ QueryProcessorAgent initialized")
    
    def process_query(
        self,
        query: str,
        top_k: int = 10,
        sentiment_filter: Optional[str] = None
    ) -> Tuple[List[NewsArticle], QueryRouting]:
        """Implements adaptive strategy selection based on filter result size."""
        
        # Step 1: Route query using LLM
        routing = self.query_router.route_query(query)
        
        # Step 2: Override sentiment filter if provided
        if sentiment_filter:
            routing.sentiment_filter = sentiment_filter
        
        # Step 3: Generate MongoDB filter
        mongodb_filter = self.query_router.generate_mongodb_filter(routing)
        
        # This ensures the filter is applied regardless of the strategy chosen by the LLM
        if sentiment_filter:
            mongodb_filter["sentiment.classification"] = sentiment_filter

        # Access collection directly for metadata-only operations
        collection = self.article_repo.collection

        # Step 4: Count potential matches
        filtered_count = collection.count_documents(mongodb_filter)
        
        if filtered_count == 0 and sentiment_filter:
            # Fallback: relax other filters, keep sentiment
            mongodb_filter = {"sentiment.classification": sentiment_filter}
            filtered_count = collection.count_documents(mongodb_filter)

        # Broad Filter Optimization
        if filtered_count == 0:
            # FALLBACK: Perform unrestricted vector search
            strategy_used = "vector_search_fallback"
            
            # Generate query embedding
            query_embedding = self.vector_store.embedding_service.create_embedding(routing.refined_query)
            
            # Perform unrestricted vector search (no MongoDB filtering)
            vector_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 2
            )
            
            # If sentiment filter provided, apply post-filtering
            if sentiment_filter:
                candidate_ids = [r["article_id"] for r in vector_results]
                
                # Verify candidates against MongoDB to check sentiment
                valid_docs = collection.find(
                    {
                        "id": {"$in": candidate_ids},
                        "sentiment.classification": sentiment_filter
                    },
                    {"id": 1}
                )
                valid_ids = {doc["id"] for doc in valid_docs}
                
                vector_results = [
                    r for r in vector_results 
                    if r["article_id"] in valid_ids
                ][:top_k * 2]
            
            routing.strategy_metadata = {
                "strategy_used": strategy_used,
                "filtered_count": 0,
                "fallback_triggered": True,
                "mongodb_filter_applied": False,
                "vector_candidates": len(vector_results)
            }
        
        elif filtered_count <= self.max_filter_ids:
            # STRATEGY A: MongoDB Filter -> Vector Search
            strategy_used = "mongo_filter_first"
            
            # Get filtered article IDs from MongoDB (Projection only)
            cursor = collection.find(mongodb_filter, {"id": 1})
            filtered_ids = [doc["id"] for doc in cursor]
            
            # Generate query embedding
            query_embedding = self.vector_store.embedding_service.create_embedding(routing.refined_query)
            
            # Perform vector search on filtered IDs only using specialized method
            vector_results = self.vector_store.search_by_ids(
                query_embedding=query_embedding,
                article_ids=filtered_ids,
                top_k=top_k * 2  # Get extra for reranking
            )
        
        else:
            # STRATEGY B: Vector Search -> MongoDB Validation (Inverted)
            strategy_used = "vector_search_first"
            
            # Generate query embedding
            query_embedding = self.vector_store.embedding_service.create_embedding(routing.refined_query)
            
            # Perform unrestricted vector search
            vector_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 5  # Get more candidates for filtering
            )
            
            # Filter results by validating against MongoDB
            candidate_ids = [r["article_id"] for r in vector_results]
            
            # Add ID filter to existing MongoDB filter
            validation_filter = mongodb_filter.copy()
            validation_filter["id"] = {"$in": candidate_ids}
            
            # Get valid IDs from MongoDB
            cursor = collection.find(validation_filter, {"id": 1})
            valid_ids = {doc["id"] for doc in cursor}
            
            # Keep only valid results
            vector_results = [
                r for r in vector_results 
                if r["article_id"] in valid_ids
            ][:top_k * 2]  # Limit to reasonable size for reranking
        
        # Step 6: Fetch full articles from MongoDB
        article_ids = [r["article_id"] for r in vector_results]
        full_articles = self.article_repo.get_articles_by_ids(article_ids)
        
        # Step 7: Attach relevance scores to articles
        self._attach_scores(full_articles, vector_results)
        
        # Step 8: Rerank articles
        reranked_articles = self._rerank_articles(full_articles, routing)
        
        # Step 9: Return top_k articles + routing metadata
        final_articles = reranked_articles[:top_k]
        
        # Attach strategy metadata to routing for debugging
        routing.strategy_metadata = {
            "strategy_used": strategy_used,
            "filtered_count": filtered_count,
            "vector_candidates": len(vector_results),
            "mongodb_filter_applied": bool(mongodb_filter),
            "threshold": self.max_filter_ids
        }
        
        return final_articles, routing
    
    def _attach_scores(
        self,
        articles: List[NewsArticle],
        vector_results: List[Dict[str, Any]]
    ) -> None:
        """
        Attach relevance scores from vector search to articles.
        Modifies articles in-place.
        """
        # Create ID->similarity map
        score_map = {
            r["article_id"]: r["similarity"] 
            for r in vector_results
        }
        
        # Attach scores to articles
        for article in articles:
            # Dynamically attach score (runtime attribute)
            article.relevance_score = score_map.get(article.id, 0.0)
    
    def _rerank_articles(
        self,
        articles: List[NewsArticle],
        routing: QueryRouting
    ) -> List[NewsArticle]:
        """
        Rerank articles combining semantic similarity with strategy scoring.
        """
        for article in articles:
            # Get base semantic score
            semantic_score = getattr(article, 'relevance_score', 0.0)
            
            # Calculate strategy-specific score
            strategy_score = self._calculate_strategy_score(article, routing)
            
            # Weighted combination (50% semantic, 50% strategy)
            base_score = (semantic_score * 0.5) + (strategy_score * 0.5)
            
            # Apply sentiment boost if applicable
            if article.has_sentiment():
                sentiment_data = article.sentiment
                if sentiment_data:
                    signal_strength = sentiment_data.get("signal_strength", 0.0) if isinstance(sentiment_data, dict) else sentiment_data.signal_strength
                    base_score = self._apply_sentiment_boost(base_score, signal_strength)
            
            # Store final score
            article.final_score = min(base_score, 1.0)
            article.strategy_score = strategy_score
        
        # Sort by final score
        return sorted(articles, key=lambda x: getattr(x, 'final_score', 0.0), reverse=True)
    
    def _calculate_strategy_score(
        self,
        article: NewsArticle,
        routing: QueryRouting
    ) -> float:
        """
        Calculate strategy-specific relevance score based on metadata match.
        """
        strategy_score = 0.0
        
        # Normalize entity access (handle both dict and list structures from legacy/new mix)
        article_companies = []
        article_sectors = []
        article_regulators = []

        if hasattr(article, 'entities') and article.entities:
            entities = article.entities
            if isinstance(entities, dict):
                article_companies = entities.get("Companies", [])
                article_sectors = entities.get("Sectors", [])
                article_regulators = entities.get("Regulators", [])
            else:
                # Assuming EntityExtractionSchema or similar object structure
                # We check attributes if it's an object
                if hasattr(entities, 'companies'):
                    article_companies = [c.name for c in entities.companies]
                if hasattr(entities, 'sectors'):
                    article_sectors = entities.sectors
                if hasattr(entities, 'regulators'):
                    article_regulators = [r.name for r in entities.regulators]

        if routing.strategy == QueryIntent.DIRECT_ENTITY:
            # Check for entity matches
            company_match = any(
                entity.lower() in [str(c).lower() for c in article_companies]
                for entity in routing.entities
            )
            
            # Check for stock symbol matches
            article_stocks = []
            if hasattr(article, 'impacted_stocks') and article.impacted_stocks:
                for s in article.impacted_stocks:
                    if isinstance(s, dict):
                        article_stocks.append(s.get("symbol", "").upper())
                    elif hasattr(s, "symbol"):
                        article_stocks.append(s.symbol.upper())

            stock_match = any(
                symbol.upper() in article_stocks
                for symbol in routing.stock_symbols
            )
            
            strategy_score = 1.0 if (company_match or stock_match) else 0.0
        
        elif routing.strategy == QueryIntent.SECTOR_WIDE:
            # Check for sector matches
            sector_match = any(
                sector.lower() in [str(s).lower() for s in article_sectors]
                for sector in routing.sectors
            )
            strategy_score = 0.8 if sector_match else 0.0
        
        elif routing.strategy == QueryIntent.REGULATORY:
            # Check for regulator matches
            regulator_match = any(
                regulator.lower() in [str(r).lower() for r in article_regulators]
                for regulator in routing.regulators
            )
            strategy_score = 1.0 if regulator_match else 0.0
        
        elif routing.strategy == QueryIntent.SENTIMENT_DRIVEN:
            # Check sentiment match
            if article.has_sentiment() and article.sentiment:
                s_class = article.sentiment.get("classification") if isinstance(article.sentiment, dict) else article.sentiment.classification
                
                sentiment_match = (s_class == routing.sentiment_filter)
                strategy_score = 0.7 if sentiment_match else 0.0
                
                # Boost if sector also matches
                if sentiment_match and routing.sectors:
                    sector_match = any(
                        sector.lower() in [str(s).lower() for s in article_sectors]
                        for sector in routing.sectors
                    )
                    if sector_match:
                        strategy_score = 0.9
        
        elif routing.strategy == QueryIntent.CROSS_IMPACT:
            # Check for cross-impact data
            has_impacts = hasattr(article, 'cross_impacts') and bool(article.cross_impacts)
            strategy_score = 0.8 if has_impacts else 0.5
        
        else:
            # Default score for other strategies
            strategy_score = 0.3
        
        return strategy_score
    
    def _apply_sentiment_boost(
        self,
        score: float,
        sentiment_signal: float
    ) -> float:
        """
        Amplify score based on sentiment signal strength.
        Formula: 1.0 + (signal_strength / 200.0). Max boost ~1.5x.
        """
        sentiment_boost = 1.0 + (sentiment_signal / 200.0)
        return score * sentiment_boost
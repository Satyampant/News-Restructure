# Similarity algorithms
from typing import List, Set
from sentence_transformers import CrossEncoder
from src.domain.models.article import NewsArticle

class DeduplicationService:
    """
    Domain service containing similarity algorithms and consolidation logic.
    """
    
    def __init__(self, model_name: str, threshold: float):
        self.cross_encoder = CrossEncoder(model_name)
        self.threshold = threshold
    
    def _prepare_text(self, article: NewsArticle) -> str:
        """Prepare article text for comparison."""
        return f"{article.title}. {article.content}"
    
    def verify_similarity(self, article1_text: str, article2_text: str) -> float:
        """Calculates cross-encoder similarity score (0-1) between two texts."""
        score = self.cross_encoder.predict(
            [[article1_text, article2_text]],
            show_progress_bar=False,
            convert_to_numpy=True
        )[0]
        
        return float(score)

    def identify_duplicates(self, target: NewsArticle, candidates: List[NewsArticle]) -> List[str]:
        """
        Identify duplicates from a list of candidates using CrossEncoder.
        Returns list of confirmed duplicate IDs.
        """
        if not candidates:
            return []

        target_text = self._prepare_text(target)
        pairs = []
        candidate_id_map = {}

        for idx, candidate in enumerate(candidates):
            candidate_text = self._prepare_text(candidate)
            pairs.append([target_text, candidate_text])
            candidate_id_map[idx] = candidate.id

        if not pairs:
            return []

        # Run cross-encoder on hydrated candidate pairs
        cross_scores = self.cross_encoder.predict(
            pairs,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        # Filter by cross-encoder threshold
        duplicate_ids = [
            candidate_id_map[idx]
            for idx, score in enumerate(cross_scores)
            if score >= self.threshold
        ]

        return duplicate_ids

    def consolidate_duplicates(self, articles: List[NewsArticle]) -> NewsArticle:
        """
        Merges duplicates, keeping the earliest timestamp and aggregating unique sources.
        """
        if not articles:
            raise ValueError("Cannot consolidate empty article list")
        
        if len(articles) == 1:
            return articles[0]
        
        # Sort by timestamp (earliest first)
        sorted_articles = sorted(articles, key=lambda x: x.timestamp)
        primary = sorted_articles[0]
        
        # Aggregate unique sources
        seen_sources = set()
        unique_sources = []
        
        for article in sorted_articles:
            if not article.source:
                continue
            sources = [s.strip() for s in article.source.split(',')]
            for source in sources:
                if source not in seen_sources:
                    seen_sources.add(source)
                    unique_sources.append(source)
        
        primary.source = ", ".join(unique_sources)
        
        return primary
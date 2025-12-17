# Stock impact scoring
from typing import List
from src.domain.models.stock_impact import StockImpact

class ImpactScorer:
    """Domain service for stock impact scoring."""
    
    def rank_impacts(
        self,
        impacts: List[StockImpact],
        max_count: int
    ) -> List[StockImpact]:
        """Sort and limit stock impacts by confidence."""
        sorted_impacts = sorted(
            impacts,
            key=lambda s: s.confidence,
            reverse=True
        )
        return sorted_impacts[:max_count]
    
    def calculate_impact_weight(
        self,
        impact_type: str,
        confidence: float
    ) -> float:
        """Calculate weighted impact score."""
        weights = {
            "direct": 1.0,
            "sector": 0.7,
            "regulatory": 0.5
        }
        # Use lowercase for safer matching
        return weights.get(impact_type.lower(), 0.5) * confidence
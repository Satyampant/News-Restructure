# Sentiment calculation logic
from src.domain.models.sentiment import SentimentAnalysisSchema

class SentimentScorer:
    """Domain service for sentiment scoring logic."""
    
    def validate_scores(self, schema: SentimentAnalysisSchema) -> SentimentAnalysisSchema:
        """Validate and normalize sentiment scores."""
        # Ensure confidence and signal strength are within bounds
        schema.confidence_score = max(0.0, min(100.0, schema.confidence_score))
        schema.signal_strength = max(0.0, min(100.0, schema.signal_strength))
        return schema
    
    def calculate_signal_boost(self, signal_strength: float) -> float:
        """Calculate sentiment boost multiplier."""
        return 1.0 + (signal_strength / 200.0)
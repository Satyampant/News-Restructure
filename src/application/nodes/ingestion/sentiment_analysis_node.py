from src.application.workflows.state import NewsIntelligenceState
from src.application.agents.sentiment_agent import SentimentAnalysisAgent

class SentimentAnalysisNode:
    """Performs sentiment analysis."""
    
    def __init__(self, sentiment_agent: SentimentAnalysisAgent):
        self.agent = sentiment_agent
        
    def process(self, state: NewsIntelligenceState) -> dict:
        """Execute sentiment analysis."""
        article = state["current_article"]
        entities_schema = state.get("entities_schema")
        
        sentiment_schema = self.agent.analyze_sentiment(article, entities_schema)
        
        # Attach to article (Domain logic assumes article has methods to set sentiment)
        # We need to map schema to the article's internal sentiment structure
        # Assuming article.set_sentiment_from_schema or similar exists, or manually setting:
        # For now, relying on the pattern where we update the article object
        
        # Construct sentiment dict for legacy compatibility/storage
        sentiment_dict = {
            "classification": sentiment_schema.classification.value,
            "confidence_score": sentiment_schema.confidence_score,
            "signal_strength": sentiment_schema.signal_strength,
            "sentiment_breakdown": {
                "key_factors": sentiment_schema.key_factors,
                "sentiment_percentages": sentiment_schema.sentiment_breakdown,
                "entity_influence": sentiment_schema.entity_influence
            },
            "analysis_method": "llm"
        }
        
        # Update article
        article.sentiment = sentiment_dict
        
        stats = {
            "sentiment_analyzed": True,
            "sentiment_classification": sentiment_schema.classification.value,
            "sentiment_confidence": sentiment_schema.confidence_score,
            "sentiment_signal_strength": sentiment_schema.signal_strength,
            "sentiment_method": "llm",
            "sentiment_key_factors_count": len(sentiment_schema.key_factors)
        }
        
        return {
            "current_article": article,
            "sentiment_schema": sentiment_schema,
            "sentiment": sentiment_dict,
            "stats": stats
        }
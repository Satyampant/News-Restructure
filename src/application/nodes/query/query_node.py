from datetime import datetime
from typing import Dict, Any

from src.application.workflows.state import NewsIntelligenceState
from src.application.agents.query_processor_agent import QueryProcessorAgent
from src.configuration.loader import get_config


class QueryNode:
    """
    Node responsible for executing the query processing logic within the workflow.
    Validates inputs, executes the Two-Step Query Processor, and compiles statistics.
    """

    def __init__(self, query_processor: QueryProcessorAgent):
        self.query_processor = query_processor
        self.config = get_config()

    def process(self, state: NewsIntelligenceState) -> Dict[str, Any]:
        """
        Execute query processing pipeline step.
        """
        query_text = state.get("query_text")
        sentiment_filter = state.get("sentiment_filter")

        if not query_text:
            return {"error": "No query text provided"}

        if sentiment_filter:
            valid_sentiments = ["Bullish", "Bearish", "Neutral"]
            if sentiment_filter not in valid_sentiments:
                return {"error": f"Invalid sentiment filter: {sentiment_filter}. Must be {valid_sentiments}"}

        # Determine top_k from config or default
        top_k = 10
        try:
            if hasattr(self.config, 'query_processing'):
                top_k = self.config.query_processing.default_top_k
        except AttributeError:
            pass

        # Execute processing using the Agent
        results, routing = self.query_processor.process_query(
            query=query_text,
            top_k=top_k,
            sentiment_filter=sentiment_filter
        )

        # Extract strategy metadata attached by the processor
        strategy_metadata = getattr(routing, 'strategy_metadata', {})

        # Compile statistics
        stats = {
            "query_time": datetime.now().isoformat(),
            "results_count": len(results),
            "query": query_text,
            "sentiment_filter": sentiment_filter,
            "sentiment_filter_applied": sentiment_filter is not None,
            "query_routing": {
                "strategy": routing.strategy.value,
                "entities_identified": len(routing.entities),
                "sectors_identified": len(routing.sectors),
                "regulators_identified": len(routing.regulators),
                "refined_query": routing.refined_query,
                "routing_confidence": routing.confidence,
                "routing_reasoning": routing.reasoning
            },
            "execution_strategy": strategy_metadata.get("strategy_used", "unknown"),
            "mongodb_filter_applied": strategy_metadata.get("mongodb_filter_applied", False),
            "filtered_count": strategy_metadata.get("filtered_count", 0),
            "vector_candidates": strategy_metadata.get("vector_candidates", 0),
            "threshold": strategy_metadata.get("threshold", 0)
        }

        return {
            "query_results": results,
            "stats": stats
        }
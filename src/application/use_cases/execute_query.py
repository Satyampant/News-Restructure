from typing import Dict, Any, Optional
from src.application.workflows.query_graph import build_query_graph
from src.application.workflows.state import NewsIntelligenceState
from src.application.nodes.query.query_node import QueryNode
from src.application.agents.query_processor_agent import QueryProcessorAgent


class ExecuteQueryUseCase:
    """High-level use case for executing queries."""
    
    def __init__(self, query_processor: QueryProcessorAgent):
        """
        Initialize use case with query processor agent.
        
        Args:
            query_processor: The configured QueryProcessorAgent instance.
        """
        self.query_processor = query_processor
        
        # Build query node and graph
        query_node = QueryNode(query_processor=query_processor)
        self.graph = build_query_graph(query_node)
    
    def execute(
        self, 
        query: str, 
        top_k: int = 10, 
        sentiment_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a natural language query."""
        initial_state: NewsIntelligenceState = {
            "articles": [],
            "current_article": None,
            "article_embedding": None,
            "duplicates": [],
            "entities_schema": None,
            "sentiment_schema": None,
            "query_text": query,
            "sentiment_filter": sentiment_filter,
            "query_results": [],
            "error": None,
            "stats": {}
        }
        
        result = self.graph.invoke(initial_state)
        
        return {
            "articles": result.get("query_results", []),
            "stats": result.get("stats", {})
        }
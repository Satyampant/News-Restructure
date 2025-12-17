from typing import Dict, Any
from src.application.workflows.ingestion_graph import build_ingestion_graph
from src.application.workflows.state import NewsIntelligenceState
from src.domain.models.article import NewsArticle

class ProcessArticleUseCase:
    """High-level use case for processing articles."""
    
    def __init__(self, graph):
        """
        Inject compiled graph.
        
        Args:
            graph: The compiled LangGraph executable.
        """
        self.graph = graph
    
    def execute(self, article: NewsArticle) -> Dict[str, Any]:
        """
        Process a news article through the full pipeline.
        
        Args:
            article: The domain article model to process.
            
        Returns:
            Dict containing the final state of the workflow.
        """
        
        initial_state: NewsIntelligenceState = {
            "articles": [],
            "current_article": article,
            "article_embedding": None,
            "duplicates": [],
            "entities_schema": None,
            "sentiment_schema": None,
            "error": None,
            "stats": {}
        }
        
        result = self.graph.invoke(initial_state)
        return result
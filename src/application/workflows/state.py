# TypedDict state definitions
from typing import TypedDict, List, Annotated, Optional, Dict, Any
import operator

from src.domain.models.article import NewsArticle
from src.domain.models.entities import EntityExtractionSchema
from src.domain.models.sentiment import SentimentAnalysisSchema

def merge_dicts(a: Dict, b: Dict) -> Dict:
    return {**a, **b}

class NewsIntelligenceState(TypedDict):
    """
    State definition for the news processing pipeline.
    """
    
    articles: Annotated[List[NewsArticle], operator.add]
    current_article: Optional[NewsArticle]
    article_embedding: Optional[List[float]] 
    duplicates: Annotated[List[str], operator.add]
    entities_schema: Optional[EntityExtractionSchema]
    entities: Optional[dict]
    impacted_stocks: Optional[List[dict]]
    sentiment_schema: Optional[SentimentAnalysisSchema]
    cross_impacts: Optional[List[Dict]]
    sentiment: Optional[dict]
    query_text: Optional[str]
    sentiment_filter: Optional[str]
    query_results: Annotated[List[NewsArticle], operator.add]
    error: Optional[str]
    stats: Annotated[dict, merge_dicts]
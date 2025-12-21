from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class ArticleOutput(BaseModel):
    """Output model for article with enriched data"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    source: str
    timestamp: datetime
    entities: Optional[Dict[str, List[str]]] = None
    impacted_stocks: Optional[List[Dict[str, Any]]] = None
    relevance_score: Optional[float] = None
    sentiment: Optional[Dict[str, Any]] = None

class IngestResponse(BaseModel):
    """Response model for article ingestion"""
    success: bool
    article_id: str
    message: str
    is_duplicate: bool
    duplicates_found: int
    entities_extracted: Dict[str, int]
    stocks_impacted: int
    sentiment_classification: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    signal_strength: Optional[float] = None
    stats: Dict[str, Any]

class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    query: str
    results_count: int
    articles: List[ArticleOutput]
    stats: Dict[str, Any]

class StatsResponse(BaseModel):
    """Response model for system statistics"""
    total_articles_stored: int
    vector_store_count: int
    dedup_threshold: Dict[str, float]
    sentiment_analysis: Dict[str, Any]
    status: str

class SentimentDetailResponse(BaseModel):
    """Response model for detailed sentiment breakdown"""
    article_id: str
    title: str
    classification: str
    confidence_score: float
    signal_strength: float
    sentiment_breakdown: Dict[str, Any]
    analysis_method: str
    timestamp: str
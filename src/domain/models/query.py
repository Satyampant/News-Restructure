# Query routing models
from dataclasses import dataclass
from typing import List, Optional, Dict
from src.domain.models.entities import QueryIntent

@dataclass
class QueryRouting:
    """Query routing result."""
    entities: List[str]
    sectors: List[str]
    stock_symbols: List[str]
    sentiment_filter: Optional[str]
    refined_query: str
    strategy: QueryIntent
    confidence: float
    reasoning: str
    regulators: List[str] = None
    temporal_scope: Optional[str] = None
    strategy_metadata: Optional[Dict] = None
    
    def __post_init__(self):
        if self.regulators is None:
            self.regulators = []
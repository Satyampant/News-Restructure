# NewsArticle + domain methods
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.models.sentiment import SentimentData
    from src.domain.models.entities import EntityExtractionSchema

@dataclass
class NewsArticle:
    id: str
    title: str
    content: str
    source: str
    timestamp: datetime
    raw_text: str = field(default="")
    
    # Rich entity data (EntityExtractionSchema as dict)
    entities_rich: Optional[Dict[str, Any]] = None
    
    # Legacy entity storage (for backward compatibility)
    entities: Optional[Dict[str, List[str]]] = None
    
    impacted_stocks: List[Dict] = field(default_factory=list)
    sentiment: Optional[Dict[str, Any]] = None
    cross_impacts: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

    # MongoDB conversion methods moved to infrastructure layer (Phase 3)
    # TODO: Implement in src/infrastructure/storage/mongodb/article_repository.py
    # def to_mongo_document(self) -> dict: ...
    # @classmethod
    # def from_mongo_document(cls, doc: dict) -> 'NewsArticle': ...
    
    def set_entities_rich(self, entities_schema: 'EntityExtractionSchema') -> None:
        """
        Store rich entity data from LLM extraction.
        Also populates legacy 'entities' dict for backward compatibility.
        """
        # Store rich data
        if hasattr(entities_schema, 'model_dump'):
            self.entities_rich = entities_schema.model_dump()
        else:
            self.entities_rich = asdict(entities_schema)
        
        # Populate legacy format for backward compatibility
        self.entities = {
            "Companies": [c.get("name") if isinstance(c, dict) else c.name 
                         for c in self.entities_rich.get("companies", [])],
            "Sectors": self.entities_rich.get("sectors", []),
            "Regulators": [r.get("name") if isinstance(r, dict) else r.name 
                          for r in self.entities_rich.get("regulators", [])],
            "People": self.entities_rich.get("people", []),
            "Events": [e.get("event_type") if isinstance(e, dict) else e.event_type 
                      for e in self.entities_rich.get("events", [])]
        }
    
    def get_entities_rich(self) -> Optional[Dict[str, Any]]:
        """Get rich entity data with tickers and confidence scores."""
        return self.entities_rich
    
    def get_company_tickers(self) -> List[Dict[str, str]]:
        """
        Extract company ticker symbols from rich entity data.
        
        Returns:
            List of dicts: [{"name": "HDFC Bank", "ticker": "HDFCBANK", "sector": "Banking"}, ...]
        """
        if not self.entities_rich:
            return []
        
        companies = self.entities_rich.get("companies", [])
        return [
            {
                "name": c.get("name"),
                "ticker": c.get("ticker_symbol"),
                "sector": c.get("sector"),
                "confidence": c.get("confidence")
            }
            for c in companies
            if c.get("ticker_symbol")
        ]
    
    def set_sentiment(self, sentiment_data: 'SentimentData') -> None:
        self.sentiment = sentiment_data.to_dict()
    
    def get_sentiment(self) -> Optional['SentimentData']:
        from src.domain.models.sentiment import SentimentData
        if self.sentiment is None:
            return None
        return SentimentData.from_dict(self.sentiment)
    
    def has_sentiment(self) -> bool:
        return self.sentiment is not None

    def set_cross_impacts(self, impacts: List[Dict]) -> None:
        self.cross_impacts = impacts
    
    def has_cross_impacts(self) -> bool:
        return len(self.cross_impacts) > 0
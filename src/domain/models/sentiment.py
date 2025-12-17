# Sentiment models
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime

from enum import Enum
from pydantic import BaseModel, Field, field_validator

@dataclass
class SentimentData:
    classification: str  # "Bullish" | "Bearish" | "Neutral"
    confidence_score: float  # 0-100 scale
    signal_strength: float  # 0-100 scale
    sentiment_breakdown: Dict[str, Any]
    analysis_method: str = "llm"
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentimentData':
        return cls(**data)




class SentimentClassification(str, Enum):
    """Sentiment polarity categories."""
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"

class SentimentAnalysisSchema(BaseModel):
    """
    Sentiment analysis output schema.
    LLM determines market sentiment with detailed reasoning.
    """
    classification: SentimentClassification = Field(..., description="Overall sentiment: Bullish, Bearish, or Neutral")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence in sentiment classification (0-100 scale)")
    key_factors: List[str] = Field(..., min_length=1, description="Bullet points explaining the sentiment decision")
    signal_strength: float = Field(..., ge=0.0, le=100.0, description="Trading signal strength based on sentiment intensity (0-100)")
    sentiment_breakdown: Optional[dict] = Field(None, description="Detailed percentage breakdown: {bullish: %, bearish: %, neutral: %}")
    entity_influence: Optional[dict] = Field(None, description="How specific entities influenced the sentiment")
    
    @field_validator('key_factors')
    @classmethod
    def validate_key_factors(cls, v: List[str]) -> List[str]:
        if not v or len(v) < 1:
            raise ValueError("At least one key factor must be provided")
        return [f.strip() for f in v if f and len(f.strip()) > 5]
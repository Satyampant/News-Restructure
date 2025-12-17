# Stock impact models
"""
Stock impact mapping models.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from src.domain.models.entities import ImpactType

class StockImpact(BaseModel):
    """Represents the impact of news on a specific stock."""
    symbol: str = Field(..., description="Stock ticker symbol (e.g., HDFCBANK, RELIANCE)")
    company_name: str = Field(..., description="Full company name for clarity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in impact assessment")
    impact_type: ImpactType = Field(..., description="Type of impact: direct, sector-wide, or regulatory")
    reasoning: str = Field(..., description="Explanation for why this stock is impacted")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        if not v or len(v.strip()) < 1:
            raise ValueError("Stock symbol cannot be empty")
        return v.strip().upper()

class StockImpactSchema(BaseModel):
    """
    Complete stock impact mapping output schema.
    LLM maps news to affected stocks with confidence and reasoning.
    """
    impacted_stocks: List[StockImpact] = Field(default_factory=list, description="List of stocks impacted by the news")
    overall_market_impact: Optional[str] = Field(None, description="Broader market implications (if any)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in impact analysis")
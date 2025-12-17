# Entity extraction models
"""
Domain entities and extraction schemas.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# Enums
class ImpactType(str, Enum):
    """Stock impact classification types."""
    DIRECT = "direct"
    SECTOR = "sector"
    REGULATORY = "regulatory"

class QueryIntent(str, Enum):
    """Query routing strategy types."""
    DIRECT_ENTITY = "DIRECT_ENTITY"
    SECTOR_WIDE = "SECTOR_WIDE"
    REGULATORY = "REGULATORY"
    SENTIMENT_DRIVEN = "SENTIMENT_DRIVEN"
    CROSS_IMPACT = "CROSS_IMPACT"
    SEMANTIC_SEARCH = "SEMANTIC_SEARCH"
    TEMPORAL = "TEMPORAL"

# Entity models
class CompanyEntity(BaseModel):
    """Represents a company mentioned in financial news."""
    name: str = Field(..., description="Full company name as mentioned in text")
    ticker_symbol: Optional[str] = Field(None, description="Stock ticker symbol (e.g., HDFCBANK, TCS)")
    sector: Optional[str] = Field(None, description="Industry sector (e.g., Banking, IT, Pharma)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this extraction")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Company name must be at least 2 characters")
        return v.strip()

class RegulatorEntity(BaseModel):
    """Represents a regulatory body mentioned in the news."""
    name: str = Field(..., description="Regulator name (e.g., RBI, SEBI, US FDA)")
    jurisdiction: Optional[str] = Field(None, description="Geographic/domain jurisdiction (e.g., India, US, Banking)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this extraction")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Regulator name must be at least 2 characters")
        return v.strip()

class EventEntity(BaseModel):
    """Represents a market event mentioned in the news."""
    event_type: str = Field(..., description="Event category (e.g., dividend, merger, policy_change)")
    description: str = Field(..., description="Brief description of the event")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this extraction")
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Event type must be specified")
        return v.strip().lower().replace(" ", "_")

class EntityExtractionSchema(BaseModel):
    """
    Complete entity extraction output schema.
    LLM extracts all relevant financial entities from news text.
    """
    companies: List[CompanyEntity] = Field(default_factory=list, description="List of companies mentioned in the article")
    sectors: List[str] = Field(default_factory=list, description="Industry sectors mentioned or inferred (e.g., Banking, IT, Auto)")
    regulators: List[RegulatorEntity] = Field(default_factory=list, description="Regulatory bodies mentioned in the article")
    people: List[str] = Field(default_factory=list, description="Names of key individuals mentioned (CEOs, policymakers, etc.)")
    events: List[EventEntity] = Field(default_factory=list, description="Market events identified in the article")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in entity extraction quality")
    extraction_reasoning: Optional[str] = Field(None, description="Brief explanation of extraction logic")
    
    @field_validator('sectors')
    @classmethod
    def validate_sectors(cls, v: List[str]) -> List[str]:
        return [s.strip() for s in v if s and len(s.strip()) > 1]
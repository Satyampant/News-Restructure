# Supply chain models
"""
Supply chain and cross-sector impact models.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class RelationshipType(str, Enum):
    """Supply chain relationship categories."""
    UPSTREAM_DEMAND_SHOCK = "upstream_demand_shock"
    DOWNSTREAM_SUPPLY_IMPACT = "downstream_supply_impact"

class CrossImpact(BaseModel):
    """Represents cross-sectoral impact via supply chain relationships."""
    source_sector: str = Field(..., description="Sector where the news originated")
    target_sector: str = Field(..., description="Sector that will be impacted")
    relationship_type: RelationshipType = Field(..., description="Type of relationship: upstream demand shock or downstream supply impact")
    impact_score: float = Field(..., ge=0.0, le=100.0, description="Impact magnitude score (0-100)")
    dependency_weight: float = Field(..., ge=0.0, le=1.0, description="Strength of dependency between sectors (0-1)")
    reasoning: str = Field(..., description="Natural language explanation of the cross-sectoral impact")
    impacted_stocks: List[str] = Field(default_factory=list, description="Stock symbols in the target sector that will be affected")
    time_horizon: Optional[str] = Field(None, description="Expected timeframe for impact (e.g., immediate, short-term, long-term)")
    
    @field_validator('source_sector', 'target_sector')
    @classmethod
    def validate_sector(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Sector name must be at least 2 characters")
        return v.strip()

class SupplyChainImpactSchema(BaseModel):
    """
    Complete supply chain impact analysis schema.
    LLM identifies upstream and downstream effects of news.
    """
    upstream_impacts: List[CrossImpact] = Field(default_factory=list, description="Impacts on upstream suppliers/dependencies")
    downstream_impacts: List[CrossImpact] = Field(default_factory=list, description="Impacts on downstream customers/consumers")
    reasoning: str = Field(..., description="Overall reasoning for supply chain impact assessment")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in supply chain analysis")
    total_sectors_impacted: int = Field(..., ge=0, description="Total number of sectors identified as impacted")
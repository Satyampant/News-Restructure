from typing import List, Set
from src.domain.models.supply_chain import SupplyChainImpactSchema, CrossImpact

class SupplyChainService:
    """Domain service for supply chain impact logic."""

    def process_impacts(
        self, 
        schema: SupplyChainImpactSchema, 
        min_impact_score: float = 0.0
    ) -> SupplyChainImpactSchema:
        """Filter, sort, and validate supply chain impacts."""
        
        # Filter and sort upstream
        schema.upstream_impacts = self._filter_and_sort(
            schema.upstream_impacts, 
            min_impact_score
        )
        
        # Filter and sort downstream
        schema.downstream_impacts = self._filter_and_sort(
            schema.downstream_impacts, 
            min_impact_score
        )
        
        # Recalculate total sectors
        impacted_sectors: Set[str] = set()
        for impact in schema.upstream_impacts:
            impacted_sectors.add(impact.target_sector)
        for impact in schema.downstream_impacts:
            impacted_sectors.add(impact.target_sector)
            
        schema.total_sectors_impacted = len(impacted_sectors)
        
        return schema

    def _filter_and_sort(
        self, 
        impacts: List[CrossImpact], 
        min_score: float
    ) -> List[CrossImpact]:
        """Filter by score and sort descending."""
        filtered = [i for i in impacts if i.impact_score >= min_score]
        return sorted(filtered, key=lambda x: x.impact_score, reverse=True)
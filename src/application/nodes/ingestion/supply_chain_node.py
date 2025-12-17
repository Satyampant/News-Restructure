from src.application.workflows.state import NewsIntelligenceState
from src.application.agents.supply_chain_agent import SupplyChainAgent

class SupplyChainNode:
    """Analyzes supply chain relationships."""
    
    def __init__(self, supply_chain_agent: SupplyChainAgent):
        self.agent = supply_chain_agent
        
    def process(self, state: NewsIntelligenceState) -> dict:
        """Execute supply chain analysis."""
        article = state["current_article"]
        entities_schema = state.get("entities_schema")
        sentiment_schema = state.get("sentiment_schema")
        
        # Pre-checks similar to legacy logic
        if not entities_schema or not sentiment_schema or not entities_schema.sectors:
            stats = {
                "cross_impacts_found": 0,
                "upstream_dependencies": 0,
                "downstream_impacts": 0,
                "supply_chain_method": "llm",
                "supply_chain_skipped": "Missing entities, sectors, or sentiment data"
            }
            return {
                "cross_impacts": [],
                "stats": stats
            }
            
        supply_chain_result = self.agent.analyze_supply_chain(
            article, entities_schema, sentiment_schema
        )
        
        all_impacts = (
            supply_chain_result.upstream_impacts +
            supply_chain_result.downstream_impacts
        )
        
        cross_impact_dicts = [
            {
                "source_sector": impact.source_sector,
                "target_sector": impact.target_sector,
                "relationship_type": impact.relationship_type.value,
                "impact_score": impact.impact_score,
                "dependency_weight": impact.dependency_weight,
                "reasoning": impact.reasoning,
                "impacted_stocks": impact.impacted_stocks,
                "time_horizon": impact.time_horizon
            }
            for impact in all_impacts
        ]
        
        article.set_cross_impacts(cross_impact_dicts)
        
        stats = {
            "cross_impacts_found": len(all_impacts),
            "upstream_dependencies": len(supply_chain_result.upstream_impacts),
            "downstream_impacts": len(supply_chain_result.downstream_impacts),
            "supply_chain_method": "llm",
            "total_sectors_impacted": supply_chain_result.total_sectors_impacted
        }
        
        if all_impacts:
            top_impact = all_impacts[0]
            stats["top_cross_impact"] = {
                "target_sector": top_impact.target_sector,
                "impact_score": top_impact.impact_score,
                "relationship_type": top_impact.relationship_type.value
            }
            
        return {
            "current_article": article,
            "cross_impacts": cross_impact_dicts,
            "stats": stats
        }
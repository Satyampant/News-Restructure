from src.application.workflows.state import NewsIntelligenceState
from src.application.agents.stock_impact_agent import StockImpactAgent

class ImpactMappingNode:
    """Maps extracted entities to specific stock tickers."""
    
    def __init__(self, impact_agent: StockImpactAgent):
        self.agent = impact_agent
        
    def process(self, state: NewsIntelligenceState) -> dict:
        """Execute stock impact mapping."""
        article = state["current_article"]
        entities_schema = state["entities_schema"]
        
        if not entities_schema:
            # Fallback handling should be done via state checks or error handling
            return {"stats": {"stock_impact_skipped": "No entities schema"}}
            
        impact_result = self.agent.map_to_stocks(entities_schema, article)
        
        # Convert to dictionary format for article storage
        impact_dicts = [
            {
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "confidence": stock.confidence,
                "impact_type": stock.impact_type.value,
                "reasoning": stock.reasoning
            }
            for stock in impact_result.impacted_stocks
        ]
        
        article.impacted_stocks = impact_dicts
        
        stats = {
            "stocks_impacted": len(impact_result.impacted_stocks),
            "stock_impact_method": "llm",
            "overall_market_impact": impact_result.overall_market_impact,
            "impact_breakdown": {
                "direct": sum(1 for s in impact_result.impacted_stocks if s.impact_type.value == "direct"),
                "sector": sum(1 for s in impact_result.impacted_stocks if s.impact_type.value == "sector"),
                "regulatory": sum(1 for s in impact_result.impacted_stocks if s.impact_type.value == "regulatory")
            }
        }
        
        return {
            "current_article": article,
            "impacted_stocks": impact_dicts,
            "stats": stats
        }
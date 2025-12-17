from src.application.workflows.state import NewsIntelligenceState
from src.application.agents.entity_agent import EntityExtractionAgent

class EntityExtractionNode:
    """Extracts entities using LLM with structured output."""
    
    def __init__(self, entity_agent: EntityExtractionAgent):
        self.agent = entity_agent

    def process(self, state: NewsIntelligenceState) -> dict:
        """Execute entity extraction."""
        article = state["current_article"]
        
        # Extract entities using agent (handles caching internally)
        entities_schema = self.agent.extract_entities(article)
        
        # Domain logic: Update article with rich entities
        article.set_entities_rich(entities_schema)
        
        # Prepare statistics
        stats = {
            "entities_extracted": {
                "companies": len(entities_schema.companies),
                "sectors": len(entities_schema.sectors),
                "regulators": len(entities_schema.regulators),
                "people": len(entities_schema.people),
                "events": len(entities_schema.events)
            },
            "entity_extraction_method": "llm",
            "extraction_reasoning": entities_schema.extraction_reasoning
        }
        
        tickers_extracted = [c.ticker_symbol for c in entities_schema.companies if c.ticker_symbol]
        stats["tickers_extracted"] = len(tickers_extracted)
        
        company_confidences = [c.confidence for c in entities_schema.companies]
        if company_confidences:
            stats["avg_company_confidence"] = round(
                sum(company_confidences) / len(company_confidences), 2
            )
            
        return {
            "current_article": article,
            "entities_schema": entities_schema,
            # Legacy field support if needed
            "entities": article.entities, 
            "stats": stats
        }
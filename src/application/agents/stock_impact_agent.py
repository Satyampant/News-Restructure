from typing import Optional
from src.infrastructure.llm.groq_client import GroqLLMClient
from src.domain.models.article import NewsArticle
from src.domain.models.entities import EntityExtractionSchema
from src.domain.models.stock_impact import StockImpactSchema
from src.domain.services.impact_scoring import ImpactScorer
from src.configuration.loader import get_config

class StockImpactAgent:
    """Maps news to affected stocks using LLM."""
    
    def __init__(
        self,
        llm_client: GroqLLMClient,
        scorer: Optional[ImpactScorer] = None,
        max_stocks: int = 15
    ):
        self.llm = llm_client
        self.scorer = scorer or ImpactScorer()
        self.max_stocks = max_stocks
        self.config = get_config()
    
    def map_to_stocks(
        self,
        entities: EntityExtractionSchema,
        article: NewsArticle
    ) -> StockImpactSchema:
        """Map entities to stock symbols with impact assessment."""
        
        # Build prompt
        prompt = self._build_prompt(entities, article)
        
        # Get system message
        system_message = self.config.prompts.stock_impact.system_message
        
        # Call LLM
        result_data = self.llm.generate_structured_output(
            prompt=prompt,
            schema=StockImpactSchema,
            system_message=system_message
        )
        
        # Ensure we have the schema object
        if isinstance(result_data, dict):
            result = StockImpactSchema.model_validate(result_data)
        else:
            result = result_data
        
        # Sort and limit using domain logic
        result.impacted_stocks = self.scorer.rank_impacts(
            result.impacted_stocks,
            max_count=self.max_stocks
        )
        
        return result

    def _build_prompt(
        self,
        entities: EntityExtractionSchema,
        article: NewsArticle
    ) -> str:
        """Build the impact analysis prompt using extracted entities."""
        
        # Format Companies
        if entities.companies:
            companies_str = "\n".join([
                f"  - {c.name}" + (f" (Ticker: {c.ticker_symbol})" if c.ticker_symbol else "") +
                (f" [Sector: {c.sector}]" if c.sector else "") +
                f" [Confidence: {c.confidence:.2f}]"
                for c in entities.companies
            ])
        else:
            companies_str = "  None explicitly mentioned"
        
        # Format Sectors
        sectors_str = ", ".join(entities.sectors) if entities.sectors else "None"
        
        # Format Regulators
        if entities.regulators:
            regulators_str = "\n".join([
                f"  - {r.name}" + (f" ({r.jurisdiction})" if r.jurisdiction else "") +
                f" [Confidence: {r.confidence:.2f}]"
                for r in entities.regulators
            ])
        else:
            regulators_str = "  None mentioned"
        
        # Format Events
        if entities.events:
            events_str = "\n".join([
                f"  - {e.event_type}: {e.description} [Confidence: {e.confidence:.2f}]"
                for e in entities.events
            ])
        else:
            events_str = "  None identified"
            
        # Get template from config
        prompt_template = self.config.prompts.stock_impact.task_prompt
        
        return prompt_template.format(
            title=article.title,
            content=article.content,
            companies=companies_str,
            sectors=sectors_str,
            regulators=regulators_str,
            events=events_str,
            max_stocks=self.max_stocks
        )
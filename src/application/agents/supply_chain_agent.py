from typing import Optional
from src.infrastructure.llm.groq_client import GroqLLMClient
from src.domain.models.article import NewsArticle
from src.domain.models.entities import EntityExtractionSchema
from src.domain.models.sentiment import SentimentAnalysisSchema
from src.domain.models.supply_chain import SupplyChainImpactSchema
from src.domain.services.supply_chain_service import SupplyChainService
from src.configuration.loader import get_config

class SupplyChainAgent:
    """Coordinates supply chain impact analysis using LLM."""

    def __init__(
        self,
        llm_client: GroqLLMClient,
        service: Optional[SupplyChainService] = None,
        min_impact_score: Optional[float] = None
    ):
        self.llm = llm_client
        self.service = service or SupplyChainService()
        self.config = get_config()
        self.min_impact_score = min_impact_score or self.config.supply_chain.min_impact_score

    def analyze_supply_chain(
        self,
        article: NewsArticle,
        entities: EntityExtractionSchema,
        sentiment: SentimentAnalysisSchema
    ) -> SupplyChainImpactSchema:
        """Analyze cross-sector supply chain impacts."""
        
        # Build prompt
        prompt = self._build_prompt(article, entities, sentiment)
        system_message = self._build_system_message()

        # Call LLM
        result = self.llm.generate_structured_output(
            prompt=prompt,
            schema=SupplyChainImpactSchema,
            system_message=system_message
        )

        # Process results using domain service (filter/sort)
        validated = self.service.process_impacts(
            result, 
            min_impact_score=self.min_impact_score
        )

        return validated

    def _build_system_message(self) -> str:
        """Build system message with examples."""
        template = self.config.prompts.supply_chain.system_message
        examples = self.config.prompts.supply_chain.few_shot_examples
        return template.format(
            few_shot_examples=examples,
            min_impact_score=self.min_impact_score
        )

    def _build_prompt(
        self,
        article: NewsArticle,
        entities: EntityExtractionSchema,
        sentiment: SentimentAnalysisSchema
    ) -> str:
        """Build analysis prompt."""
        template = self.config.prompts.supply_chain.task_prompt
        
        entity_context = self._format_entity_context(entities)
        sentiment_context = self._format_sentiment_context(sentiment)

        return template.format(
            title=article.title,
            content=article.content,
            entity_context=entity_context,
            sentiment_context=sentiment_context,
            signal_strength=sentiment.signal_strength,
            min_impact_score=self.min_impact_score
        )

    def _format_entity_context(self, entities: EntityExtractionSchema) -> str:
        """Format extracted entities for prompt."""
        parts = []
        if entities.companies:
            names = ", ".join([c.name for c in entities.companies])
            parts.append(f"Companies: [{names}]")
        if entities.sectors:
            sectors = ", ".join(entities.sectors)
            parts.append(f"Sectors: [{sectors}]")
        if entities.regulators:
            names = ", ".join([r.name for r in entities.regulators])
            parts.append(f"Regulators: [{names}]")
        if entities.events:
            types = ", ".join([e.event_type for e in entities.events])
            parts.append(f"Events: [{types}]")
            
        return "\n".join(parts) if parts else "No key entities identified"

    def _format_sentiment_context(self, sentiment: SentimentAnalysisSchema) -> str:
        """Format sentiment metrics for prompt."""
        factors = "\n".join([f"  - {f}" for f in sentiment.key_factors[:3]])
        # Handle enum value if necessary, though str(Enum) often works
        classification = sentiment.classification.value if hasattr(sentiment.classification, 'value') else sentiment.classification
        
        return (
            f"Sentiment Classification: {classification}\n"
            f"Signal Strength: {sentiment.signal_strength}/100\n"
            f"Confidence: {sentiment.confidence_score}/100\n"
            f"Key Factors:\n{factors}"
        )
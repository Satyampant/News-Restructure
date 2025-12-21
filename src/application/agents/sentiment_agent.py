from typing import Optional

from src.infrastructure.llm.groq_client import GroqLLMClient
from src.domain.models.article import NewsArticle
from src.domain.models.entities import EntityExtractionSchema
from src.domain.models.sentiment import SentimentAnalysisSchema
from src.domain.services.sentiment_scoring import SentimentScorer
from src.configuration.loader import get_config
from src.infrastructure.llm.prompt_builder import build_sentiment_prompt

class SentimentAnalysisAgent:
    """Coordinates sentiment analysis using LLM."""
    
    def __init__(
        self,
        llm_client: GroqLLMClient,
        scorer: Optional[SentimentScorer] = None,
        use_entity_context: bool = True
    ):
        self.llm = llm_client
        self.scorer = scorer or SentimentScorer()
        self.use_entity_context = use_entity_context
        self.config = get_config()
    
    def analyze_sentiment(
        self,
        article: NewsArticle,
        entities: Optional[EntityExtractionSchema] = None
    ) -> SentimentAnalysisSchema:
        """Analyze sentiment with entity context."""
        
        # Build prompt using infrastructure utility and config
        prompt_config = self.config.prompts.sentiment_analysis
        
        prompt = self._build_prompt(article, entities)
        
        # Prepare system message with few-shot examples
        system_message = prompt_config.system_message.format(
            few_shot_examples=prompt_config.few_shot_examples
        )
        
        # Call LLM
        result = self.llm.generate_structured_output(
            prompt=prompt,
            schema=SentimentAnalysisSchema,
            system_message=system_message
        )
        
        if isinstance(result, dict):
            result = SentimentAnalysisSchema.model_validate(result)

        # Validate scores using domain service
        validated = self.scorer.validate_scores(result)
        
        return validated

    def _build_prompt(
        self, 
        article: NewsArticle, 
        entities: Optional[EntityExtractionSchema]
    ) -> str:
        """Internal helper to build prompt via infrastructure builder."""
        prompt_config = self.config.prompts.sentiment_analysis
        
        return build_sentiment_prompt(
            article=article,
            entities=entities if self.use_entity_context else None,
            template=prompt_config.task_prompt,
            few_shot=prompt_config.few_shot_examples
        )
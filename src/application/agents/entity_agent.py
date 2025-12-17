# Calls LLM + domain logic
from typing import Optional
from src.infrastructure.llm.groq_client import GroqLLMClient
from src.infrastructure.storage.cache.redis_cache import RedisCacheService
from src.infrastructure.llm.prompt_builder import build_entity_extraction_prompt
from src.domain.models.article import NewsArticle
from src.domain.models.entities import EntityExtractionSchema
from src.domain.services.entity_normalization import EntityNormalizer
from src.configuration.loader import get_config

class EntityExtractionAgent:
    """
    Application service that coordinates entity extraction.
    Orchestrates: Cache Check -> LLM Extraction -> Domain Normalization -> Cache Update.
    """
    
    def __init__(
        self,
        llm_client: GroqLLMClient,
        cache_service: Optional[RedisCacheService] = None,
        normalizer: Optional[EntityNormalizer] = None
    ):
        self.llm = llm_client
        self.cache = cache_service
        self.normalizer = normalizer or EntityNormalizer()
        self.config = get_config()
    
    def extract_entities(
        self,
        article: NewsArticle,
        use_cache: bool = True
    ) -> EntityExtractionSchema:
        """
        Extract entities from an article using LLM with caching and normalization.
        """
        
        # 1. Check Cache
        if use_cache and self.cache and self.cache.is_connected:
            cached = self.cache.get(article.id)
            if cached:
                try:
                    return EntityExtractionSchema.model_validate(cached)
                except Exception as e:
                    # Log warning but continue to fresh extraction
                    print(f"⚠ Cache deserialization warning for {article.id}: {e}")
        
        # 2. Build Prompt
        prompt = self._build_prompt(article)
        system_message = self.config.prompts.entity_extraction.system_message
        
        # 3. Call LLM
        # Using the structured output capability of the LLM provider
        result_dict = self.llm.generate_structured_output(
            prompt=prompt,
            schema=EntityExtractionSchema,
            system_message=system_message
        )
        
        # Convert dictionary to Pydantic model
        raw_schema = EntityExtractionSchema.model_validate(result_dict)
        
        # 4. Normalize using Domain Service
        validated_schema = self.normalizer.normalize(raw_schema)
        
        # 5. Update Cache
        if self.cache and self.cache.is_connected:
            self.cache.set(article.id, validated_schema.model_dump())
        
        return validated_schema
    
    def _build_prompt(self, article: NewsArticle) -> str:
        """Internal helper to construct the prompt using infrastructure builder."""
        template = self.config.prompts.entity_extraction.task_prompt
        return build_entity_extraction_prompt(article, template)
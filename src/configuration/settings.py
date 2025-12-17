# Pydantic Settings from config.yaml
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import os

class EntityExtractionPrompts(BaseModel):
    system_message: str = ""
    task_prompt: str = ""
    entity_context_format: str = ""

class SentimentAnalysisPrompts(BaseModel):
    system_message: str = ""
    task_prompt: str = ""
    few_shot_examples: str = ""

class StockMappingPrompts(BaseModel):
    system_message: str = ""
    task_prompt: str = ""

class SupplyChainPrompts(BaseModel):
    system_message: str = ""
    few_shot_examples: str = ""
    task_prompt: str = ""

class QueryRoutingPrompts(BaseModel):
    system_message: str = ""
    few_shot_examples: str = ""
    task_prompt: str = ""

class PromptConfig(BaseModel):
    """Prompt templates configuration."""
    entity_extraction: EntityExtractionPrompts = Field(default_factory=EntityExtractionPrompts)
    sentiment_analysis: SentimentAnalysisPrompts = Field(default_factory=SentimentAnalysisPrompts)
    stock_impact: StockMappingPrompts = Field(default_factory=StockMappingPrompts)
    supply_chain: SupplyChainPrompts = Field(default_factory=SupplyChainPrompts)
    query_routing: QueryRoutingPrompts = Field(default_factory=QueryRoutingPrompts)

class MongoDBConfig(BaseModel):
    """MongoDB configuration for article storage."""
    connection_string: Optional[str] = None # Handled dynamically in loader
    database_name: str = "marketmuni"
    collection_name: str = "articles"
    max_pool_size: int = 100
    timeout_ms: int = 5000
    max_filter_ids: int = 1000

class RedisConfig(BaseModel):
    """Redis cache configuration."""
    enabled: bool = True
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ttl_seconds: int = 86400
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

class DeduplicationConfig(BaseModel):
    bi_encoder_threshold: float = 0.50
    cross_encoder_threshold: float = 0.70
    cross_encoder_model: str = "cross-encoder/stsb-distilroberta-base"

class EntityExtractionConfig(BaseModel):
    spacy_model: str = "en_core_web_sm"
    use_spacy: bool = True
    event_keywords: List[str] = Field(default_factory=list)

class VectorStoreConfig(BaseModel):
    collection_name: str = "financial_news"
    persist_directory: str = "data/chroma_db"
    embedding_model: str = "all-mpnet-base-v2"
    distance_metric: str = "cosine"

class LLMRoutingConfig(BaseModel):
    """LLM-based query routing configuration."""
    enabled: bool = True
    confidence_threshold: float = 0.6
    fallback_strategy: str = "semantic_search"
    max_entities_per_query: int = 10
    enable_query_expansion: bool = True

class MultiQueryConfig(BaseModel):
    max_context_queries: int = 3
    initial_retrieval_multiplier: int = 2

class RerankingWeights(BaseModel):
    strategy_weight: float = 0.5
    semantic_weight: float = 0.5

class SentimentBoostConfig(BaseModel):
    enabled: bool = True
    max_multiplier: float = 1.5

class QueryProcessingConfig(BaseModel):
    default_top_k: int = 10
    min_similarity: float = 0.3
    llm_routing: LLMRoutingConfig = Field(default_factory=LLMRoutingConfig)
    strategy_weights: Dict[str, float] = Field(default_factory=dict)
    multi_query: MultiQueryConfig = Field(default_factory=MultiQueryConfig)
    reranking_weights: Dict[str, RerankingWeights] = Field(default_factory=dict)
    sentiment_boost: SentimentBoostConfig = Field(default_factory=SentimentBoostConfig)

class StockImpactConfig(BaseModel):
    confidence_thresholds: Dict[str, float] = Field(default_factory=dict)
    fuzzy_match_threshold: float = 0.80

class SupplyChainConfig(BaseModel):
    traversal_depth: int = 1
    min_impact_score: float = 25.0
    weight_decay: float = 0.8

class LLMModelsConfig(BaseModel):
    """Alternative models for specific tasks."""
    fast: str = "llama-3.1-8b-instant"
    reasoning: str = "llama-3.3-70b-versatile"
    structured: str = "llama-3.3-70b-versatile"

class LLMFeaturesConfig(BaseModel):
    """Feature flags for LLM-based components."""
    entity_extraction: bool = True
    stock_mapping: bool = True
    sentiment_analysis: bool = True
    supply_chain: bool = True
    query_expansion: bool = True

class LLMConfig(BaseModel):
    """LLM configuration for Groq integration."""
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 30
    max_retries: int = 3
    models: LLMModelsConfig = Field(default_factory=LLMModelsConfig)
    features: LLMFeaturesConfig = Field(default_factory=LLMFeaturesConfig)

class APIConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    title: str = "Financial News Intelligence API"
    description: str = "Multi-agent AI system for processing and querying financial news"
    version: str = "1.0.0"

class ResourcesConfig(BaseModel):
    company_aliases: str = "company_aliases.json"
    sector_tickers: str = "sector_tickers.json"
    regulators: str = "regulators.json"
    regulator_impact: str = "regulator_sector_impact.json"
    supply_chain_graph: str = "supply_chain_graph.json"

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class PerformanceConfig(BaseModel):
    cache_embeddings: bool = True
    batch_size: int = 32
    num_workers: int = 4

class DevelopmentConfig(BaseModel):
    debug: bool = False
    use_mock_data: bool = False
    mock_data_path: str = "mock_news_data.json"
    enable_profiling: bool = False

class Config(BaseModel):
    """Main configuration class containing all settings."""
    mongodb: MongoDBConfig = Field(default_factory=MongoDBConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    entity_extraction: EntityExtractionConfig = Field(default_factory=EntityExtractionConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    query_processing: QueryProcessingConfig = Field(default_factory=QueryProcessingConfig)
    stock_impact: StockImpactConfig = Field(default_factory=StockImpactConfig)
    supply_chain: SupplyChainConfig = Field(default_factory=SupplyChainConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    resources: ResourcesConfig = Field(default_factory=ResourcesConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)
    prompts: PromptConfig = Field(default_factory=PromptConfig)
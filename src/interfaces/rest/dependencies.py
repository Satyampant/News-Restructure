# FastAPI dependency injection
from functools import lru_cache
from typing import Optional

from fastapi import Depends, FastAPI

from src.configuration.loader import get_config
from src.configuration.settings import Config
from src.infrastructure.llm.groq_client import GroqLLMClient
from src.infrastructure.storage.mongodb.client import MongoDBClient
from src.infrastructure.storage.mongodb.article_repository import ArticleRepository
from src.infrastructure.storage.vector.chroma_client import ChromaDBClient
from src.infrastructure.storage.vector.embeddings import EmbeddingService
from src.infrastructure.storage.cache.redis_cache import RedisCacheService

from src.application.agents.entity_agent import EntityExtractionAgent
from src.application.agents.sentiment_agent import SentimentAnalysisAgent
from src.application.agents.stock_impact_agent import StockImpactAgent
from src.application.agents.supply_chain_agent import SupplyChainAgent
from src.application.agents.deduplication_agent import DeduplicationAgent

from src.application.nodes.ingestion.ingestion_node import IngestionNode
from src.application.nodes.ingestion.deduplication_node import DeduplicationNode
from src.application.nodes.ingestion.entity_extraction_node import EntityExtractionNode
from src.application.nodes.ingestion.impact_mapping_node import ImpactMappingNode
from src.application.nodes.ingestion.sentiment_analysis_node import SentimentAnalysisNode
from src.application.nodes.ingestion.supply_chain_node import SupplyChainNode
from src.application.nodes.ingestion.indexing_node import IndexingNode

from src.application.workflows.ingestion_graph import build_ingestion_graph
from src.application.use_cases.process_article import ProcessArticleUseCase

# Singleton config
@lru_cache()
def get_config_cached() -> Config:
    return get_config()

# Infrastructure dependencies
@lru_cache()
def get_llm_client(config: Config = Depends(get_config_cached)) -> GroqLLMClient:
    return GroqLLMClient(
        model=config.llm.model,
        temperature=config.llm.temperature
    )

@lru_cache()
def get_mongodb_client(config: Config = Depends(get_config_cached)) -> MongoDBClient:
    client = MongoDBClient(
        connection_string=config.mongodb.connection_string,
        database_name=config.mongodb.database_name
    )
    client.connect()
    return client

def get_article_repository(
    mongo: MongoDBClient = Depends(get_mongodb_client),
    config: Config = Depends(get_config_cached)
) -> ArticleRepository:
    return ArticleRepository(
        client=mongo,
        collection_name=config.mongodb.collection_name
    )

@lru_cache()
def get_redis_service(config: Config = Depends(get_config_cached)) -> RedisCacheService:
    return RedisCacheService(
        host=config.redis.host,
        port=config.redis.port,
        password=config.redis.password
    )

@lru_cache()
def get_embedding_service(config: Config = Depends(get_config_cached)) -> EmbeddingService:
    return EmbeddingService(
        model_name=config.vector_store.embedding_model
    )

@lru_cache()
def get_vector_store(
    config: Config = Depends(get_config_cached),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> ChromaDBClient:
    return ChromaDBClient(
        collection_name=config.vector_store.collection_name,
        persist_directory=config.vector_store.persist_directory,
        embedding_service=embedding_service
    )

# Agent dependencies
@lru_cache()
def get_entity_agent(
    llm: GroqLLMClient = Depends(get_llm_client),
    cache: RedisCacheService = Depends(get_redis_service)
) -> EntityExtractionAgent:
    return EntityExtractionAgent(llm_client=llm, cache_service=cache)

@lru_cache()
def get_sentiment_agent(llm: GroqLLMClient = Depends(get_llm_client)) -> SentimentAnalysisAgent:
    return SentimentAnalysisAgent(llm_client=llm)

@lru_cache()
def get_stock_impact_agent(llm: GroqLLMClient = Depends(get_llm_client)) -> StockImpactAgent:
    return StockImpactAgent(llm_client=llm)

@lru_cache()
def get_supply_chain_agent(llm: GroqLLMClient = Depends(get_llm_client)) -> SupplyChainAgent:
    return SupplyChainAgent(llm_client=llm)

@lru_cache()
def get_deduplication_agent() -> DeduplicationAgent:
    return DeduplicationAgent()

# Use case dependencies
def get_process_article_use_case(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    dedup_agent: DeduplicationAgent = Depends(get_deduplication_agent),
    article_repo: ArticleRepository = Depends(get_article_repository),
    vector_store: ChromaDBClient = Depends(get_vector_store),
    entity_agent: EntityExtractionAgent = Depends(get_entity_agent),
    stock_agent: StockImpactAgent = Depends(get_stock_impact_agent),
    sentiment_agent: SentimentAnalysisAgent = Depends(get_sentiment_agent),
    supply_agent: SupplyChainAgent = Depends(get_supply_chain_agent),
) -> ProcessArticleUseCase:
    
    # Build Nodes
    ingestion_node = IngestionNode(embedding_service=embedding_service)
    
    dedup_node = DeduplicationNode(
        dedup_agent=dedup_agent,
        article_repo=article_repo,
        vector_store=vector_store
    )
    
    entity_node = EntityExtractionNode(entity_agent=entity_agent)
    
    impact_node = ImpactMappingNode(stock_agent=stock_agent)
    
    sentiment_node = SentimentAnalysisNode(sentiment_agent=sentiment_agent)
    
    supply_chain_node = SupplyChainNode(supply_chain_agent=supply_agent)
    
    indexing_node = IndexingNode(
        article_repo=article_repo,
        vector_store=vector_store
    )
    
    # Build Graph
    graph = build_ingestion_graph(
        ingestion_node=ingestion_node,
        dedup_node=dedup_node,
        entity_node=entity_node,
        impact_node=impact_node,
        sentiment_node=sentiment_node,
        supply_chain_node=supply_chain_node,
        indexing_node=indexing_node
    )
    
    return ProcessArticleUseCase(graph=graph)

def setup_dependencies(app: FastAPI):
    """Configure dependency injection for the app."""
    # Can add startup/shutdown events here
    pass
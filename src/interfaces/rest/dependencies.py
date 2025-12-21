# src/interfaces/rest/dependencies.py
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
from src.application.agents.query_router_agent import QueryRouterAgent
from src.application.agents.query_processor_agent import QueryProcessorAgent

from src.application.nodes.ingestion.ingestion_node import IngestionNode
from src.application.nodes.ingestion.deduplication_node import DeduplicationNode
from src.application.nodes.ingestion.entity_extraction_node import EntityExtractionNode
from src.application.nodes.ingestion.impact_mapping_node import ImpactMappingNode
from src.application.nodes.ingestion.sentiment_analysis_node import SentimentAnalysisNode
from src.application.nodes.ingestion.supply_chain_node import SupplyChainNode
from src.application.nodes.ingestion.indexing_node import IndexingNode

from src.application.workflows.ingestion_graph import build_ingestion_graph
from src.application.use_cases.process_article import ProcessArticleUseCase
from src.application.use_cases.execute_query import ExecuteQueryUseCase

# Singleton config
@lru_cache()
def get_config_cached() -> Config:
    return get_config()

# Infrastructure dependencies
# FIX: Removed arguments from cached functions to avoid "unhashable type: Config" error.
# We call get_config_cached() directly inside instead.

@lru_cache()
def get_llm_client() -> GroqLLMClient:
    config = get_config_cached()
    return GroqLLMClient(
        model=config.llm.model,
        temperature=config.llm.temperature
    )

@lru_cache()
def get_mongodb_client() -> MongoDBClient:
    config = get_config_cached()
    client = MongoDBClient(
        connection_string=config.mongodb.connection_string,
        database_name=config.mongodb.database_name
    )
    client.connect()
    return client

# This is NOT cached, so it can accept arguments via Depends without issues
def get_article_repository(
    mongo: MongoDBClient = Depends(get_mongodb_client),
    config: Config = Depends(get_config_cached)
) -> ArticleRepository:
    return ArticleRepository(
        client=mongo,
        collection_name=config.mongodb.collection_name
    )

@lru_cache()
def get_redis_service() -> RedisCacheService:
    config = get_config_cached()
    return RedisCacheService(
        host=config.redis.host,
        port=config.redis.port,
        password=config.redis.password
    )

@lru_cache()
def get_embedding_service() -> EmbeddingService:
    config = get_config_cached()
    return EmbeddingService(
        model_name=config.vector_store.embedding_model
    )

@lru_cache()
def get_vector_store() -> ChromaDBClient:
    config = get_config_cached()
    embedding_service = get_embedding_service() # Call directly
    return ChromaDBClient(
        collection_name=config.vector_store.collection_name,
        persist_directory=config.vector_store.persist_directory,
        embedding_service=embedding_service
    )

# Agent dependencies
# Updated these to also be parameterless for consistency and safety with lru_cache

@lru_cache()
def get_entity_agent() -> EntityExtractionAgent:
    llm = get_llm_client()
    cache = get_redis_service()
    return EntityExtractionAgent(llm_client=llm, cache_service=cache)

@lru_cache()
def get_sentiment_agent() -> SentimentAnalysisAgent:
    llm = get_llm_client()
    return SentimentAnalysisAgent(llm_client=llm)

@lru_cache()
def get_stock_impact_agent() -> StockImpactAgent:
    llm = get_llm_client()
    return StockImpactAgent(llm_client=llm)

@lru_cache()
def get_supply_chain_agent() -> SupplyChainAgent:
    llm = get_llm_client()
    return SupplyChainAgent(llm_client=llm)

@lru_cache()
def get_deduplication_agent() -> DeduplicationAgent:
    return DeduplicationAgent()

@lru_cache()
def get_query_router_agent() -> QueryRouterAgent:
    llm = get_llm_client()
    return QueryRouterAgent(llm_client=llm)

# Query Processor is NOT cached (it holds request-specific logic if any), so it can use Depends
def get_query_processor_agent(
    article_repo: ArticleRepository = Depends(get_article_repository),
    vector_store: ChromaDBClient = Depends(get_vector_store),
    query_router: QueryRouterAgent = Depends(get_query_router_agent),
    config: Config = Depends(get_config_cached)
) -> QueryProcessorAgent:
    return QueryProcessorAgent(
        article_repo=article_repo,
        vector_store=vector_store,
        query_router=query_router,
        config=config
    )

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
    
    impact_node = ImpactMappingNode(impact_agent=stock_agent)
    
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

def get_execute_query_use_case(
    query_processor: QueryProcessorAgent = Depends(get_query_processor_agent)
) -> ExecuteQueryUseCase:
    return ExecuteQueryUseCase(query_processor=query_processor)

def setup_dependencies(app: FastAPI):
    """Configure dependency injection for the app."""
    # Can add startup/shutdown events here
    pass
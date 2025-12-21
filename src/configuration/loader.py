# Configuration loading logic
import os
import yaml
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from src.configuration.settings import (
    Config, 
    MongoDBConfig, 
    DeduplicationConfig, 
    EntityExtractionConfig,
    VectorStoreConfig,
    QueryProcessingConfig,
    LLMRoutingConfig,
    MultiQueryConfig,
    RerankingWeights,
    SentimentBoostConfig,
    StockImpactConfig,
    SupplyChainConfig,
    LLMConfig,
    LLMModelsConfig,
    LLMFeaturesConfig,
    RedisConfig,
    APIConfig,
    LoggingConfig,
    PerformanceConfig,
    DevelopmentConfig,
    PromptConfig,
    EntityExtractionPrompts,
    SentimentAnalysisPrompts,
    StockMappingPrompts,
    SupplyChainPrompts,
    QueryRoutingPrompts
)

load_dotenv()

# Resolve paths
# src/configuration/loader.py -> src/configuration/ -> src/ -> root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT_DIR / "config"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

# Determine which config file to use based on environment
ENV = os.getenv("ENV", "development")
CONFIG_FILE = CONFIG_DIR / f"{ENV}.yaml"

def load_prompts(prompts_dir: Path) -> PromptConfig:
    """Load prompts from individual YAML files in prompts directory."""
    prompts_config = PromptConfig()
    
    try:
        if not prompts_dir.exists():
            print(f"⚠ Prompts directory not found: {prompts_dir}")
            print(f"  Creating empty prompts directory at: {prompts_dir}")
            prompts_dir.mkdir(parents=True, exist_ok=True)
            return prompts_config
        
        # Load entity_extraction.yaml
        entity_file = prompts_dir / "entity_extraction.yaml"
        if entity_file.exists():
            with open(entity_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            prompts_config.entity_extraction = EntityExtractionPrompts(
                system_message=data.get('system_message', ''),
                task_prompt=data.get('task_prompt', ''),
                entity_context_format=data.get('entity_context_format', '')
            )
            print(f"  ✓ Loaded entity_extraction.yaml")
        else:
            print(f"  ⚠ entity_extraction.yaml not found")
        
        # Load sentiment_analysis.yaml
        sentiment_file = prompts_dir / "sentiment_analysis.yaml"
        if sentiment_file.exists():
            with open(sentiment_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            prompts_config.sentiment_analysis = SentimentAnalysisPrompts(
                system_message=data.get('system_message', ''),
                task_prompt=data.get('task_prompt', ''),
                few_shot_examples=data.get('few_shot_examples', '')
            )
            print(f"  ✓ Loaded sentiment_analysis.yaml")
        else:
            print(f"  ⚠ sentiment_analysis.yaml not found")
        
        # Load stock_impact.yaml
        stock_file = prompts_dir / "stock_impact.yaml"
        if stock_file.exists():
            with open(stock_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            prompts_config.stock_impact = StockMappingPrompts(
                system_message=data.get('system_message', ''),
                task_prompt=data.get('task_prompt', '')
            )
            print(f"  ✓ Loaded stock_impact.yaml")
        else:
            print(f"  ⚠ stock_impact.yaml not found")
        
        # Load supply_chain.yaml
        supply_file = prompts_dir / "supply_chain.yaml"
        if supply_file.exists():
            with open(supply_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            prompts_config.supply_chain = SupplyChainPrompts(
                system_message=data.get('system_message', ''),
                task_prompt=data.get('task_prompt', ''),
                few_shot_examples=data.get('few_shot_examples', '')
            )
            print(f"  ✓ Loaded supply_chain.yaml")
        else:
            print(f"  ⚠ supply_chain.yaml not found")
        
        # Load query_routing.yaml
        query_file = prompts_dir / "query_routing.yaml"
        if query_file.exists():
            with open(query_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            prompts_config.query_routing = QueryRoutingPrompts(
                system_message=data.get('system_message', ''),
                task_prompt=data.get('task_prompt', ''),
                few_shot_examples=data.get('few_shot_examples', '')
            )
            print(f"  ✓ Loaded query_routing.yaml")
        else:
            print(f"  ⚠ query_routing.yaml not found")
        
        print(f"✓ Prompts loading completed from {prompts_dir}")
        
    except Exception as e:
        print(f"⚠ Error loading prompts: {e}")
    
    return prompts_config

def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from YAML file, falling back to defaults if missing."""
    if config_path is None:
        config_path = CONFIG_FILE
    
    try:
        yaml_data = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                yaml_data = yaml.safe_load(f) or {}
            print(f"✓ Config loaded from {config_path}")
        else:
            print(f"⚠ Config file not found at {config_path}")
            print(f"  Available config files in {CONFIG_DIR}:")
            if CONFIG_DIR.exists():
                for file in CONFIG_DIR.glob("*.yaml"):
                    print(f"    - {file.name}")
            print(f"  Using default configuration values")
        
        config = Config()
        
        # --- MongoDB Configuration ---
        mongo = yaml_data.get('mongodb', {})
        config.mongodb = MongoDBConfig(
            connection_string=os.getenv("MONGODB_URL") or mongo.get('connection_string'),
            database_name=mongo.get('database_name', 'MarketMuni'),
            collection_name=mongo.get('collection_name', 'articles'),
            max_pool_size=mongo.get('max_pool_size', 100),
            timeout_ms=mongo.get('timeout_ms', 5000),
            max_filter_ids=mongo.get('max_filter_ids', 1000)
        )
        
        # --- Deduplication ---
        dedup = yaml_data.get('deduplication', {})
        config.deduplication = DeduplicationConfig(
            bi_encoder_threshold=dedup.get('bi_encoder_threshold', 0.50),
            cross_encoder_threshold=dedup.get('cross_encoder_threshold', 0.70),
            cross_encoder_model=dedup.get('cross_encoder_model', 'cross-encoder/stsb-distilroberta-base')
        )
        
        # --- Entity Extraction ---
        entity = yaml_data.get('entity_extraction', {})
        config.entity_extraction = EntityExtractionConfig(
            spacy_model=entity.get('spacy_model', 'en_core_web_sm'),
            use_spacy=entity.get('use_spacy', True),
            event_keywords=entity.get('event_keywords', [])
        )
        
        # --- Vector Store ---
        vs = yaml_data.get('vector_store', {})
        config.vector_store = VectorStoreConfig(
            collection_name=vs.get('collection_name', 'financial_news'),
            persist_directory=vs.get('persist_directory', 'data/chroma_db'),
            embedding_model=vs.get('embedding_model', 'all-mpnet-base-v2'),
            distance_metric=vs.get('distance_metric', 'cosine')
        )
        
        # --- Query Processing  ---
        qp = yaml_data.get('query_processing', {})
        
        # LLM Routing Config
        lr = qp.get('llm_routing', {})
        llm_routing = LLMRoutingConfig(
            enabled=lr.get('enabled', True),
            confidence_threshold=lr.get('confidence_threshold', 0.6),
            fallback_strategy=lr.get('fallback_strategy', 'semantic_search'),
            max_entities_per_query=lr.get('max_entities_per_query', 10),
            enable_query_expansion=lr.get('enable_query_expansion', True)
        )
        
        # Strategy Weights
        strategy_weights = qp.get('strategy_weights', {})
        
        mq = qp.get('multi_query', {})
        multi_query = MultiQueryConfig(
            max_context_queries=mq.get('max_context_queries', 3),
            initial_retrieval_multiplier=mq.get('initial_retrieval_multiplier', 2)
        )
        
        reranking_weights = {}
        rw_data = qp.get('reranking_weights', {})
        for strategy, weights in rw_data.items():
            reranking_weights[strategy] = RerankingWeights(
                strategy_weight=weights.get('strategy_weight', 0.5),
                semantic_weight=weights.get('semantic_weight', 0.5)
            )
        
        sb = qp.get('sentiment_boost', {})
        sentiment_boost = SentimentBoostConfig(
            enabled=sb.get('enabled', True),
            max_multiplier=sb.get('max_multiplier', 1.5)
        )
        
        config.query_processing = QueryProcessingConfig(
            default_top_k=qp.get('default_top_k', 10),
            min_similarity=qp.get('min_similarity', 0.3),
            llm_routing=llm_routing,
            strategy_weights=strategy_weights,
            multi_query=multi_query,
            reranking_weights=reranking_weights,
            sentiment_boost=sentiment_boost
        )
        
        # --- Stock Impact ---
        si = yaml_data.get('stock_impact', {})
        config.stock_impact = StockImpactConfig(
            confidence_thresholds=si.get('confidence_thresholds', {}),
            fuzzy_match_threshold=si.get('fuzzy_match_threshold', 0.80)
        )
        
        # --- Supply Chain ---
        sc = yaml_data.get('supply_chain', {})
        config.supply_chain = SupplyChainConfig(
            traversal_depth=sc.get('traversal_depth', 1),
            min_impact_score=sc.get('min_impact_score', 25.0),
            weight_decay=sc.get('weight_decay', 0.8)
        )
        
        # --- LLM Configuration ---
        llm = yaml_data.get('llm', {})
        
        m = llm.get('models', {})
        models_config = LLMModelsConfig(
            fast=m.get('fast', 'llama-3.1-8b-instant'),
            reasoning=m.get('reasoning', 'llama-3.3-70b-versatile'),
            structured=m.get('structured', 'llama-3.3-70b-versatile')
        )
        
        f = llm.get('features', {})
        features_config = LLMFeaturesConfig(
            entity_extraction=f.get('entity_extraction', True),
            stock_mapping=f.get('stock_mapping', True),
            sentiment_analysis=f.get('sentiment_analysis', True),
            supply_chain=f.get('supply_chain', True),
            query_expansion=f.get('query_expansion', True)
        )
        
        config.llm = LLMConfig(
            provider=llm.get('provider', 'groq'),
            model=llm.get('model', 'llama-3.3-70b-versatile'),
            temperature=llm.get('temperature', 0.1),
            max_tokens=llm.get('max_tokens', 4096),
            timeout=llm.get('timeout', 30),
            max_retries=llm.get('max_retries', 3),
            models=models_config,
            features=features_config
        )

        # --- Redis Configuration ---
        redis_config = yaml_data.get('redis', {})
        
        # Support environment variable override for password
        redis_password = redis_config.get('password')
        if redis_password is None:
            redis_password = os.getenv('REDIS_PASSWORD')
        
        config.redis = RedisConfig(
            enabled=redis_config.get('enabled', True),
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            password=redis_password,
            ttl_seconds=redis_config.get('ttl_seconds', 86400),
            max_connections=redis_config.get('connection_pool', {}).get('max_connections', 50),
            socket_timeout=redis_config.get('connection_pool', {}).get('socket_timeout', 5),
            socket_connect_timeout=redis_config.get('connection_pool', {}).get('socket_connect_timeout', 5)
        )
        
        # --- API ---
        api = yaml_data.get('api', {})
        config.api = APIConfig(
            host=api.get('host', '0.0.0.0'),
            port=api.get('port', 8000),
            reload=api.get('reload', True),
            title=api.get('title', 'Financial News Intelligence API'),
            description=api.get('description', 'Multi-agent AI system'),
            version=api.get('version', '1.0.0')
        )
        
        # --- Logging ---
        log = yaml_data.get('logging', {})
        config.logging = LoggingConfig(
            level=log.get('level', 'INFO'),
            format=log.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # --- Performance ---
        perf = yaml_data.get('performance', {})
        config.performance = PerformanceConfig(
            cache_embeddings=perf.get('cache_embeddings', True),
            batch_size=perf.get('batch_size', 32),
            num_workers=perf.get('num_workers', 4)
        )
        
        # --- Development ---
        dev = yaml_data.get('development', {})
        config.development = DevelopmentConfig(
            debug=dev.get('debug', False),
            use_mock_data=dev.get('use_mock_data', False),
            mock_data_path=dev.get('mock_data_path', 'mock_news_data.json'),
            enable_profiling=dev.get('enable_profiling', False)
        )
        
        # Load Prompts from individual files
        config.prompts = load_prompts(PROMPTS_DIR)
        
        return config
        
    except Exception as e:
        print(f"⚠ Error loading config file: {e}")
        print("  Using default configuration values")
        config = Config()
        config.prompts = load_prompts(PROMPTS_DIR)
        return config

# Singleton instance
_config_instance: Optional[Config] = None

def get_config(reload: bool = False) -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = load_config()
    return _config_instance
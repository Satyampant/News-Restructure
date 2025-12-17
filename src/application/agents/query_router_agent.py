"""
Query Router Agent with MongoDB Filter Generation.
Refactored from app/agents/query_router.py.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator

from src.infrastructure.llm.groq_client import GroqLLMClient, LLMServiceError
from src.infrastructure.llm.prompt_builder import build_query_routing_prompt
from src.domain.models.query import QueryRouting
from src.domain.models.entities import QueryIntent
from src.configuration.loader import get_config


# DTO for LLM Structured Output
# Mirrors QueryRouting domain model but adds Pydantic validation/descriptions for the LLM
class QueryRouterSchema(BaseModel):
    """
    Query routing schema for LLM-based query understanding.
    Determines optimal search strategy and extracts relevant entities.
    """
    strategy: QueryIntent = Field(..., description="Primary search strategy to execute")
    entities: List[str] = Field(
        default_factory=list,
        description="Company names identified in query"
    )
    stock_symbols: List[str] = Field(
        default_factory=list,
        description="Stock ticker symbols extracted or inferred"
    )
    sectors: List[str] = Field(
        default_factory=list,
        description="Industry sectors mentioned or implied"
    )
    regulators: List[str] = Field(
        default_factory=list,
        description="Regulatory bodies mentioned in query"
    )
    sentiment_filter: Optional[str] = Field(
        None,
        description="Sentiment filter: Bullish, Bearish, or Neutral"
    )
    temporal_scope: Optional[str] = Field(
        None,
        description="Time scope: recent, last_week, last_month, etc."
    )
    refined_query: str = Field(
        ...,
        description="Optimized semantic search query for vector retrieval"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in routing decision (0.0-1.0)"
    )
    reasoning: str = Field(
        ...,
        description="Explanation for why this strategy was chosen"
    )
    
    @field_validator('sentiment_filter')
    @classmethod
    def validate_sentiment_filter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_sentiments = ["Bullish", "Bearish", "Neutral"]
            if v not in valid_sentiments:
                raise ValueError(f"Sentiment filter must be one of {valid_sentiments}")
        return v
    
    @field_validator('entities', 'stock_symbols', 'sectors', 'regulators')
    @classmethod
    def validate_list_fields(cls, v: List[str]) -> List[str]:
        return [item.strip() for item in v if item and len(item.strip()) > 0]
    
    @field_validator('refined_query')
    @classmethod
    def validate_refined_query(cls, v: str) -> str:
        if not v or len(v.strip()) < 3:
            raise ValueError("Refined query must be at least 3 characters")
        return v.strip()


class QueryRouterAgent:
    """
    LLM-based query router that generates MongoDB-compatible filters.
    """
    
    def __init__(self, llm_client: Optional[GroqLLMClient] = None):
        self.config = get_config()
        
        if llm_client is None:
            self.llm_client = GroqLLMClient(
                model=self.config.llm.models.fast, # Use fast model for routing
                temperature=0.1
            )
        else:
            self.llm_client = llm_client
        
        print(f"✓ QueryRouterAgent initialized (MongoDB filter generation)")
    
    def _validate_and_enrich(self, raw_result: QueryRouterSchema) -> QueryRouterSchema:
        """Post-process routing result to normalize and deduplicate extracted data."""
        
        # Deduplicate entities (case-insensitive)
        seen_entities = set()
        unique_entities = []
        for entity in raw_result.entities:
            entity_lower = entity.lower().strip()
            if entity_lower and entity_lower not in seen_entities:
                unique_entities.append(entity.strip())
                seen_entities.add(entity_lower)
        raw_result.entities = unique_entities
        
        # Deduplicate and uppercase stock symbols
        raw_result.stock_symbols = list(set(s.upper().strip() for s in raw_result.stock_symbols if s))
        
        # Deduplicate sectors
        seen_sectors = set()
        unique_sectors = []
        for sector in raw_result.sectors:
            sector_lower = sector.lower().strip()
            if sector_lower and sector_lower not in seen_sectors:
                unique_sectors.append(sector.strip())
                seen_sectors.add(sector_lower)
        raw_result.sectors = unique_sectors
        
        # Deduplicate regulators
        seen_regulators = set()
        unique_regulators = []
        for regulator in raw_result.regulators:
            regulator_lower = regulator.lower().strip()
            if regulator_lower and regulator_lower not in seen_regulators:
                unique_regulators.append(regulator.strip())
                seen_regulators.add(regulator_lower)
        raw_result.regulators = unique_regulators
        
        # Ensure refined query is not empty
        if not raw_result.refined_query.strip():
            raw_result.refined_query = raw_result.entities[0] if raw_result.entities else "financial news"
        
        return raw_result
    
    def route_query(self, query: str) -> QueryRouting:
        """
        Route query using LLM reasoning.
        Returns QueryRouting domain object with MongoDB filter generation support.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Prepare system message with few-shot examples
        system_message_template = self.config.prompts.query_routing.system_message
        few_shot_examples = self.config.prompts.query_routing.few_shot_examples
        system_message = f"{system_message_template}\n\n{few_shot_examples}"
            
        # Use Prompt Builder
        prompt_template = self.config.prompts.query_routing.task_prompt
        prompt = build_query_routing_prompt(query, prompt_template)
        
        try:
            # Generate structured output from LLM
            result_dict = self.llm_client.generate_structured_output(
                prompt=prompt,
                schema=QueryRouterSchema,
                system_message=system_message
            )
            
            # Validate and enrich
            raw_result = QueryRouterSchema.model_validate(result_dict)
            validated_result = self._validate_and_enrich(raw_result)
            
            # Convert to Domain Dataclass
            routing = QueryRouting(
                entities=validated_result.entities,
                sectors=validated_result.sectors,
                stock_symbols=validated_result.stock_symbols,
                sentiment_filter=validated_result.sentiment_filter,
                refined_query=validated_result.refined_query,
                strategy=validated_result.strategy,
                confidence=validated_result.confidence,
                reasoning=validated_result.reasoning,
                regulators=validated_result.regulators,
                temporal_scope=validated_result.temporal_scope
            )
            
            return routing
            
        except Exception as e:
            raise LLMServiceError(f"Query routing failed: {e}")
    
    def generate_mongodb_filter(self, routing: QueryRouting) -> Dict[str, Any]:
        """
        Generate MongoDB query filter from routing result.
        
        Returns MongoDB-compatible filter dict based on strategy and extracted entities.
        Empty dict {} means no filtering (unrestricted search).
        """
        
        if routing.strategy == QueryIntent.DIRECT_ENTITY:
            # Priority 1: Filter by stock symbols (highest precision)
            if routing.stock_symbols:
                if len(routing.stock_symbols) == 1:
                    return {
                        "impacted_stocks.symbol": routing.stock_symbols[0]
                    }
                else:
                    return {
                        "impacted_stocks.symbol": {"$in": routing.stock_symbols}
                    }
            
            # Priority 2: Filter by company names
            elif routing.entities:
                if len(routing.entities) == 1:
                    return {
                        "entities.Companies": routing.entities[0]
                    }
                else:
                    return {
                        "entities.Companies": {"$in": routing.entities}
                    }
            
            return {}
        
        elif routing.strategy == QueryIntent.SECTOR_WIDE:
            # Filter by sector names
            if routing.sectors:
                if len(routing.sectors) == 1:
                    return {
                        "entities.Sectors": routing.sectors[0]
                    }
                else:
                    return {
                        "entities.Sectors": {"$in": routing.sectors}
                    }
            return {}
        
        elif routing.strategy == QueryIntent.REGULATORY:
            # Filter by regulator names
            if routing.regulators:
                if len(routing.regulators) == 1:
                    return {
                        "entities.Regulators": routing.regulators[0]
                    }
                else:
                    return {
                        "entities.Regulators": {"$in": routing.regulators}
                    }
            return {}
        
        elif routing.strategy == QueryIntent.SENTIMENT_DRIVEN:
            # Filter by sentiment + optional sectors
            if routing.sentiment_filter:
                base_filter = {
                    "sentiment.classification": routing.sentiment_filter
                }
                
                if routing.sectors:
                    if len(routing.sectors) == 1:
                        return {
                            "$and": [
                                base_filter,
                                {"entities.Sectors": routing.sectors[0]}
                            ]
                        }
                    else:
                        return {
                            "$and": [
                                base_filter,
                                {"entities.Sectors": {"$in": routing.sectors}}
                            ]
                        }
                
                return base_filter
            return {}
        
        elif routing.strategy == QueryIntent.CROSS_IMPACT:
            # Filter by multiple sectors (supply chain analysis)
            if len(routing.sectors) >= 2:
                return {
                    "entities.Sectors": {"$in": routing.sectors}
                }
            elif routing.sectors:
                return {
                    "entities.Sectors": routing.sectors[0]
                }
            return {}
        
        elif routing.strategy == QueryIntent.TEMPORAL:
            # Temporal strategy: Falls back to entity filtering if available
            if routing.stock_symbols:
                if len(routing.stock_symbols) == 1:
                    return {
                        "impacted_stocks.symbol": routing.stock_symbols[0]
                    }
                else:
                    return {
                        "impacted_stocks.symbol": {"$in": routing.stock_symbols}
                    }
            elif routing.entities:
                if len(routing.entities) == 1:
                    return {
                        "entities.Companies": routing.entities[0]
                    }
                else:
                    return {
                        "entities.Companies": {"$in": routing.entities}
                    }
            return {}
        
        elif routing.strategy == QueryIntent.SEMANTIC_SEARCH:
            # No metadata filtering - pure vector search
            return {}
        
        # Default: no filter
        return {}
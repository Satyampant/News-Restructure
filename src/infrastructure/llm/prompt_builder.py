# Prompt construction utilities
from typing import Any, List, Optional
from pydantic import BaseModel

# --- Shared Utilities ---

def format_entity_context(entities: Any) -> str:
    """
    General purpose entity formatter.
    Used by Sentiment Analysis and potentially others.
    """
    if not entities:
        return "No known entities."
    
    # Handle Pydantic model vs dict
    data = entities.model_dump() if isinstance(entities, BaseModel) else entities
        
    context = []
    
    if data.get("companies"):
        comps = [f"{c.get('name')} ({c.get('ticker_symbol', 'N/A')})" for c in data["companies"]]
        context.append(f"Companies: {', '.join(comps)}")
        
    if data.get("sectors"):
        context.append(f"Sectors: {', '.join(data['sectors'])}")
        
    if data.get("regulators"):
        regs = [r.get("name") for r in data["regulators"]]
        context.append(f"Regulators: {', '.join(regs)}")
        
    if data.get("events"):
        events = [f"{e.get('event_type')}: {e.get('description')}" for e in data["events"]]
        context.append(f"Events: {'; '.join(events)}")
        
    return "\n".join(context)


def _format_sentiment_context(sentiment: Any) -> str:
    """Format sentiment metrics for context."""
    # Handle Pydantic model vs dict
    if isinstance(sentiment, BaseModel):
        classification = sentiment.classification.value if hasattr(sentiment.classification, 'value') else sentiment.classification
        signal = sentiment.signal_strength
        conf = sentiment.confidence_score
        factors = sentiment.key_factors
    else:
        classification = sentiment.get("classification")
        signal = sentiment.get("signal_strength")
        conf = sentiment.get("confidence_score")
        factors = sentiment.get("key_factors", [])

    return f"""Sentiment Classification: {classification}
Signal Strength: {signal}/100
Confidence: {conf}/100
Key Factors:
{chr(10).join(f'  - {factor}' for factor in factors[:3])}"""


# --- Specific Prompt Builders ---

def build_entity_extraction_prompt(article, template: str) -> str:
    """Build entity extraction prompt from template."""
    return template.format(
        title=article.title,
        content=article.content
    )


def build_sentiment_prompt(
    article,
    entities,
    template: str,
    few_shot: str
) -> str:
    """Build sentiment analysis prompt."""
    entity_context = format_entity_context(entities)
    return template.format(
        title=article.title,
        content=article.content,
        entity_context=entity_context,
        few_shot=few_shot
    )


def build_stock_impact_prompt(
    article,
    entities,
    template: str,
    max_stocks: int
) -> str:
    """
    Build stock impact analysis prompt.
    Refactored from LLMStockImpactMapper._build_impact_analysis_prompt.
    """
    # Handle Pydantic model vs dict for EntityExtractionSchema
    data = entities.model_dump() if isinstance(entities, BaseModel) else entities
    
    # 1. Format Companies (Specific format for Stock Mapper)
    if data.get("companies"):
        companies_str = "\n".join([
            f"  - {c.get('name')}" + 
            (f" (Ticker: {c.get('ticker_symbol')})" if c.get('ticker_symbol') else "") +
            (f" [Sector: {c.get('sector')}]" if c.get('sector') else "") +
            f" [Confidence: {c.get('confidence', 0.0):.2f}]"
            for c in data["companies"]
        ])
    else:
        companies_str = "  None explicitly mentioned"
    
    # 2. Format Sectors
    sectors_list = data.get("sectors", [])
    sectors_str = ", ".join(sectors_list) if sectors_list else "None"
    
    # 3. Format Regulators
    if data.get("regulators"):
        regulators_str = "\n".join([
            f"  - {r.get('name')}" + 
            (f" ({r.get('jurisdiction')})" if r.get('jurisdiction') else "") +
            f" [Confidence: {r.get('confidence', 0.0):.2f}]"
            for r in data["regulators"]
        ])
    else:
        regulators_str = "  None mentioned"
    
    # 4. Format Events
    if data.get("events"):
        events_str = "\n".join([
            f"  - {e.get('event_type')}: {e.get('description')} [Confidence: {e.get('confidence', 0.0):.2f}]"
            for e in data["events"]
        ])
    else:
        events_str = "  None identified"
    
    return template.format(
        title=article.title,
        content=article.content,
        companies=companies_str,
        sectors=sectors_str,
        regulators=regulators_str,
        events=events_str,
        max_stocks=max_stocks
    )


def build_supply_chain_prompt(
    article,
    entities,
    sentiment,
    template: str,
    min_impact_score: float
) -> str:
    """
    Build supply chain analysis prompt.
    Refactored from LLMSupplyChainAnalyzer._build_analysis_prompt.
    """
    # Supply Chain agent uses a slightly different entity format (compact lists)
    data = entities.model_dump() if isinstance(entities, BaseModel) else entities
    
    context_parts = []
    if data.get("companies"):
        companies_str = ", ".join([c.get("name") for c in data["companies"]])
        context_parts.append(f"Companies: [{companies_str}]")
    
    if data.get("sectors"):
        sectors_str = ", ".join(data["sectors"])
        context_parts.append(f"Sectors: [{sectors_str}]")
    
    if data.get("regulators"):
        regulators_str = ", ".join([r.get("name") for r in data["regulators"]])
        context_parts.append(f"Regulators: [{regulators_str}]")
        
    if data.get("events"):
        events_str = ", ".join([e.get("event_type") for e in data["events"]])
        context_parts.append(f"Events: [{events_str}]")
        
    entity_context = "\n".join(context_parts) if context_parts else "No key entities identified"
    sentiment_context = _format_sentiment_context(sentiment)
    
    # Extract signal strength safely
    if isinstance(sentiment, BaseModel):
        signal_strength = sentiment.signal_strength
    else:
        signal_strength = sentiment.get("signal_strength", 0.0)

    return template.format(
        title=article.title,
        content=article.content,
        entity_context=entity_context,
        sentiment_context=sentiment_context,
        signal_strength=signal_strength,
        min_impact_score=min_impact_score
    )


def build_query_routing_prompt(query: str, template: str) -> str:
    """
    Build query routing prompt.
    Refactored from QueryRouter._build_routing_prompt.
    """
    return template.format(query=query)
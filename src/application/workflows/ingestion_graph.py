# Graph structure + edges
from langgraph.graph import StateGraph, START, END
from src.application.workflows.state import NewsIntelligenceState

# Importing nodes from their specific modules to ensure absolute paths work 
# regardless of __init__.py configuration in the new structure.
from src.application.nodes.ingestion.ingestion_node import IngestionNode
from src.application.nodes.ingestion.deduplication_node import DeduplicationNode
from src.application.nodes.ingestion.entity_extraction_node import EntityExtractionNode
from src.application.nodes.ingestion.impact_mapping_node import ImpactMappingNode
from src.application.nodes.ingestion.sentiment_analysis_node import SentimentAnalysisNode
from src.application.nodes.ingestion.supply_chain_node import SupplyChainNode
from src.application.nodes.ingestion.indexing_node import IndexingNode

def build_ingestion_graph(
    ingestion_node: IngestionNode,
    dedup_node: DeduplicationNode,
    entity_node: EntityExtractionNode,
    impact_node: ImpactMappingNode,
    sentiment_node: SentimentAnalysisNode,
    supply_chain_node: SupplyChainNode,
    indexing_node: IndexingNode
):
    """
    Build the news ingestion LangGraph pipeline.
    
    This function accepts instantiated nodes (with their dependencies injected)
    and wires them together into a stateful graph.
    """
    
    # Initialize the graph with the typed state
    graph = StateGraph(NewsIntelligenceState)
    
    # Add nodes with their process methods
    # The .process method of each node class is registered as the runnable for that step
    graph.add_node("ingestion", ingestion_node.process)
    graph.add_node("deduplication", dedup_node.process)
    graph.add_node("entity_extraction", entity_node.process)
    graph.add_node("impact_mapper", impact_node.process)
    graph.add_node("sentiment_analysis", sentiment_node.process)
    graph.add_node("cross_impact", supply_chain_node.process)
    graph.add_node("indexing", indexing_node.process)
    
    # Define edges (workflow)
    # 1. Start -> Ingestion
    graph.add_edge(START, "ingestion")
    
    # 2. Ingestion -> Deduplication
    graph.add_edge("ingestion", "deduplication")
    
    # 3. Deduplication -> Entity Extraction
    # Note: Logic inside deduplication node determines if we skip processing,
    # but the linear graph flow passes state to entity extraction next.
    # Conditional edges could be added here if deduplication should halt the flow,
    # but strictly following the migration plan's linear flow:
    graph.add_edge("deduplication", "entity_extraction")
    
    # 4. Entity Extraction -> Impact Mapping
    graph.add_edge("entity_extraction", "impact_mapper")
    
    # 5. Impact Mapping -> Sentiment Analysis
    graph.add_edge("impact_mapper", "sentiment_analysis")
    
    # 6. Sentiment Analysis -> Cross Impact (Supply Chain)
    graph.add_edge("sentiment_analysis", "cross_impact")
    
    # 7. Cross Impact -> Indexing
    graph.add_edge("cross_impact", "indexing")
    
    # 8. Indexing -> End
    graph.add_edge("indexing", END)
    
    return graph.compile()
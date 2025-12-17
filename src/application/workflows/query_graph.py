# Graph structure + edges
from langgraph.graph import StateGraph, START, END
from src.application.workflows.state import NewsIntelligenceState
from src.application.nodes.query.query_node import QueryNode


def build_query_graph(query_node: QueryNode):
    """
    Build the query processing LangGraph pipeline.
    
    Args:
        query_node: Configured QueryNode instance.
        
    Returns:
        Compiled StateGraph for query execution.
    """
    graph = StateGraph(NewsIntelligenceState)

    # Add query processing node
    graph.add_node("query", query_node.process)

    # Define simple linear flow
    graph.add_edge(START, "query")
    graph.add_edge("query", END)

    return graph.compile()
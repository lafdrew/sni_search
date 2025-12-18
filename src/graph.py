"""StateGraph builder for SNI RAG system."""

from typing import Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic

from src.config import settings
from src.state import SNIGraphState, create_initial_state
from src.tools import SNITools
from src.nodes import SNIGraphNodes


def create_sni_graph(
    qdrant_url: Optional[str] = None,
    api_key: Optional[str] = None,
    use_checkpointer: bool = True,
):
    """Create SNI recognition StateGraph.

    Args:
        qdrant_url: Qdrant server URL
        api_key: Anthropic API key
        use_checkpointer: Whether to use memory checkpointer

    Returns:
        Compiled LangGraph application
    """
    # Initialize LLM
    llm_kwargs = {
        "model": settings.CLAUDE_MODEL,
        "api_key": api_key or settings.ANTHROPIC_API_KEY,
        "temperature": 0,
    }
    if settings.ANTHROPIC_BASE_URL:
        llm_kwargs["base_url"] = settings.ANTHROPIC_BASE_URL

    llm = ChatAnthropic(**llm_kwargs)

    # Initialize tools
    tools = SNITools(qdrant_url=qdrant_url or settings.QDRANT_URL)

    # Initialize nodes
    nodes = SNIGraphNodes(llm, tools)

    # Create StateGraph
    workflow = StateGraph(SNIGraphState)

    # Add nodes
    workflow.add_node("understand", nodes.understand_query)
    workflow.add_node("exact_search", nodes.exact_search_node)
    workflow.add_node("vector_search", nodes.vector_search_node)
    workflow.add_node("domain_search", nodes.domain_search_node)
    workflow.add_node("aggregate", nodes.aggregate_results)
    workflow.add_node("generate", nodes.generate_answer)

    # Set entry point
    workflow.set_entry_point("understand")

    # Add conditional edges from understand node
    workflow.add_conditional_edges(
        "understand",
        nodes.route_query,
        {
            "exact_search": "exact_search",
            "vector_search": "vector_search",
            "domain_search": "domain_search",
        },
    )

    # All search nodes lead to aggregate
    workflow.add_edge("exact_search", "aggregate")
    workflow.add_edge("vector_search", "aggregate")
    workflow.add_edge("domain_search", "aggregate")

    # Conditional edges from aggregate
    workflow.add_conditional_edges(
        "aggregate",
        nodes.should_continue,
        {
            "vector_search": "vector_search",
            "generate_answer": "generate",
        },
    )

    # Generate leads to END
    workflow.add_edge("generate", END)

    # Compile with optional checkpointer
    if use_checkpointer:
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)
    else:
        app = workflow.compile()

    return app


def query_sni(
    query: str,
    app=None,
    session_id: Optional[str] = None,
) -> dict:
    """Execute SNI query.

    Args:
        query: User query string
        app: Pre-compiled graph application (optional)
        session_id: Session ID for state tracking

    Returns:
        Query result dictionary
    """
    if app is None:
        app = create_sni_graph()

    initial_state = create_initial_state(query)

    config = {}
    if session_id:
        config = {"configurable": {"thread_id": session_id}}

    result = app.invoke(initial_state, config=config)

    return {
        "query": query,
        "answer": result.get("answer"),
        "tool_calls": result.get("tool_calls", []),
        "steps": result.get("step_count", 0),
    }


async def aquery_sni(
    query: str,
    app=None,
    session_id: Optional[str] = None,
) -> dict:
    """Execute SNI query asynchronously.

    Args:
        query: User query string
        app: Pre-compiled graph application (optional)
        session_id: Session ID for state tracking

    Returns:
        Query result dictionary
    """
    if app is None:
        app = create_sni_graph()

    initial_state = create_initial_state(query)

    config = {}
    if session_id:
        config = {"configurable": {"thread_id": session_id}}

    result = await app.ainvoke(initial_state, config=config)

    return {
        "query": query,
        "answer": result.get("answer"),
        "tool_calls": result.get("tool_calls", []),
        "steps": result.get("step_count", 0),
    }


async def stream_sni_query(query: str, app=None, session_id: Optional[str] = None):
    """Stream SNI query execution.

    Args:
        query: User query string
        app: Pre-compiled graph application (optional)
        session_id: Session ID for state tracking

    Yields:
        Execution events from each node
    """
    if app is None:
        app = create_sni_graph()

    initial_state = create_initial_state(query)

    config = {}
    if session_id:
        config = {"configurable": {"thread_id": session_id}}

    async for event in app.astream(initial_state, config=config):
        for node_name, node_output in event.items():
            yield {
                "node": node_name,
                "output": node_output,
            }


def visualize_graph(output_path: str = "sni_graph.png"):
    """Visualize the StateGraph.

    Args:
        output_path: Output file path for the graph image
    """
    app = create_sni_graph(use_checkpointer=False)

    try:
        mermaid_png = app.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(mermaid_png)
        print(f"Graph saved to {output_path}")
    except Exception as e:
        print(f"Could not generate graph image: {e}")
        # Fallback to mermaid text
        mermaid_code = app.get_graph().draw_mermaid()
        print("Mermaid diagram:")
        print(mermaid_code)


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        app = create_sni_graph()

        # Test query
        result = await aquery_sni("www.google.com", app=app)
        print(f"Answer: {result['answer']}")
        print(f"Steps: {result['steps']}")
        print(f"Tool calls: {result['tool_calls']}")

    asyncio.run(main())

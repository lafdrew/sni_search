"""Build LangGraph workflow for SNI Agent."""

import logging
from typing import Optional

from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from src.graph.state import SNIAgentState
from src.graph.nodes import (
    SNIWorkflowNodes,
    should_try_vector_search,
    should_web_search
)
from src.tools import SNITools
from src.config import settings

logger = logging.getLogger(__name__)


def _create_llm(
    provider: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0,
    max_tokens: int = 200000,
):
    """Create LLM instance based on provider.

    Args:
        provider: LLM provider name ("claude" or "openai")
        model: Model name
        api_key: API key
        base_url: Optional base URL
        temperature: Temperature setting
        max_tokens: Maximum tokens

    Returns:
        LangChain ChatModel instance

    Raises:
        ValueError: If provider is unsupported
    """
    provider = provider.lower()

    if provider == "claude":
        llm_kwargs = {
            "model": model or settings.CLAUDE_MODEL,
            "api_key": api_key or settings.ANTHROPIC_API_KEY,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if base_url or settings.ANTHROPIC_BASE_URL:
            llm_kwargs["base_url"] = base_url or settings.ANTHROPIC_BASE_URL

        logger.info(f"[_create_llm] Creating Claude LLM: {llm_kwargs['model']}")
        return ChatAnthropic(**llm_kwargs)

    elif provider == "openai":
        llm_kwargs = {
            "model": model or settings.OPENAI_MODEL,
            "api_key": api_key or settings.OPENAI_API_KEY,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if base_url or settings.OPENAI_BASE_URL:
            llm_kwargs["base_url"] = base_url or settings.OPENAI_BASE_URL

        logger.info(f"[_create_llm] Creating OpenAI LLM: {llm_kwargs['model']}")
        return ChatOpenAI(**llm_kwargs)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Must be 'claude' or 'openai'")


def create_sni_graph(
    qdrant_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    locale: str = "en-US"
):
    """Create and compile SNI Agent LangGraph workflow.

    New multi-round search workflow:
    1. Exact SNI match
    2. Vector search + initial web search (parallel)
    3. Round 1: Generate 4 queries → 4 parallel searches
    4. Round 2: Extract 2 keywords → 2 parallel searches
    5. Final: Generate ultimate query → 1 final search
    6. Synthesize comprehensive answer

    All flow control is in PYTHON CODE for 100% reliability.

    LLM Provider: Supports both Claude and OpenAI. The provider is selected via
    the LLM_PROVIDER configuration. When passing api_key/model parameters, ensure
    they match the configured provider.

    Args:
        qdrant_url: Qdrant server URL
        api_key: API key (Claude or OpenAI, depending on LLM_PROVIDER)
        model: Model name (Claude or OpenAI model, depending on LLM_PROVIDER)
        locale: Language locale (en-US, zh-CN, etc.)

    Returns:
        Compiled LangGraph workflow
    """
    logger.info("[create_sni_graph] Building multi-round SNI search workflow")

    tools_instance = SNITools(qdrant_url=qdrant_url or settings.QDRANT_URL)

    llm = _create_llm(
        provider=settings.LLM_PROVIDER,
        model=model,
        api_key=api_key,
        temperature=0,
        max_tokens=200000,
    )

    nodes = SNIWorkflowNodes(tools_instance, llm, locale)

    workflow = StateGraph(SNIAgentState)

    workflow.add_node("sni_exact_query", nodes.sni_exact_query_node)
    workflow.add_node("vector_search", nodes.sni_vector_query_node)
    workflow.add_node("initial_web_search", nodes.initial_web_search_node)
    workflow.add_node("round1_planning", nodes.round1_planning_node)
    workflow.add_node("round1_search", nodes.round1_parallel_search_node)
    workflow.add_node("round2_planning", nodes.round2_planning_node)
    workflow.add_node("round2_search", nodes.round2_parallel_search_node)
    workflow.add_node("final_planning", nodes.final_search_planning_node)
    workflow.add_node("final_search", nodes.final_search_node)
    workflow.add_node("synthesize", nodes.synthesize_node)

    workflow.set_entry_point("sni_exact_query")

    workflow.add_conditional_edges(
        "sni_exact_query",
        should_try_vector_search,
        {
            "vector_search": "vector_search",
            "synthesize": "synthesize"
        }
    )

    workflow.add_edge("vector_search", "initial_web_search")
    workflow.add_edge("initial_web_search", "round1_planning")
    workflow.add_edge("round1_planning", "round1_search")
    workflow.add_edge("round1_search", "round2_planning")
    workflow.add_edge("round2_planning", "round2_search")
    workflow.add_edge("round2_search", "final_planning")
    workflow.add_edge("final_planning", "final_search")
    workflow.add_edge("final_search", "synthesize")
    workflow.add_edge("synthesize", END)

    compiled_graph = workflow.compile()

    logger.info("[create_sni_graph] Multi-round workflow compiled successfully")
    logger.info("""
    New workflow structure:

    START → sni_exact_query
              ↓
              ├─[has results]─→ synthesize → END
              └─[no results]──→ vector_search
                                  ↓
                                  initial_web_search (direct SNI search)
                                  ↓
                                  round1_planning (LLM generates 4 queries)
                                  ↓
                                  round1_search (4 parallel searches)
                                  ↓
                                  round2_planning (LLM extracts 2 keywords)
                                  ↓
                                  round2_search (2 parallel searches)
                                  ↓
                                  final_planning (LLM generates final query)
                                  ↓
                                  final_search (1 comprehensive search)
                                  ↓
                                  synthesize → END

    Total: Up to 8 web searches (1 initial + 4 round1 + 2 round2 + 1 final)
    """)

    return compiled_graph


def visualize_graph(graph):
    """Visualize the workflow graph (requires graphviz).

    Args:
        graph: Compiled LangGraph workflow

    Returns:
        Mermaid diagram string
    """
    try:
        # Try to get mermaid diagram
        return graph.get_graph().draw_mermaid()
    except Exception as e:
        logger.warning(f"Could not visualize graph: {e}")
        return None

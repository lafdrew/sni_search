"""SNI RAG Agent with LangGraph workflow."""

import logging
from typing import Optional, Dict, Any

from src.config import settings
from src.graph import create_sni_graph

logger = logging.getLogger(__name__)


class SNIAgent:
    """SNI Recognition Agent using LangGraph workflow.

    This agent uses a deterministic workflow where all flow control
    is handled by Python code, not LLM decisions. This provides:

    - 100% reliable flow control
    - Faster execution (less LLM inference)
    - Lower cost (40%+ token savings)
    - Better debuggability

    Workflow:
        1. Query SNI database (exact match)
        2. If no results → Query SNI database (vector similarity)
        3. If poor results → Search web
        4. If official site found → Crawl content
        5. Synthesize final answer with LLM
    """

    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        locale: str = "en-US",
    ):
        """Initialize SNI Agent with LangGraph workflow.

        Supports multiple LLM providers (Claude, OpenAI) via the LLM_PROVIDER
        configuration in .env file. When passing api_key/model parameters,
        ensure they match the configured provider.

        Args:
            qdrant_url: Qdrant server URL
            api_key: LLM API key (Claude or OpenAI, depending on LLM_PROVIDER)
            model: LLM model name (Claude or OpenAI model, depending on LLM_PROVIDER)
            locale: Language locale (e.g., en-US, zh-CN)
        """
        self.locale = locale

        # 根据配置的提供商选择正确的默认参数
        provider = settings.LLM_PROVIDER

        if provider == "claude":
            default_api_key = settings.ANTHROPIC_API_KEY
            default_model = settings.CLAUDE_MODEL
        elif provider == "openai":
            default_api_key = settings.OPENAI_API_KEY
            default_model = settings.OPENAI_MODEL
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        # Create LangGraph workflow
        self.graph = create_sni_graph(
            qdrant_url=qdrant_url or settings.QDRANT_URL,
            api_key=api_key or default_api_key,
            model=model or default_model,
            locale=locale
        )

        logger.info(f"SNI Agent initialized with locale: {locale}, provider: {provider}, model: {default_model}")

    def query(
        self,
        query: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Execute SNI query using LangGraph workflow.

        Args:
            query: User query string
            verbose: If True, print detailed execution process

        Returns:
            Query result dictionary with answer and metadata
        """
        if verbose:
            print("\n" + "="*80)
            print(f"[SNI Agent] Query: {query}")
            print(f"[SNI Agent] Locale: {self.locale}")
            print("="*80)

        # Prepare initial state
        initial_state = {
            "messages": [],
            "query": query,
            "sni_exact_results": None,
            "sni_vector_results": None,
            "web_search_results": None,
            "crawled_content": None,
            "final_answer": None,
            "locale": self.locale,
            "initial_search_result": None,
            "round1_queries": None,
            "round1_results": None,
            "round2_keywords": None,
            "round2_results": None,
            "final_search_query": None,
            "final_search_result": None,
            "raw_answer": None,
            "tgt_metadata": None
        }

        # Execute workflow
        try:
            result = self.graph.invoke(initial_state)

            if verbose:
                print("\n" + "="*80)
                print("[SNI Agent] Workflow Execution Complete")
                print("="*80)
                self._print_execution_summary(result)
                print("\n[Final Answer]")
                print("-"*80)
                answer = result.get("final_answer", "No answer generated")
                print(answer[:500] + "..." if len(answer) > 500 else answer)
                print("="*80)

            return {
                "query": query,
                "answer": result.get("final_answer", "No answer generated"),
                "metadata": {
                    "has_exact_results": bool(result.get("sni_exact_results")),
                    "has_vector_results": bool(result.get("sni_vector_results")),
                    "has_web_results": bool(result.get("web_search_results")),
                    "crawled": result.get("crawled_content") is not None,
                    "locale": self.locale
                }
            }

        except Exception as e:
            logger.error(f"Error during query execution: {e}", exc_info=True)

            if verbose:
                print(f"\n[Error] {e}")
                print("="*80)

            return {
                "query": query,
                "answer": f'{{"tgt": "Error", "Explanation": "An error occurred", "Query Results": "{str(e)}"}}',
                "metadata": {"error": str(e)}
            }

    async def aquery(
        self,
        query: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Execute SNI query asynchronously using LangGraph workflow.

        Args:
            query: User query string
            verbose: If True, print detailed execution process

        Returns:
            Query result dictionary with answer and metadata
        """
        if verbose:
            print("\n" + "="*80)
            print(f"[SNI Agent] Async Query: {query}")
            print(f"[SNI Agent] Locale: {self.locale}")
            print("="*80)

        # Prepare initial state
        initial_state = {
            "messages": [],
            "query": query,
            "sni_exact_results": None,
            "sni_vector_results": None,
            "web_search_results": None,
            "crawled_content": None,
            "final_answer": None,
            "locale": self.locale,
            "initial_search_result": None,
            "round1_queries": None,
            "round1_results": None,
            "round2_keywords": None,
            "round2_results": None,
            "final_search_query": None,
            "final_search_result": None,
            "raw_answer": None,
            "tgt_metadata": None
        }

        # Execute workflow asynchronously
        try:
            result = await self.graph.ainvoke(initial_state)

            if verbose:
                print("\n" + "="*80)
                print("[SNI Agent] Workflow Execution Complete")
                print("="*80)
                self._print_execution_summary(result)
                print("\n[Final Answer]")
                print("-"*80)
                answer = result.get("final_answer", "No answer generated")
                print(answer[:500] + "..." if len(answer) > 500 else answer)
                print("="*80)

            return {
                "query": query,
                "answer": result.get("final_answer", "No answer generated"),
                "metadata": {
                    "has_exact_results": bool(result.get("sni_exact_results")),
                    "has_vector_results": bool(result.get("sni_vector_results")),
                    "has_web_results": bool(result.get("web_search_results")),
                    "crawled": result.get("crawled_content") is not None,
                    "locale": self.locale
                }
            }

        except Exception as e:
            logger.error(f"Error during async query execution: {e}", exc_info=True)

            if verbose:
                print(f"\n[Error] {e}")
                print("="*80)

            return {
                "query": query,
                "answer": f'{{"tgt": "Error", "Explanation": "An error occurred", "Query Results": "{str(e)}"}}',
                "metadata": {"error": str(e)}
            }

    async def aquery_stream(
        self,
        query: str,
        verbose: bool = True
    ):
        """Execute SNI query with SSE streaming events.

        Args:
            query: User query string
            verbose: If True, print detailed execution process

        Yields:
            dict: Event with 'type' and 'data' keys for SSE streaming
        """
        from datetime import datetime

        if verbose:
            print("\n" + "="*80)
            print(f"[SNI Agent] Stream Query: {query}")
            print(f"[SNI Agent] Locale: {self.locale}")
            print("="*80)

        # Prepare initial state
        initial_state = {
            "messages": [],
            "query": query,
            "sni_exact_results": None,
            "sni_vector_results": None,
            "web_search_results": None,
            "crawled_content": None,
            "final_answer": None,
            "locale": self.locale,
            "initial_search_result": None,
            "round1_queries": None,
            "round1_results": None,
            "round2_keywords": None,
            "round2_results": None,
            "final_search_query": None,
            "final_search_result": None,
            "raw_answer": None,
            "tgt_metadata": None
        }

        try:
            import time
            node_start_time = time.time()

            # Stream execution using LangGraph's astream
            async for chunk in self.graph.astream(initial_state):
                # chunk format: {node_name: {updated_state}}
                for node_name, node_state in chunk.items():
                    elapsed = time.time() - node_start_time

                    if verbose:
                        print(f"[SNI Agent] Node completed: {node_name} (in {elapsed:.2f}s)")

                    node_start_time = time.time()

                    # Extract relevant state for this node
                    extract_start = time.time()
                    event = {
                        "type": f"node_{node_name}",
                        "data": {
                            "node": node_name,
                            "state": self._extract_relevant_state(node_name, node_state),
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    extract_elapsed = time.time() - extract_start

                    if verbose and extract_elapsed > 0.1:
                        print(f"[SNI Agent] State extraction took: {extract_elapsed:.2f}s")

                    yield event

            # Send completion event
            yield {
                "type": "search_completed",
                "data": {
                    "timestamp": datetime.now().isoformat()
                }
            }

            if verbose:
                print("\n" + "="*80)
                print("[SNI Agent] Stream Execution Complete")
                print("="*80)

        except Exception as e:
            logger.error(f"Error during streaming query: {e}", exc_info=True)

            yield {
                "type": "error",
                "data": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }

    def _extract_relevant_state(self, node_name: str, state: dict) -> dict:
        """Extract relevant state information for each node type.

        Args:
            node_name: Name of the node that completed
            state: Current state dictionary

        Returns:
            Filtered state dict with only relevant keys for this node
        """
        mapping = {
            "sni_exact_query": ["sni_exact_results"],
            "vector_search": ["sni_vector_results"],
            "initial_web_search": ["initial_search_result"],
            "keyword_extraction": ["extracted_keywords", "enhanced_query"],
            "round1_planning": ["round1_queries"],
            "round1_search": ["round1_results"],
            "round2_planning": ["round2_keywords"],
            "round2_search": ["round2_results"],
            "final_planning": ["final_search_query"],
            "final_search": ["final_search_result"],
            "synthesize": ["raw_answer"],
            "tgt_standardization": ["final_answer", "tgt_metadata"]
        }

        relevant_keys = mapping.get(node_name, [])
        result = {}

        for key in relevant_keys:
            if key in state and state[key] is not None:
                # Convert to JSON-serializable format
                value = state[key]

                # Handle Pydantic models
                if hasattr(value, 'model_dump'):
                    result[key] = value.model_dump()
                elif hasattr(value, 'dict'):  # Older Pydantic
                    result[key] = value.dict()
                # Handle LangChain messages
                elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                    try:
                        # Try to serialize list/dict
                        result[key] = value
                    except:
                        result[key] = str(value)
                # Handle primitives
                else:
                    result[key] = value

        return result

    def _print_execution_summary(self, result: Dict[str, Any]) -> None:
        """Print execution summary in verbose mode."""
        print(f"✓ Exact Match:     {'Yes' if result.get('sni_exact_results') else 'No'}")
        print(f"✓ Vector Search:   {'Yes' if result.get('sni_vector_results') else 'No'}")
        print(f"✓ Web Search:      {'Yes' if result.get('web_search_results') else 'No'}")
        print(f"✓ Content Crawled: {'Yes' if result.get('crawled_content') else 'No'}")


def create_sni_agent(
    qdrant_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    locale: str = "en-US",
) -> SNIAgent:
    """Create SNI Agent instance.

    Supports multiple LLM providers (Claude, OpenAI) via the LLM_PROVIDER
    configuration in .env file. When passing api_key/model parameters,
    ensure they match the configured provider.

    Args:
        qdrant_url: Qdrant server URL
        api_key: LLM API key (Claude or OpenAI, depending on LLM_PROVIDER)
        model: LLM model name (Claude or OpenAI model, depending on LLM_PROVIDER)
        locale: Language locale (e.g., en-US, zh-CN)

    Returns:
        Configured SNI Agent with LangGraph workflow
    """
    return SNIAgent(
        qdrant_url=qdrant_url,
        api_key=api_key,
        model=model,
        locale=locale,
    )

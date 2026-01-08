"""Compare context size between different queries."""

import asyncio
import logging
from src.graph.builder import create_sni_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_query(query: str):
    """Test a single query and return context size."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing: {query}")
    logger.info(f"{'='*80}\n")

    graph = create_sni_graph()

    initial_state = {
        "messages": [],
        "query": query,
        "sni_exact_results": None,
        "sni_vector_results": None,
        "web_search_results": None,
        "crawled_content": None,
        "final_answer": None,
        "locale": "en-US",
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
        result = await graph.ainvoke(initial_state)

        # Check what data was collected
        exact_count = len(result.get("sni_exact_results", []))
        vector_count = len(result.get("sni_vector_results", []))

        logger.info(f"\n{'='*80}")
        logger.info(f"Results for {query}:")
        logger.info(f"  - Exact matches: {exact_count}")
        logger.info(f"  - Vector matches: {vector_count}")
        logger.info(f"{'='*80}\n")

        return {
            "query": query,
            "exact_count": exact_count,
            "vector_count": vector_count,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error for {query}: {e}")
        return {
            "query": query,
            "error": str(e),
            "success": False
        }


async def main():
    """Compare www.bilibili.com vs api.bilibili.com."""

    queries = [
        "www.bilibili.com",
        "api.bilibili.com"
    ]

    results = []

    for query in queries:
        result = await test_query(query)
        results.append(result)

    # Print comparison
    logger.info(f"\n{'='*80}")
    logger.info("COMPARISON SUMMARY")
    logger.info(f"{'='*80}")

    for r in results:
        if r["success"]:
            logger.info(f"{r['query']}:")
            logger.info(f"  - Exact matches: {r['exact_count']}")
            logger.info(f"  - Vector matches: {r['vector_count']}")
        else:
            logger.info(f"{r['query']}: ERROR - {r.get('error', 'Unknown')}")

    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())

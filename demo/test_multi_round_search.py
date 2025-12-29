"""Test multi-round iterative search workflow."""

import asyncio
import logging
from src.graph.builder import create_sni_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_multi_round_search():
    """Test the multi-round iterative search workflow with 8 search rounds."""

    logger.info("=" * 80)
    logger.info("Testing Multi-Round Iterative Search Workflow")
    logger.info("=" * 80)

    test_query = "www.bilibili.com"

    logger.info(f"\nTest Query: {test_query}\n")

    graph = create_sni_graph()

    initial_state = {
        "messages": [],
        "query": test_query,
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
        "final_search_result": None
    }

    logger.info("Starting multi-round workflow execution...\n")

    result = await graph.ainvoke(initial_state)

    # Handle case where result is None or empty
    if result is None:
        logger.error("Workflow returned None - execution failed")
        return None

    logger.info("\n" + "=" * 80)
    logger.info("WORKFLOW EXECUTION RESULTS")
    logger.info("=" * 80)

    logger.info(f"\nOriginal Query: {result.get('query')}")

    if result.get('sni_exact_results'):
        exact_results = result.get('sni_exact_results')
        match_count = exact_results.get('match_count', 0) if isinstance(exact_results, dict) else 0
        logger.info(f"\n[1] Exact Match: Found {match_count} matches")
    else:
        logger.info(f"\n[1] Exact Match: No results (proceeding to multi-round search)")

    if result.get('sni_vector_results'):
        vector_results = result.get('sni_vector_results')
        logger.info(f"\n[2] Vector Search: {len(vector_results)} results")
        for i, r in enumerate(vector_results[:3], 1):
            logger.info(f"  {i}. SNI: {r.get('sni')}, Domain: {r.get('domain')}, Score: {r.get('score', 0):.3f}")

    if result.get('initial_search_result'):
        initial_result = str(result.get('initial_search_result'))
        logger.info(f"\n[3] Initial Web Search: Completed ({len(initial_result)} chars)")
        logger.info(f"  Preview: {initial_result[:200]}...")

    if result.get('round1_queries'):
        queries = result.get('round1_queries')
        logger.info(f"\n[4] Round 1 Planning: Generated {len(queries)} queries")
        for i, q in enumerate(queries, 1):
            logger.info(f"  {i}. {q}")

    if result.get('round1_results'):
        round1_results = result.get('round1_results')
        logger.info(f"\n[5] Round 1 Search: Completed {len(round1_results)}/4 searches")
        for i, r in enumerate(round1_results, 1):
            query = r.get('query', 'Unknown')
            success = r.get('success', False)
            logger.info(f"  {i}. {query}: {'Success' if success else 'Failed'}")

    if result.get('round2_keywords'):
        keywords = result.get('round2_keywords')
        logger.info(f"\n[6] Round 2 Planning: Extracted {len(keywords)} keywords")
        for i, kw in enumerate(keywords, 1):
            logger.info(f"  {i}. {kw}")

    if result.get('round2_results'):
        round2_results = result.get('round2_results')
        logger.info(f"\n[7] Round 2 Search: Completed {len(round2_results)}/2 searches")
        for i, r in enumerate(round2_results, 1):
            keyword = r.get('keyword', 'Unknown')
            success = r.get('success', False)
            logger.info(f"  {i}. {keyword}: {'Success' if success else 'Failed'}")

    if result.get('final_search_query'):
        final_query = result.get('final_search_query')
        logger.info(f"\n[8] Final Search Planning: {final_query}")

    if result.get('final_search_result'):
        final_result = str(result.get('final_search_result'))
        logger.info(f"\n[9] Final Search: Completed ({len(final_result)} chars)")
        logger.info(f"  Preview: {final_result[:200]}...")

    if result.get('final_answer'):
        final_answer = result.get('final_answer')
        logger.info(f"\n[10] Final Answer Synthesis:")
        logger.info(f"  {final_answer[:500]}...")

    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    success_criteria = []
    total_searches = 0

    if result.get('sni_vector_results'):
        success_criteria.append("Vector search completed")

    if result.get('initial_search_result'):
        success_criteria.append("Initial web search completed")
        total_searches += 1

    if result.get('round1_results'):
        count = len(result.get('round1_results'))
        success_criteria.append(f"Round 1: {count}/4 searches completed")
        total_searches += count

    if result.get('round2_results'):
        count = len(result.get('round2_results'))
        success_criteria.append(f"Round 2: {count}/2 searches completed")
        total_searches += count

    if result.get('final_search_result'):
        success_criteria.append("Final search completed")
        total_searches += 1

    if result.get('final_answer'):
        success_criteria.append("Final answer synthesized")

    logger.info(f"\nTotal Web Searches Executed: {total_searches}/8")
    logger.info(f"Success Criteria Met: {len(success_criteria)}/6")
    logger.info("\nCriteria:")
    for criterion in success_criteria:
        logger.info(f"  - {criterion}")

    logger.info("\n" + "=" * 80)
    logger.info("WORKFLOW PERFORMANCE")
    logger.info("=" * 80)

    logger.info(f"\nSearch Depth: {total_searches} rounds")

    # Safely access result fields with proper None checks
    # Use 'or []' to handle both missing keys and None values
    round1_queries = (result.get('round1_queries') or []) if result else []
    round2_keywords = (result.get('round2_keywords') or []) if result else []

    logger.info(f"Query Diversification: Round 1 used {len(round1_queries)} different angles")
    logger.info(f"Keyword Refinement: Round 2 focused on {len(round2_keywords)} core topics")
    logger.info(f"Comprehensive Coverage: {'Yes' if total_searches >= 7 else 'Partial'}")

    logger.info("\n" + "=" * 80)

    return result


if __name__ == "__main__":
    asyncio.run(test_multi_round_search())

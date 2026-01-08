"""State definition for SNI Agent workflow."""

from typing import TypedDict, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage


class SNIAgentState(TypedDict):
    """State for SNI Agent workflow.

    Attributes:
        messages: Conversation history
        query: User's original query
        sni_exact_results: Results from exact SNI search
        sni_vector_results: Results from vector similarity search
        extracted_keywords: Keywords extracted from vector search results
        enhanced_query: Enhanced query for web search
        web_search_results: Results from web search
        crawled_content: Content crawled from web pages
        final_answer: Final synthesized answer
        locale: Language locale (en-US, zh-CN, etc.)

        initial_search_result: Initial web search result (direct SNI search)
        round1_queries: Query list for round 1 (4 parallel searches)
        round1_results: Results from round 1 searches
        round2_keywords: Keywords extracted from round 1 results (2 keywords)
        round2_results: Results from round 2 searches
        final_search_query: Final comprehensive search query
        final_search_result: Result from final search
    """
    messages: List[BaseMessage]
    query: str
    sni_exact_results: Optional[List[Dict[str, Any]]]
    sni_vector_results: Optional[List[Dict[str, Any]]]
    extracted_keywords: Optional[List[str]]
    enhanced_query: Optional[str]
    web_search_results: Optional[Dict[str, Any]]
    crawled_content: Optional[str]
    final_answer: Optional[str]
    locale: str

    initial_search_result: Optional[str]
    round1_queries: Optional[List[str]]
    round1_results: Optional[List[Dict[str, Any]]]
    round2_keywords: Optional[List[str]]
    round2_results: Optional[List[Dict[str, Any]]]
    final_search_query: Optional[str]
    final_search_result: Optional[str]

    # TGT 标准化相关字段
    raw_answer: Optional[str]  # synthesize 节点生成的原始答案
    tgt_metadata: Optional[Dict[str, Any]]  # TGT 标准化元数据

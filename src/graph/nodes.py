"""Workflow nodes for SNI Agent."""

import logging
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from src.graph.state import SNIAgentState
from src.tools import SNITools
from src.prompts import get_prompt_template, apply_prompt_variables
from src.config import settings

logger = logging.getLogger(__name__)


class SNIWorkflowNodes:
    """Collection of workflow nodes for SNI Agent."""

    def __init__(
        self,
        tools_instance: SNITools,
        llm: BaseChatModel,
        locale: str = "en-US",
        enable_tgt_library: bool = True
    ):
        """Initialize workflow nodes.

        Args:
            tools_instance: SNI tools instance
            llm: Language model instance
            locale: Language locale
            enable_tgt_library: Enable TGT standard library integration
        """
        self.tools = tools_instance
        self.llm = llm
        self.locale = locale

        # Initialize TGT standard library
        if enable_tgt_library:
            try:
                from src.tools.tgt_library import TGTLibraryTools
                self.tgt_library = TGTLibraryTools(
                    qdrant_url=settings.QDRANT_URL,
                    collection_name=settings.QDRANT_TGT_COLLECTION,
                    embedding_model=settings.EMBEDDING_MODEL
                )
                logger.info("TGT standard library initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize TGT library: {e}")
                self.tgt_library = None
        else:
            self.tgt_library = None

    def sni_exact_query_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node 1: Query SNI database with exact match.

        Args:
            state: Current agent state

        Returns:
            Updated state with exact query results
        """
        query = state["query"]
        logger.info(f"[sni_exact_query_node] Querying exact match for: {query}")

        try:
            results = self.tools.search_sni_exact(query)
            logger.info(f"[sni_exact_query_node] Found {len(results) if results else 0} results")

            return {"sni_exact_results": results}
        except Exception as e:
            logger.error(f"[sni_exact_query_node] Error: {e}")
            return {"sni_exact_results": None}

    def sni_vector_query_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node 2: Query SNI database with vector similarity.

        Args:
            state: Current agent state

        Returns:
            Updated state with vector query results
        """
        query = state["query"]
        logger.info(f"[sni_vector_query_node] Querying vector similarity for: {query}")

        try:
            results = self.tools.search_sni_vector(query, top_k=5)
            logger.info(f"[sni_vector_query_node] Found {len(results) if results else 0} results")

            return {"sni_vector_results": results}
        except Exception as e:
            logger.error(f"[sni_vector_query_node] Error: {e}")
            return {"sni_vector_results": None}

    def keyword_extraction_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node 2.5: Extract keywords from vector results and initial web search using LLM.

        Args:
            state: Current agent state

        Returns:
            Updated state with extracted keywords and enhanced query
        """
        query = state["query"]
        vector_results = state.get("sni_vector_results")
        initial_search_result = state.get("initial_search_result")

        logger.info(f"[keyword_extraction_node] Extracting keywords from vector results and initial web search")

        if (not vector_results or len(vector_results) == 0) and not initial_search_result:
            logger.warning("[keyword_extraction_node] No data sources available")
            return {
                "extracted_keywords": [],
                "enhanced_query": query
            }

        try:
            if vector_results and len(vector_results) > 0:
                results_summary = "\n".join([
                    f"- SNI: {r.get('sni')}, Domain: {r.get('domain')}, Score: {r.get('score')}, Protocols: {r.get('protocols')}"
                    for r in vector_results[:5]
                ])
            else:
                results_summary = "No vector search results available"

            if initial_search_result:
                initial_summary = initial_search_result[:500] + "..." if len(initial_search_result) > 500 else initial_search_result
            else:
                initial_summary = "No initial search content available"

            extraction_prompt = apply_prompt_variables(
                "keyword_extraction",
                variables={
                    "query": query,
                    "results_summary": results_summary,
                    "initial_content": initial_summary
                },
                locale=state.get("locale", "en-US")
            )

            messages = [
                {"role": "user", "content": extraction_prompt}
            ]

            response = self.llm.invoke(messages)
            answer = response.content

            import json

            # Clean markdown code blocks if present
            cleaned_answer = answer.strip()
            if cleaned_answer.startswith("```"):
                lines = cleaned_answer.split("\n")
                # Remove first line if it's a markdown fence (```json or ```)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove last line if it's a closing fence
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_answer = "\n".join(lines)

            result = json.loads(cleaned_answer)

            keywords = result.get("keywords", [])
            enhanced_query = result.get("enhanced_query", query)
            reasoning = result.get("reasoning", "")

            logger.info(f"[keyword_extraction_node] Extracted keywords: {keywords}")
            logger.info(f"[keyword_extraction_node] Enhanced query: {enhanced_query}")
            logger.info(f"[keyword_extraction_node] Reasoning: {reasoning}")

            return {
                "extracted_keywords": keywords,
                "enhanced_query": enhanced_query
            }

        except Exception as e:
            logger.error(f"[keyword_extraction_node] Error: {e}")
            return {
                "extracted_keywords": [],
                "enhanced_query": query
            }

    def web_search_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node 3: Agent-driven web search with optional crawling.

        This node uses an Agent that can autonomously decide whether to:
        1. Perform web search
        2. Crawl specific URLs for deeper information

        The Agent (LLM) makes all tool-calling decisions autonomously.

        Args:
            state: Current agent state

        Returns:
            Updated state with web search results and optional crawled content
        """
        enhanced_query = state.get("enhanced_query")
        original_query = state["query"]
        search_query = enhanced_query if enhanced_query else original_query

        logger.info(f"[web_search_node] Starting Agent-driven research for: {search_query}")
        if enhanced_query and enhanced_query != original_query:
            logger.info(f"[web_search_node] Using enhanced query (original: {original_query})")

        try:
            from langchain.agents import create_agent
            from src.tools import get_web_search_tool, crawl_tool

            # Prepare tools for the agent
            web_search_tool = get_web_search_tool(max_search_results=settings.MAX_SEARCH_RESULTS)
            tools = [web_search_tool, crawl_tool]

            # Create agent with system prompt
            system_prompt = get_prompt_template("web_search_agent", locale=state.get("locale", "en-US"))

            # Create the agent (returns CompiledStateGraph)
            agent_graph = create_agent(
                model=self.llm,
                tools=tools,
                system_prompt=system_prompt
            )

            # Execute agent
            result = agent_graph.invoke({
                "messages": [("user", f"Research and gather information about: {search_query}")]
            })

            # Extract results from agent output
            messages = result.get("messages", [])
            final_message = messages[-1] if messages else None
            output = final_message.content if final_message else ""

            # Try to extract tool calls and responses from messages
            web_results = None
            crawled_content = None

            # Debug: log message types
            logger.debug(f"[web_search_node] Total messages: {len(messages)}")

            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                logger.debug(f"[web_search_node] Message {i}: {msg_type}")

                # Check for ToolMessage (tool responses)
                if msg_type == "ToolMessage":
                    tool_name = getattr(msg, 'name', '')
                    content = getattr(msg, 'content', '')
                    logger.info(f"[web_search_node] Found tool response: {tool_name}")

                    if tool_name == 'web_search':
                        web_results = content
                    elif tool_name == 'crawl_tool':
                        crawled_content = content

                # Also check AIMessage with tool_calls
                elif msg_type == "AIMessage" and hasattr(msg, 'tool_calls'):
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get('name', '')
                        logger.info(f"[web_search_node] Agent called tool: {tool_name}")

            logger.info(f"[web_search_node] Agent completed research")
            logger.info(f"[web_search_node] Web search used: {web_results is not None}")
            logger.info(f"[web_search_node] Crawling used: {crawled_content is not None}")

            return {
                "web_search_results": web_results or output,
                "crawled_content": crawled_content
            }

        except Exception as e:
            logger.error(f"[web_search_node] Error: {e}", exc_info=True)
            return {
                "web_search_results": None,
                "crawled_content": None
            }

    def synthesize_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node: Synthesize final answer using LLM.

        Integrates all search results from multi-round search workflow:
        - SNI exact results
        - SNI vector results
        - Initial search
        - Round 1 (4 searches)
        - Round 2 (2 searches)
        - Final search

        Args:
            state: Current agent state

        Returns:
            Updated state with final answer
        """
        logger.info(f"[synthesize_node] Synthesizing final answer from all sources")

        try:
            MAX_CONTEXT_CHARS = 15000
            context_parts = []

            if state.get("sni_exact_results"):
                exact_str = str(state['sni_exact_results'])[:500]
                context_parts.append(f"**SNI Exact Match Results:**\n{exact_str}")

            vector_results = state.get("sni_vector_results") or []
            if vector_results:
                vector_summary = "\n".join([
                    f"  - SNI: {r.get('sni')}, Domain: {r.get('domain')}, Score: {r.get('score', 0):.2f}"
                    for r in vector_results[:3]
                ])
                context_parts.append(f"**SNI Vector Search Results:**\n{vector_summary}")

            if state.get("initial_search_result"):
                initial_preview = str(state['initial_search_result'])[:800]
                context_parts.append(f"**Initial Web Search:**\n{initial_preview}")

            round1_results = state.get("round1_results") or []
            if round1_results:
                round1_summary = "\n".join([
                    f"  - Query: {r.get('query')[:80]}\n    Result: {str(r.get('result', ''))[:400]}"
                    for r in round1_results[:4]
                ])
                context_parts.append(f"**Round 1 Searches (4 queries):**\n{round1_summary}")

            round2_results = state.get("round2_results") or []
            if round2_results:
                round2_summary = "\n".join([
                    f"  - Keyword: {r.get('keyword')}\n    Result: {str(r.get('result', ''))[:400]}"
                    for r in round2_results[:2]
                ])
                context_parts.append(f"**Round 2 Searches (2 keywords):**\n{round2_summary}")

            if state.get("final_search_result"):
                final_preview = str(state['final_search_result'])[:1500]
                context_parts.append(f"**Final Comprehensive Search:**\n{final_preview}")

            context = "\n\n".join(context_parts)

            if len(context) > MAX_CONTEXT_CHARS:
                logger.warning(f"[synthesize_node] Context too large ({len(context)} chars), truncating to {MAX_CONTEXT_CHARS}")
                context = context[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated due to size limit]"

            logger.info(f"[synthesize_node] Context size: {len(context)} chars")

            system_prompt = get_prompt_template("sni_agent", locale=state.get("locale", "en-US"))

            synthesis_prompt = apply_prompt_variables(
                "synthesis",
                variables={
                    "query": state['query'],
                    "context": context
                },
                locale=state.get("locale", "en-US")
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": synthesis_prompt}
            ]

            response = self.llm.invoke(messages)
            answer = response.content

            if answer is None:
                logger.error("[synthesize_node] LLM returned None content")
                error_answer = '{"tgt": "Error", "Explanation": "LLM returned None", "Query Results": "No content"}'
                return {"final_answer": error_answer}

            logger.info(f"[synthesize_node] Generated comprehensive answer from {len(context_parts)} sources")

            # TGT standardization flow
            if self.tgt_library:
                answer = self._standardize_tgt(answer, state)

            return {"final_answer": answer}

        except Exception as e:
            import traceback
            logger.error(f"[synthesize_node] Error: {e}")
            logger.error(f"[synthesize_node] Traceback:\n{traceback.format_exc()}")
            error_answer = '{"tgt": "Error", "Explanation": "An error occurred during synthesis", "Query Results": "' + str(e) + '"}'
            return {"final_answer": error_answer}

    async def initial_web_search_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node: Crawl homepage directly for SNI domain.

        Directly crawls the SNI domain homepage to extract service information.

        Args:
            state: Current agent state

        Returns:
            Updated state with crawled homepage content
        """
        sni = state["query"]
        logger.info(f"[initial_web_search_node] Crawling homepage for: {sni}")

        try:
            from src.tools.crawler import Crawler

            crawler = Crawler()

            url_https = f"https://{sni}"
            url_http = f"http://{sni}"

            result = None
            error_msg = None

            try:
                logger.info(f"[initial_web_search_node] Trying HTTPS: {url_https}")
                article = crawler.crawl(url_https)
                markdown_content = article.to_markdown()

                if markdown_content and markdown_content.strip():
                    result = markdown_content[:10000]
                    logger.info(f"[initial_web_search_node] Successfully crawled via HTTPS ({len(result)} chars, title: '{article.title}')")
                else:
                    logger.warning(f"[initial_web_search_node] HTTPS returned empty content")
                    error_msg = "HTTPS returned empty content"

            except Exception as e:
                logger.warning(f"[initial_web_search_node] HTTPS failed: {e}")
                error_msg = f"HTTPS failed: {str(e)}"

            if not result:
                try:
                    logger.info(f"[initial_web_search_node] Trying HTTP: {url_http}")
                    article = crawler.crawl(url_http)
                    markdown_content = article.to_markdown()

                    if markdown_content and markdown_content.strip():
                        result = markdown_content[:10000]
                        logger.info(f"[initial_web_search_node] Successfully crawled via HTTP ({len(result)} chars, title: '{article.title}')")
                    else:
                        logger.warning(f"[initial_web_search_node] HTTP returned empty content")
                        error_msg += " | HTTP returned empty content"

                except Exception as e:
                    logger.warning(f"[initial_web_search_node] HTTP failed: {e}")
                    error_msg += f" | HTTP failed: {str(e)}"

            if result:
                return {"initial_search_result": result}
            else:
                logger.error(f"[initial_web_search_node] Both HTTPS and HTTP failed: {error_msg}")
                return {"initial_search_result": f"Failed to crawl homepage: {error_msg}"}

        except Exception as e:
            logger.error(f"[initial_web_search_node] Error: {e}", exc_info=True)
            return {"initial_search_result": f"Crawler error: {str(e)}"}

    def round1_planning_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node: Generate 4 diverse search queries for round 1.

        Based on extracted keywords from previous steps, generates 4 queries
        exploring different aspects (technical, service info, infrastructure, security).

        Args:
            state: Current agent state

        Returns:
            Updated state with round1_queries
        """
        query = state["query"]
        extracted_keywords = state.get("extracted_keywords", [])

        logger.info(f"[round1_planning_node] Generating round 1 queries for: {query}")
        logger.info(f"[round1_planning_node] Using extracted keywords: {extracted_keywords}")

        if not extracted_keywords or len(extracted_keywords) == 0:
            logger.warning("[round1_planning_node] No extracted keywords, using fallback queries")
            # Use only the query itself without adding descriptive words
            return {
                "round1_queries": [
                    query,
                    query,
                    query,
                    query
                ]
            }

        try:
            keywords_str = ", ".join(extracted_keywords)

            planning_prompt = apply_prompt_variables(
                "round1_planning",
                variables={
                    "query": query,
                    "keywords": keywords_str
                },
                locale=state.get("locale", "en-US")
            )

            messages = [
                {"role": "user", "content": planning_prompt}
            ]

            response = self.llm.invoke(messages)
            answer = response.content

            import json

            cleaned_answer = answer.strip()
            if cleaned_answer.startswith("```"):
                lines = cleaned_answer.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_answer = "\n".join(lines)

            result = json.loads(cleaned_answer)

            queries = result.get("queries", [])
            reasoning = result.get("reasoning", "")

            if len(queries) < 4:
                logger.warning(f"[round1_planning_node] Only got {len(queries)} queries, padding with fallback")
                while len(queries) < 4:
                    queries.append(f"{query} additional search {len(queries)}")

            logger.info(f"[round1_planning_node] Generated queries: {queries}")
            logger.info(f"[round1_planning_node] Reasoning: {reasoning}")

            return {"round1_queries": queries[:4]}

        except Exception as e:
            logger.error(f"[round1_planning_node] Error: {e}")
            return {
                "round1_queries": [
                    f"{query} technical details",
                    f"{query} service information",
                    f"{query} infrastructure",
                    f"{query} security"
                ]
            }

    async def round1_parallel_search_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node: Execute 4 parallel web searches for round 1 queries.

        Uses asyncio.gather with concurrency control.

        Args:
            state: Current agent state

        Returns:
            Updated state with round1_results
        """
        import asyncio
        queries = state.get("round1_queries", [])

        if not queries:
            logger.warning("[round1_parallel_search_node] No queries to execute")
            return {"round1_results": []}

        logger.info(f"[round1_parallel_search_node] Executing {len(queries)} parallel searches")

        try:
            from src.tools import get_web_search_tool

            web_search_tool = get_web_search_tool(max_search_results=settings.MAX_SEARCH_RESULTS)

            semaphore = asyncio.Semaphore(4)

            async def search_with_limit(query: str) -> Dict:
                async with semaphore:
                    try:
                        logger.info(f"[round1_parallel_search_node] Searching: {query}")
                        result = await web_search_tool.ainvoke(query)
                        return {"query": query, "result": result, "success": True}
                    except Exception as e:
                        logger.error(f"[round1_parallel_search_node] Search failed for '{query}': {e}")
                        return {"query": query, "error": str(e), "success": False}

            results = await asyncio.gather(*[search_with_limit(q) for q in queries])

            successful_results = [r for r in results if r.get("success")]

            logger.info(f"[round1_parallel_search_node] Completed {len(successful_results)}/{len(queries)} searches")

            return {"round1_results": successful_results}

        except Exception as e:
            logger.error(f"[round1_parallel_search_node] Error: {e}", exc_info=True)
            return {"round1_results": []}

    def round2_planning_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node: Extract organization from round 1 results and generate 2 precise queries.

        Args:
            state: Current agent state

        Returns:
            Updated state with round2_keywords
        """
        round1_results = state.get("round1_results", [])
        query = state["query"]

        logger.info(f"[round2_planning_node] Generating Round2 queries from {len(round1_results)} Round1 results")

        if not round1_results:
            logger.warning("[round2_planning_node] No round1 results, using query as fallback")
            return {"round2_keywords": [query, query]}

        try:
            results_summary = "\n\n".join([
                f"Query: {r.get('query')}\nResult Preview: {str(r.get('result', ''))[:500]}..."
                for r in round1_results[:4]
            ])

            planning_prompt = apply_prompt_variables(
                "round2_planning",
                variables={
                    "query": query,  # Pass full SNI so LLM can see the prefix
                    "results_summary": results_summary
                },
                locale=state.get("locale", "en-US")
            )

            messages = [
                {"role": "user", "content": planning_prompt}
            ]

            response = self.llm.invoke(messages)
            answer = response.content

            import json

            cleaned_answer = answer.strip()
            if cleaned_answer.startswith("```"):
                lines = cleaned_answer.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_answer = "\n".join(lines)

            result = json.loads(cleaned_answer)

            queries = result.get("queries", [])
            organization = result.get("organization", "")
            reasoning = result.get("reasoning", "")

            if len(queries) < 2:
                logger.warning(f"[round2_planning_node] Only got {len(queries)} queries, using fallback")
                queries = [query, query]

            logger.info(f"[round2_planning_node] Discovered organization: {organization}")
            logger.info(f"[round2_planning_node] Generated queries: {queries}")
            logger.info(f"[round2_planning_node] Reasoning: {reasoning}")

            return {"round2_keywords": queries[:2]}

        except Exception as e:
            logger.error(f"[round2_planning_node] Error: {e}")
            return {"round2_keywords": [query, query]}

    async def round2_parallel_search_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node: Execute 2 parallel web searches for round 2 keywords.

        Args:
            state: Current agent state

        Returns:
            Updated state with round2_results
        """
        import asyncio
        keywords = state.get("round2_keywords", [])

        if not keywords:
            logger.warning("[round2_parallel_search_node] No keywords to search")
            return {"round2_results": []}

        logger.info(f"[round2_parallel_search_node] Executing {len(keywords)} parallel searches")

        try:
            from src.tools import get_web_search_tool

            web_search_tool = get_web_search_tool(max_search_results=settings.MAX_SEARCH_RESULTS)

            async def search_keyword(keyword: str) -> Dict:
                try:
                    logger.info(f"[round2_parallel_search_node] Searching: {keyword}")
                    result = await web_search_tool.ainvoke(keyword)
                    return {"keyword": keyword, "result": result, "success": True}
                except Exception as e:
                    logger.error(f"[round2_parallel_search_node] Search failed for '{keyword}': {e}")
                    return {"keyword": keyword, "error": str(e), "success": False}

            results = await asyncio.gather(*[search_keyword(k) for k in keywords])

            successful_results = [r for r in results if r.get("success")]

            logger.info(f"[round2_parallel_search_node] Completed {len(successful_results)}/{len(keywords)} searches")

            return {"round2_results": successful_results}

        except Exception as e:
            logger.error(f"[round2_parallel_search_node] Error: {e}", exc_info=True)
            return {"round2_results": []}

    def final_search_planning_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node: Generate final verification search query.

        Uses Round 2 keywords + original query to create a verification search.

        Args:
            state: Current agent state

        Returns:
            Updated state with final_search_query
        """
        query = state["query"]
        round2_keywords = state.get("round2_keywords", [])

        logger.info(f"[final_search_planning_node] Generating final verification query")
        logger.info(f"[final_search_planning_node] Using Round 2 keywords: {round2_keywords}")

        # If no Round 2 keywords, use query itself
        if not round2_keywords or len(round2_keywords) == 0:
            logger.warning("[final_search_planning_node] No Round 2 keywords, using query as fallback")
            return {"final_search_query": query}

        try:
            keywords_str = ", ".join(round2_keywords)

            planning_prompt = apply_prompt_variables(
                "final_search_planning",
                variables={
                    "query": query,
                    "round2_keywords": keywords_str
                },
                locale=state.get("locale", "en-US")
            )

            messages = [
                {"role": "user", "content": planning_prompt}
            ]

            response = self.llm.invoke(messages)
            answer = response.content

            import json

            if answer is None:
                logger.error("[final_search_planning_node] LLM returned None content")
                return {"final_search_query": query}

            cleaned_answer = answer.strip()
            if cleaned_answer.startswith("```"):
                lines = cleaned_answer.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_answer = "\n".join(lines)

            result = json.loads(cleaned_answer)

            final_query = result.get("final_query", "")
            reasoning = result.get("reasoning", "")

            if not final_query:
                logger.warning("[final_search_planning_node] No final query generated, using fallback")
                final_query = f"{query} {keywords_str}"

            logger.info(f"[final_search_planning_node] Final query: {final_query}")
            logger.info(f"[final_search_planning_node] Reasoning: {reasoning}")

            return {"final_search_query": final_query}

        except Exception as e:
            logger.error(f"[final_search_planning_node] Error: {e}")
            # Fallback: combine query with keywords
            if round2_keywords:
                fallback_query = f"{query} {' '.join(round2_keywords)}"
            else:
                fallback_query = query
            return {"final_search_query": fallback_query}

    async def final_search_node(self, state: SNIAgentState) -> Dict[str, Any]:
        """Node: Execute final comprehensive search.

        Args:
            state: Current agent state

        Returns:
            Updated state with final_search_result
        """
        final_query = state.get("final_search_query")

        if not final_query:
            logger.warning("[final_search_node] No final query, skipping")
            return {"final_search_result": None}

        logger.info(f"[final_search_node] Executing final search: {final_query}")

        try:
            from src.tools import get_web_search_tool

            web_search_tool = get_web_search_tool(max_search_results=settings.MAX_SEARCH_RESULTS)
            result = await web_search_tool.ainvoke(final_query)

            logger.info(f"[final_search_node] Final search completed")

            return {"final_search_result": result}

        except Exception as e:
            logger.error(f"[final_search_node] Error: {e}")
            return {"final_search_result": None}

    def _standardize_tgt(self, answer: str, state: SNIAgentState) -> str:
        """Standardize TGT using standard library.

        Args:
            answer: Raw LLM answer (JSON string)
            state: Current agent state

        Returns:
            Standardized answer (JSON string)
        """
        try:
            import json

            # Parse LLM response
            tgt_data = json.loads(answer)
            raw_tgt = tgt_data.get("tgt", "Unknown")

            # Skip if no valid tgt
            if raw_tgt in ["Unknown", "Error", ""]:
                logger.info(f"[TGT] No valid tgt to standardize: {raw_tgt}")
                return answer

            logger.info(f"[TGT] Starting standardization for: {raw_tgt}")

            # Step 1: Exact match
            exact_match = self.tgt_library.search_exact(raw_tgt)
            if exact_match:
                logger.info(f"[TGT] Exact match found: {exact_match['standard_name']}")
                tgt_data["tgt"] = exact_match["standard_name"]
                tgt_data["_tgt_metadata"] = {
                    "matched_entity_id": exact_match["id"],
                    "match_type": "exact",
                    "original_tgt": raw_tgt
                }
                return json.dumps(tgt_data, ensure_ascii=False)

            # Step 2: Vector search for similar entities
            vector_results = self.tgt_library.search_vector(
                raw_tgt,
                top_k=3,
                threshold=settings.TGT_VECTOR_THRESHOLD
            )

            if vector_results:
                logger.info(f"[TGT] Found {len(vector_results)} similar entities via vector search")

                # Step 3: LLM judgment
                llm_decision = self._check_tgt_similarity(
                    raw_tgt,
                    tgt_data.get("Explanation", ""),
                    vector_results
                )

                if llm_decision["match_found"] and llm_decision["confidence"] > settings.TGT_LLM_CONFIDENCE_THRESHOLD:
                    matched_entity = llm_decision["matched_standard_name"]
                    logger.info(f"[TGT] LLM matched to entity: {matched_entity} (confidence: {llm_decision['confidence']:.2f})")

                    # Step 4: Update alias if needed
                    if llm_decision["is_alias"] and llm_decision["suggested_alias"]:
                        success = self.tgt_library.add_alias(
                            matched_entity,
                            llm_decision["suggested_alias"]
                        )
                        if success:
                            logger.info(f"[TGT] Added alias: '{llm_decision['suggested_alias']}' → '{matched_entity}'")

                    tgt_data["tgt"] = matched_entity
                    tgt_data["_tgt_metadata"] = {
                        "matched_entity": matched_entity,
                        "match_type": "vector_llm",
                        "confidence": llm_decision["confidence"],
                        "original_tgt": raw_tgt,
                        "reasoning": llm_decision["reasoning"]
                    }
                    return json.dumps(tgt_data, ensure_ascii=False)

            # Step 5: Check specificity before creating new entity
            specificity_check = self.tgt_library.check_specificity(raw_tgt, self.llm)

            if not specificity_check["is_specific"]:
                logger.warning(f"[TGT] Rejected generic entity: {raw_tgt} - {specificity_check['reason']}")
                tgt_data["_tgt_metadata"] = {
                    "match_type": "rejected",
                    "reason": "too_generic",
                    "details": specificity_check["reason"],
                    "suggestion": specificity_check["suggested_refinement"]
                }
                return json.dumps(tgt_data, ensure_ascii=False)

            # Step 6: Create new entity
            try:
                new_entity_id = self.tgt_library.create_entity({
                    "standard_name": raw_tgt,
                    "full_name": raw_tgt,
                    "aliases": [],
                    "category": self._extract_category(tgt_data),
                    "description": tgt_data.get("Explanation", ""),
                    "verification_status": "auto_generated",
                })

                logger.info(f"[TGT] Created new entity: {raw_tgt} (ID: {new_entity_id})")
                tgt_data["_tgt_metadata"] = {
                    "matched_entity_id": new_entity_id,
                    "match_type": "new_entity",
                    "confidence": specificity_check["confidence"]
                }
            except Exception as e:
                logger.error(f"[TGT] Failed to create entity: {e}")
                tgt_data["_tgt_metadata"] = {
                    "match_type": "error",
                    "error": str(e)
                }

            return json.dumps(tgt_data, ensure_ascii=False)

        except json.JSONDecodeError as e:
            logger.error(f"[TGT] Failed to parse answer as JSON: {e}")
            return answer
        except Exception as e:
            logger.error(f"[TGT] Standardization error: {e}")
            return answer

    def _check_tgt_similarity(
        self,
        new_tgt: str,
        explanation: str,
        candidates: List[Dict]
    ) -> Dict:
        """Use LLM to check if new tgt belongs to any candidate entity.

        Args:
            new_tgt: New TGT name
            explanation: Explanation from synthesis
            candidates: Candidate entities from vector search

        Returns:
            Dict with match_found, matched_standard_name, is_alias,
            suggested_alias, confidence, reasoning
        """
        try:
            prompt = apply_prompt_variables(
                "tgt_similarity_check",
                variables={
                    "new_tgt": new_tgt,
                    "new_explanation": explanation,
                    "candidates": candidates
                },
                locale=self.locale
            )

            response = self.llm.invoke([{"role": "user", "content": prompt}])
            result = self._parse_json_response(response.content)

            return {
                "match_found": result.get("match_found", False),
                "matched_standard_name": result.get("matched_standard_name"),
                "is_alias": result.get("is_alias", False),
                "suggested_alias": result.get("suggested_alias"),
                "confidence": result.get("confidence", 0.0),
                "reasoning": result.get("reasoning", "")
            }

        except Exception as e:
            logger.error(f"[TGT] Error in similarity check: {e}")
            return {
                "match_found": False,
                "matched_standard_name": None,
                "is_alias": False,
                "suggested_alias": None,
                "confidence": 0.0,
                "reasoning": f"Error: {e}"
            }

    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON from LLM response, handling markdown code blocks.

        Args:
            content: Raw LLM response

        Returns:
            Parsed JSON dict
        """
        import json

        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()
        return json.loads(content)

    def _extract_category(self, tgt_data: Dict) -> str:
        """Extract entity category from TGT data.

        Args:
            tgt_data: TGT data dict

        Returns:
            Category string
        """
        explanation = tgt_data.get("Explanation", "").lower()

        # Simple rule-based category extraction
        if "云服务" in explanation or "cloud" in explanation:
            return "云服务提供商"
        elif "导航" in explanation or "定位" in explanation or "navigation" in explanation:
            return "导航定位服务"
        elif "社交" in explanation or "social" in explanation:
            return "社交平台"
        elif "视频" in explanation or "video" in explanation:
            return "视频平台"
        elif "音乐" in explanation or "music" in explanation:
            return "音乐服务"
        elif "支付" in explanation or "payment" in explanation:
            return "支付服务"
        elif "cdn" in explanation:
            return "CDN服务"
        else:
            return "其他"


# Decision functions (these are pure Python, no LLM involved!)

def should_try_vector_search(state: SNIAgentState) -> str:
    """Decision: Should we try vector search?

    This is a PYTHON function, not LLM decision!
    100% deterministic and reliable.

    Args:
        state: Current agent state

    Returns:
        Next node name
    """
    exact_results = state.get("sni_exact_results")

    if exact_results and exact_results.get("found") and exact_results.get("match_count", 0) > 0:
        logger.info(f"[Decision] Exact results found ({exact_results.get('match_count')} matches) → skip to synthesize")
        return "synthesize"
    else:
        logger.info("[Decision] No exact results → try vector search")
        return "vector_search"


def should_web_search(state: SNIAgentState) -> str:
    """Decision: Should we search the web?

    Modified behavior: Always proceed to web search after vector search.
    Vector search results are kept as supplementary information for synthesis,
    but do not affect the decision to search the web.

    Args:
        state: Current agent state

    Returns:
        Next node name (always "web_search")
    """
    vector_results = state.get("sni_vector_results")

    if vector_results and len(vector_results) > 0:
        top_score = vector_results[0].get("score", 0) if isinstance(vector_results[0], dict) else 0
        logger.info(f"[Decision] Vector search completed (top score: {top_score:.2f}) → proceed to web search")
    else:
        logger.info("[Decision] No vector results → proceed to web search")

    return "web_search"

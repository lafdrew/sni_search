"""Workflow nodes for SNI Agent."""

import logging
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from src.graph.state import SNIAgentState
from src.tools import SNITools
from src.prompts import get_prompt_template
from src.config import settings

logger = logging.getLogger(__name__)


class SNIWorkflowNodes:
    """Collection of workflow nodes for SNI Agent."""

    def __init__(
        self,
        tools_instance: SNITools,
        llm: BaseChatModel,
        locale: str = "en-US"
    ):
        """Initialize workflow nodes.

        Args:
            tools_instance: SNI tools instance
            llm: Language model instance
            locale: Language locale
        """
        self.tools = tools_instance
        self.llm = llm
        self.locale = locale

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
        """Node 2.5: Extract keywords from vector results using LLM.

        Args:
            state: Current agent state

        Returns:
            Updated state with extracted keywords and enhanced query
        """
        query = state["query"]
        vector_results = state.get("sni_vector_results")

        logger.info(f"[keyword_extraction_node] Analyzing vector results for keyword extraction")

        if not vector_results or len(vector_results) == 0:
            logger.warning("[keyword_extraction_node] No vector results to analyze")
            return {
                "extracted_keywords": [],
                "enhanced_query": query
            }

        try:
            results_summary = "\n".join([
                f"- SNI: {r.get('sni')}, Domain: {r.get('domain')}, Score: {r.get('score')}, Protocols: {r.get('protocols')}"
                for r in vector_results[:5]
            ])

            extraction_prompt = f"""Based on the vector search results below, extract meaningful keywords that could help improve web search for the user's query.

User Query: {query}

Vector Search Results:
{results_summary}

Your task:
1. Identify the most relevant keywords from domains, SNI names, and protocols
2. Extract 3-5 keywords that would help find more information on the web
3. Generate an enhanced search query by combining the original query with selected keywords

Respond in JSON format:
{{
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "enhanced_query": "enhanced search query string",
    "reasoning": "brief explanation of your selection"
}}

Output valid JSON without markdown code blocks."""

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
            system_prompt = """You are a research assistant helping to gather information about an SNI (Server Name Indication).

Your task:
1. Use web_search to find information about the query
2. Analyze the search results carefully
3. If you find an official website, authoritative documentation, or highly relevant source, use crawl_tool to get detailed content
4. Only crawl if the source is trustworthy and would provide significantly more value than search snippets

Guidelines for crawling:
- Crawl official websites, documentation pages, or authoritative sources
- Do NOT crawl if search snippets already provide sufficient information
- Do NOT crawl untrusted or irrelevant sources
- Crawl at most ONE page to keep response time reasonable

Return your findings in a concise summary."""

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

            synthesis_prompt = f"""Based on comprehensive information from multiple search rounds, identify what service this SNI represents.

Original Query (SNI): {state['query']}

All Available Information:
{context}

Your task: Determine what service/application this SNI represents.

Provide a JSON response with these fields:
- "tgt": Name and type of the service (identify specifically: what service/product is this?)
- "Explanation": Clear explanation of what the service does, who operates/owns it, and what it's used for
- "Query Results": Summary of key findings that helped identify the service (include company name, service category, primary function)

Focus on answering:
1. What service is this SNI used for?
2. Who operates this service?
3. What do users access through this domain?

Prioritize information from:
1. Official sources and company documentation
2. Frequently appearing service/company names across searches
3. Authoritative technical documentation
4. Verified service descriptions

Output valid JSON without markdown code blocks."""

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

        Based on vector search results and original SNI, generates 4 queries
        exploring different aspects (technical, service info, infrastructure, security).

        Args:
            state: Current agent state

        Returns:
            Updated state with round1_queries
        """
        query = state["query"]
        vector_results = state.get("sni_vector_results")

        logger.info(f"[round1_planning_node] Generating round 1 queries for: {query}")

        if not vector_results or len(vector_results) == 0:
            logger.warning("[round1_planning_node] No vector results, using fallback queries")
            return {
                "round1_queries": [
                    f"{query} technical details",
                    f"{query} service information",
                    f"{query} infrastructure",
                    f"{query} security"
                ]
            }

        try:
            results_summary = "\n".join([
                f"- SNI: {r.get('sni')}, Domain: {r.get('domain')}, Score: {r.get('score')}, Protocols: {r.get('protocols')}"
                for r in vector_results[:5]
            ])

            planning_prompt = f"""Based on the vector search results below, generate 4 diverse search queries to identify what service this SNI represents.

User Query (SNI): {query}

Vector Search Results:
{results_summary}

Generate 4 queries covering:
1. Service identification (what service/application uses this domain, company/organization behind it)
2. Technical infrastructure (protocols, certificates, CDN, hosting details that reveal service purpose)
3. Related domains and ecosystem (associated domains that indicate service category)
4. Usage and purpose (what users access through this domain, typical use cases)

All queries should focus on answering: "What service does this SNI represent?"

Respond in JSON format:
{{
    "queries": ["query1", "query2", "query3", "query4"],
    "reasoning": "brief explanation of query strategy"
}}

Output valid JSON without markdown code blocks."""

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
        """Node: Extract 2 most important keywords from round 1 results.

        Args:
            state: Current agent state

        Returns:
            Updated state with round2_keywords
        """
        round1_results = state.get("round1_results", [])

        logger.info(f"[round2_planning_node] Extracting keywords from {len(round1_results)} results")

        if not round1_results:
            logger.warning("[round2_planning_node] No round1 results, using query as fallback")
            query = state["query"]
            return {"round2_keywords": [query, f"{query} service"]}

        try:
            results_summary = "\n\n".join([
                f"Query: {r.get('query')}\nResult Preview: {str(r.get('result', ''))[:500]}..."
                for r in round1_results[:4]
            ])

            planning_prompt = f"""Analyze the following 4 search results and extract the 2 MOST IMPORTANT keywords for identifying what service this SNI represents.

Search Results:
{results_summary}

Choose keywords that:
1. Help identify the service/application (company name, product name, service type)
2. Appear frequently across multiple results and are central to service identification
3. Would lead to finding official documentation or authoritative sources about the service

Focus on: What service is this? Who operates it? What is it used for?

Respond in JSON format:
{{
    "keywords": ["keyword1", "keyword2"],
    "reasoning": "why these keywords identify the service"
}}

Output valid JSON without markdown code blocks."""

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

            keywords = result.get("keywords", [])
            reasoning = result.get("reasoning", "")

            if len(keywords) < 2:
                logger.warning(f"[round2_planning_node] Only got {len(keywords)} keywords, using fallback")
                query = state["query"]
                keywords = [query, f"{query} documentation"]

            logger.info(f"[round2_planning_node] Extracted keywords: {keywords}")
            logger.info(f"[round2_planning_node] Reasoning: {reasoning}")

            return {"round2_keywords": keywords[:2]}

        except Exception as e:
            logger.error(f"[round2_planning_node] Error: {e}")
            query = state["query"]
            return {"round2_keywords": [query, f"{query} documentation"]}

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
        """Node: Generate final comprehensive search query.

        Synthesizes all previous search results into one ultimate query.

        Args:
            state: Current agent state

        Returns:
            Updated state with final_search_query
        """
        query = state["query"]
        initial_result = state.get("initial_search_result")
        round1_results = state.get("round1_results") or []
        round2_results = state.get("round2_results") or []

        logger.info(f"[final_search_planning_node] Generating final search query")

        try:
            MAX_CONTEXT_CHARS = 8000
            context_parts = []

            if initial_result:
                context_parts.append(f"Initial Search: {str(initial_result)[:500]}")

            if round1_results:
                round1_summary = "\n".join([
                    f"- {r.get('query', '')[:60]}: {str(r.get('result', ''))[:300]}"
                    for r in round1_results[:4]
                ])
                context_parts.append(f"Round 1 Results:\n{round1_summary}")

            if round2_results:
                round2_summary = "\n".join([
                    f"- {r.get('keyword')}: {str(r.get('result', ''))[:300]}"
                    for r in round2_results[:2]
                ])
                context_parts.append(f"Round 2 Results:\n{round2_summary}")

            context = "\n\n".join(context_parts)

            if len(context) > MAX_CONTEXT_CHARS:
                logger.warning(f"[final_search_planning_node] Context too large ({len(context)} chars), truncating")
                context = context[:MAX_CONTEXT_CHARS] + "\n[Context truncated]"

            logger.info(f"[final_search_planning_node] Context size: {len(context)} chars")

            planning_prompt = f"""Based on ALL the search results below, generate ONE final comprehensive search query to definitively identify what service this SNI represents.

Original SNI Query: {query}

All Search Results:
{context}

The final query should:
1. Focus on identifying the service: What is it? Who operates it? What is its purpose?
2. Incorporate key findings (company/service names, product identifiers) from all search rounds
3. Target official documentation, company websites, or authoritative service descriptions
4. Be specific enough to find definitive service identification

Goal: Find authoritative information that clearly explains what service this SNI provides.

Respond in JSON format:
{{
    "final_query": "comprehensive search query for service identification",
    "reasoning": "how this query will identify the service"
}}

Output valid JSON without markdown code blocks."""

            messages = [
                {"role": "user", "content": planning_prompt}
            ]

            response = self.llm.invoke(messages)
            answer = response.content

            import json
            import traceback

            if answer is None:
                logger.error("[final_search_planning_node] LLM returned None content")
                return {"final_search_query": f"{query} official documentation"}

            cleaned_answer = answer.strip()
            if cleaned_answer.startswith("```"):
                lines = cleaned_answer.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_answer = "\n".join(lines)

            try:
                result = json.loads(cleaned_answer)
            except json.JSONDecodeError as je:
                logger.error(f"[final_search_planning_node] JSON decode error: {je}")
                logger.error(f"[final_search_planning_node] Raw answer: {answer}")
                return {"final_search_query": f"{query} official documentation"}

            final_query = result.get("final_query", query)
            reasoning = result.get("reasoning", "")

            logger.info(f"[final_search_planning_node] Final query: {final_query}")
            logger.info(f"[final_search_planning_node] Reasoning: {reasoning}")

            return {"final_search_query": final_query}

        except Exception as e:
            import traceback
            logger.error(f"[final_search_planning_node] Error: {e}")
            logger.error(f"[final_search_planning_node] Traceback:\n{traceback.format_exc()}")
            return {"final_search_query": f"{query} official documentation"}

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
            logger.error(f"[final_search_node] Error: {e}", exc_info=True)
            return {"final_search_result": None}


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

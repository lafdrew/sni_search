"""LangGraph nodes for SNI RAG system."""

import re
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from src.state import SNIGraphState
from src.tools import SNITools


class SNIGraphNodes:
    """LangGraph node definitions for SNI query workflow."""

    # Regex patterns for entity extraction
    SNI_PATTERN = re.compile(
        r"\b([a-zA-Z0-9][-a-zA-Z0-9]{0,62}(?:\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.?)\b"
    )
    DOMAIN_PATTERN = re.compile(
        r"\b([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+[a-zA-Z]{2,}\b"
    )

    def __init__(self, llm: BaseChatModel, tools: SNITools):
        """Initialize graph nodes.

        Args:
            llm: Language model for understanding and generation
            tools: SNI query tools
        """
        self.llm = llm
        self.tools = tools

    def understand_query(self, state: SNIGraphState) -> Dict[str, Any]:
        """Node: Understand user query intent.

        Analyzes the user query to determine:
        - Query type (exact, vector, domain, batch)
        - User intent
        - Extracted entities (SNI names, domains)

        Args:
            state: Current graph state

        Returns:
            Updated state fields
        """
        query = state["query"]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an SNI recognition assistant. Analyze the user query and determine:
1. query_type: exact | vector | domain | batch
   - exact: User provides a complete SNI/domain name
   - vector: Fuzzy search, partial name, or similar search
   - domain: User wants to see all SNIs under a domain
   - batch: User provides multiple SNIs

2. Output your analysis in this format:
   Type: <query_type>
   Intent: <brief description>

Examples:
- "www.google.com" -> Type: exact, Intent: Query specific SNI info
- "google" -> Type: vector, Intent: Fuzzy search for google-related
- "SNIs under google.com" -> Type: domain, Intent: List all google.com SNIs
- "search for something like facebook" -> Type: vector, Intent: Similar search""",
                ),
                ("human", "{query}"),
            ]
        )

        response = self.llm.invoke(prompt.format_messages(query=query))
        content = response.content.lower()

        # Parse query type from LLM response
        if "type: exact" in content or "type:exact" in content:
            query_type = "exact"
        elif "type: domain" in content or "type:domain" in content:
            query_type = "domain"
        elif "type: vector" in content or "type:vector" in content:
            query_type = "vector"
        elif "type: batch" in content or "type:batch" in content:
            query_type = "batch"
        else:
            # Fallback heuristics
            query_type = self._infer_query_type(query)

        # Extract entities
        extracted_entities = self._extract_entities(query)

        return {
            "query_type": query_type,
            "intent": content,
            "extracted_entities": extracted_entities,
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content=query)],
        }

    def _infer_query_type(self, query: str) -> str:
        """Infer query type using heuristics.

        Args:
            query: User query

        Returns:
            Inferred query type
        """
        query_lower = query.lower()

        # Check for domain query indicators
        domain_keywords = ["snis", "all", "list", "under", "subdomains"]
        if any(kw in query_lower for kw in domain_keywords):
            return "domain"

        # Check for fuzzy search indicators
        fuzzy_keywords = ["like", "similar", "search", "find"]
        if any(kw in query_lower for kw in fuzzy_keywords):
            return "vector"

        # Check if query contains a valid domain/SNI pattern
        if self.SNI_PATTERN.search(query):
            return "exact"

        # Default to vector search for ambiguous queries
        return "vector"

    def _extract_entities(self, query: str) -> Dict:
        """Extract SNI and domain entities from query.

        Args:
            query: User query

        Returns:
            Extracted entities
        """
        entities = {"sni_list": [], "domains": []}

        # Extract SNI patterns
        sni_matches = self.SNI_PATTERN.findall(query)
        if sni_matches:
            entities["sni_list"] = list(set(sni_matches))

        # Extract domain patterns
        domain_matches = self.DOMAIN_PATTERN.findall(query)
        if domain_matches:
            # Domain pattern returns partial matches, reconstruct full domains
            for match in self.SNI_PATTERN.findall(query):
                if "." in match:
                    entities["domains"].append(match)
            entities["domains"] = list(set(entities["domains"]))

        return entities

    def route_query(self, state: SNIGraphState) -> str:
        """Routing node: Determine which tool node to call.

        Args:
            state: Current graph state

        Returns:
            Name of the next node to execute
        """
        query_type = state.get("query_type", "exact")

        route_map = {
            "exact": "exact_search",
            "vector": "vector_search",
            "domain": "domain_search",
            "batch": "exact_search",  # Batch uses exact search internally
        }

        return route_map.get(query_type, "exact_search")

    def exact_search_node(self, state: SNIGraphState) -> Dict[str, Any]:
        """Node: Exact SNI search.

        Args:
            state: Current graph state

        Returns:
            Updated state fields
        """
        query = state["query"]
        entities = state.get("extracted_entities") or {}

        # Get SNI from extracted entities or parse from query
        sni_list = entities.get("sni_list", [])
        if sni_list:
            sni = sni_list[0]
        else:
            # Try to extract from query directly
            matches = self.SNI_PATTERN.findall(query)
            sni = matches[0] if matches else query.strip()

        # Call tool
        result = self.tools.search_sni_exact(sni)

        return {
            "tool_calls": state.get("tool_calls", [])
            + [{"tool": "search_sni_exact", "input": sni}],
            "tool_results": state.get("tool_results", []) + [result],
            "step_count": state.get("step_count", 0) + 1,
        }

    def vector_search_node(self, state: SNIGraphState) -> Dict[str, Any]:
        """Node: Vector similarity search.

        Args:
            state: Current graph state

        Returns:
            Updated state fields
        """
        query = state["query"]

        # Extract search keyword
        entities = state.get("extracted_entities") or {}
        sni_list = entities.get("sni_list", [])

        # Use extracted SNI or the original query
        search_query = sni_list[0] if sni_list else query

        # Call tool
        result = self.tools.search_sni_vector(search_query, top_k=5)

        return {
            "tool_calls": state.get("tool_calls", [])
            + [{"tool": "search_sni_vector", "input": search_query}],
            "tool_results": state.get("tool_results", []) + [result],
            "step_count": state.get("step_count", 0) + 1,
        }

    def domain_search_node(self, state: SNIGraphState) -> Dict[str, Any]:
        """Node: Domain-based search.

        Args:
            state: Current graph state

        Returns:
            Updated state fields
        """
        query = state["query"]
        entities = state.get("extracted_entities") or {}

        # Get domain from entities or extract from query
        domains = entities.get("domains", [])
        if domains:
            domain = domains[0]
        else:
            # Try to extract from query
            matches = self.SNI_PATTERN.findall(query)
            domain = matches[0] if matches else "google.com"

        # Call tool
        result = self.tools.search_by_domain(domain, limit=20)

        return {
            "tool_calls": state.get("tool_calls", [])
            + [{"tool": "search_by_domain", "input": domain}],
            "tool_results": state.get("tool_results", []) + [result],
            "step_count": state.get("step_count", 0) + 1,
        }

    def aggregate_results(self, state: SNIGraphState) -> Dict[str, Any]:
        """Node: Aggregate and evaluate results.

        Args:
            state: Current graph state

        Returns:
            Updated state fields
        """
        tool_results = state.get("tool_results", [])

        # Check if we need more information
        need_more = False
        if not tool_results:
            need_more = True
        else:
            # Check if all results are empty or not found
            all_empty = True
            for result in tool_results:
                if isinstance(result, dict):
                    if result.get("found", False):
                        all_empty = False
                        break
                elif isinstance(result, list) and len(result) > 0:
                    all_empty = False
                    break
            need_more = all_empty

        return {
            "need_more_info": need_more,
            "step_count": state.get("step_count", 0) + 1,
        }

    def should_continue(self, state: SNIGraphState) -> str:
        """Conditional node: Decide whether to continue or generate answer.

        Args:
            state: Current graph state

        Returns:
            Next node name
        """
        need_more = state.get("need_more_info", False)
        step_count = state.get("step_count", 0)
        query_type = state.get("query_type", "exact")

        # If need more info and haven't tried vector search yet, try it
        if need_more and step_count < 4 and query_type == "exact":
            return "vector_search"

        return "generate_answer"

    def generate_answer(self, state: SNIGraphState) -> Dict[str, Any]:
        """Node: Generate final answer.

        Args:
            state: Current graph state

        Returns:
            Updated state fields with answer
        """
        import json
        import re

        query = state["query"]
        tool_results = state.get("tool_results", [])

        # Build context from tool results
        context = self._build_context(tool_results)

        # Generate structured answer using LLM
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an SNI recognition expert. Based on the query results, provide a structured JSON response with ONLY these three fields:

{{
  "Website/Service": "The name of the website or service",
  "Explanation": "A brief 1-2 sentence explanation of what this service does",
  "Query Results": "The raw query results from the database"
}}

CRITICAL REQUIREMENTS:
1. Output MUST be valid JSON only, no markdown, no code blocks, no additional text
2. Start directly with {{ and end with }}
3. If no results found, use "Unknown" for Website/Service
4. Always respond in the same language as the user's query
5. Keep Explanation concise (max 2 sentences)""",
                ),
                ("human", "User query: {query}\n\nDatabase results:\n{context}"),
            ]
        )

        response = self.llm.invoke(prompt.format_messages(query=query, context=context))

        # Extract JSON from response
        content = response.content.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        # Remove any leading/trailing non-JSON text
        if not content.startswith('{'):
            # Find first {
            start = content.find('{')
            if start != -1:
                content = content[start:]

        if not content.endswith('}'):
            # Find last }
            end = content.rfind('}')
            if end != -1:
                content = content[:end+1]

        return {
            "answer": content,
            "messages": state.get("messages", []) + [AIMessage(content=content)],
            "step_count": state.get("step_count", 0) + 1,
        }

    def _build_context(self, tool_results: list) -> str:
        """Build context string from tool results.

        Args:
            tool_results: List of tool results

        Returns:
            Formatted context string
        """
        if not tool_results:
            return "No results found"

        context_parts = ["Query Results:"]

        for i, result in enumerate(tool_results, 1):
            if isinstance(result, dict):
                if result.get("found"):
                    # Check if it's new format with multiple matches
                    if "matches" in result and "match_count" in result:
                        match_count = result.get("match_count", 0)
                        matches = result.get("matches", [])

                        context_parts.append(f"\n{i}. Found {match_count} records for SNI: {result.get('sni')}")
                        context_parts.append("\nAll matching domains:")

                        # Show all matches
                        for idx, match in enumerate(matches[:20], 1):  # Limit to 20 for readability
                            context_parts.append(
                                f"   {idx}. Domain: {match.get('domain')} | "
                                f"Protocols: {', '.join(match.get('protocols', []))}"
                            )

                        if match_count > 20:
                            context_parts.append(f"   ... and {match_count - 20} more records")
                    else:
                        # Old format
                        context_parts.append(f"\n{i}. SNI: {result.get('sni')}")
                        context_parts.append(f"   Domain: {result.get('domain')}")
                        protocols = result.get("protocols", [])
                        if protocols:
                            context_parts.append(f"   Protocols: {', '.join(protocols)}")
                        related = result.get("all_related_snis", [])
                        if related:
                            context_parts.append(
                                f"   Related SNIs: {', '.join(related[:5])}"
                            )
                elif result.get("error"):
                    context_parts.append(f"\n{i}. Error: {result.get('error')}")
            elif isinstance(result, list) and len(result) > 0:
                context_parts.append(f"\nFound {len(result)} related SNIs:")
                for item in result[:5]:
                    context_parts.append(
                        f"  - {item.get('sni')} (Domain: {item.get('domain')}, "
                        f"Score: {item.get('score', 'N/A')})"
                    )

        if len(context_parts) == 1:
            return "No results found in the database"

        return "\n".join(context_parts)

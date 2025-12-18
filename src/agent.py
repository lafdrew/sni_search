"""SNI RAG Agent with LLM tool calling."""

from typing import Optional, Dict, Any, List, Iterator
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.config import settings
from src.tools import SNITools, create_langchain_tools


class SNIAgent:
    """SNI Recognition Agent that uses LLM to actively call tools."""

    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize SNI Agent.

        Args:
            qdrant_url: Qdrant server URL
            api_key: Anthropic API key
            model: Claude model name
        """
        self.tools_instance = SNITools(qdrant_url=qdrant_url or settings.QDRANT_URL)

        llm_kwargs = {
            "model": model or settings.CLAUDE_MODEL,
            "api_key": api_key or settings.ANTHROPIC_API_KEY,
            "temperature": 0,
        }
        if settings.ANTHROPIC_BASE_URL:
            llm_kwargs["base_url"] = settings.ANTHROPIC_BASE_URL

        self.llm = ChatAnthropic(**llm_kwargs)

        self.langchain_tools = create_langchain_tools(self.tools_instance)
        self.llm_with_tools = self.llm.bind_tools(self.langchain_tools)

        self.system_prompt = """You are an SNI (Server Name Indication) recognition expert assistant.

Your task is to help users query SNI information from a database. You have access to the following tools:

1. search_sni_exact: Use when the user provides a complete SNI/domain name (e.g., "www.google.com")
2. search_sni_vector: Use for fuzzy search, partial matching, or similar queries (e.g., "google")
3. search_by_domain: Use when the user wants to see all SNIs under a domain (e.g., "all SNIs under google.com")

WORKFLOW:
1. Analyze the user query to understand their intent
2. Select the most appropriate tool(s) to call
3. Call the tool(s) with proper parameters
4. Generate a structured response based on tool results

OUTPUT FORMAT:
After receiving tool results, provide a JSON response with these three fields:
{
  "Website/Service": "The name of the website or service",
  "Explanation": "A brief 1-2 sentence explanation of what this service does",
  "Query Results": "Summary of the database query results"
}

IMPORTANT:
- Always respond in the same language as the user's query
- If no results found, use "Unknown" for Website/Service
- Keep explanations concise and informative
- Output MUST be valid JSON without markdown code blocks"""

    def _create_prompt(self, query: str) -> List:
        """Create prompt messages for the LLM.

        Args:
            query: User query

        Returns:
            List of messages
        """
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query},
        ]

    def query(
        self,
        query: str,
        max_iterations: int = 5,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """Execute SNI query using LLM agent.

        Args:
            query: User query string
            max_iterations: Maximum number of agent iterations
            verbose: If True, print detailed execution process

        Returns:
            Query result dictionary with answer and metadata
        """
        messages = self._create_prompt(query)
        tool_calls_made = []
        execution_trace = []

        if verbose:
            print("\n" + "="*80)
            print(f"Agent Query: {query}")
            print("="*80)

        for iteration in range(max_iterations):
            if verbose:
                print(f"\n[Iteration {iteration + 1}]")
                print("-"*80)
                print("Thinking...")

            response = self.llm_with_tools.invoke(messages)

            if not response.tool_calls:
                answer = response.content
                if verbose:
                    print("\nFinal Answer Generated:")
                    print("-"*80)
                    print(answer[:300] + "..." if len(answer) > 300 else answer)
                    print("="*80)

                return {
                    "query": query,
                    "answer": answer,
                    "tool_calls": tool_calls_made,
                    "iterations": iteration + 1,
                    "trace": execution_trace,
                }

            if verbose and hasattr(response, 'content') and response.content:
                print(f"Reasoning: {response.content}")

            messages.append(response)

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                if verbose:
                    print(f"\nTool Call: {tool_name}")
                    print(f"Arguments: {tool_args}")

                tool_calls_made.append({
                    "tool": tool_name,
                    "args": tool_args,
                })

                tool_func = next(
                    (t for t in self.langchain_tools if t.name == tool_name),
                    None
                )

                if tool_func:
                    try:
                        tool_result = tool_func.invoke(tool_args)
                        if verbose:
                            result_preview = str(tool_result)[:200]
                            print(f"Result: {result_preview}..." if len(str(tool_result)) > 200 else f"Result: {tool_result}")
                    except Exception as e:
                        tool_result = {"error": str(e)}
                        if verbose:
                            print(f"Error: {e}")
                else:
                    tool_result = {"error": f"Tool {tool_name} not found"}
                    if verbose:
                        print(f"Error: Tool {tool_name} not found")

                execution_trace.append({
                    "iteration": iteration + 1,
                    "tool": tool_name,
                    "args": tool_args,
                    "result": tool_result,
                })

                tool_message = ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_id,
                )
                messages.append(tool_message)

        if verbose:
            print("\nMaximum iterations reached!")
            print("="*80)

        return {
            "query": query,
            "answer": "Maximum iterations reached without final answer",
            "tool_calls": tool_calls_made,
            "iterations": max_iterations,
            "trace": execution_trace,
        }

    async def aquery(
        self,
        query: str,
        max_iterations: int = 5,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """Execute SNI query asynchronously using LLM agent.

        Args:
            query: User query string
            max_iterations: Maximum number of agent iterations
            verbose: If True, print detailed execution process

        Returns:
            Query result dictionary with answer and metadata
        """
        messages = self._create_prompt(query)
        tool_calls_made = []
        execution_trace = []

        if verbose:
            print("\n" + "="*80)
            print(f"Agent Query: {query}")
            print("="*80)

        for iteration in range(max_iterations):
            if verbose:
                print(f"\n[Iteration {iteration + 1}]")
                print("-"*80)
                print("Thinking...")

            response = await self.llm_with_tools.ainvoke(messages)

            if not response.tool_calls:
                answer = response.content
                if verbose:
                    print("\nFinal Answer Generated:")
                    print("-"*80)
                    print(answer[:300] + "..." if len(answer) > 300 else answer)
                    print("="*80)

                return {
                    "query": query,
                    "answer": answer,
                    "tool_calls": tool_calls_made,
                    "iterations": iteration + 1,
                    "trace": execution_trace,
                }

            if verbose and hasattr(response, 'content') and response.content:
                print(f"Reasoning: {response.content}")

            messages.append(response)

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                if verbose:
                    print(f"\nTool Call: {tool_name}")
                    print(f"Arguments: {tool_args}")

                tool_calls_made.append({
                    "tool": tool_name,
                    "args": tool_args,
                })

                tool_func = next(
                    (t for t in self.langchain_tools if t.name == tool_name),
                    None
                )

                if tool_func:
                    try:
                        tool_result = await tool_func.ainvoke(tool_args)
                        if verbose:
                            result_preview = str(tool_result)[:200]
                            print(f"Result: {result_preview}..." if len(str(tool_result)) > 200 else f"Result: {tool_result}")
                    except Exception as e:
                        tool_result = {"error": str(e)}
                        if verbose:
                            print(f"Error: {e}")
                else:
                    tool_result = {"error": f"Tool {tool_name} not found"}
                    if verbose:
                        print(f"Error: Tool {tool_name} not found")

                execution_trace.append({
                    "iteration": iteration + 1,
                    "tool": tool_name,
                    "args": tool_args,
                    "result": tool_result,
                })

                tool_message = ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_id,
                )
                messages.append(tool_message)

        if verbose:
            print("\nMaximum iterations reached!")
            print("="*80)

        return {
            "query": query,
            "answer": "Maximum iterations reached without final answer",
            "tool_calls": tool_calls_made,
            "iterations": max_iterations,
            "trace": execution_trace,
        }


def create_sni_agent(
    qdrant_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> SNIAgent:
    """Create SNI Agent instance.

    Args:
        qdrant_url: Qdrant server URL
        api_key: Anthropic API key
        model: Claude model name

    Returns:
        Configured SNI Agent
    """
    return SNIAgent(
        qdrant_url=qdrant_url,
        api_key=api_key,
        model=model,
    )


def stream_query(
    agent: SNIAgent,
    query: str,
    max_iterations: int = 5,
) -> Dict[str, Any]:
    """Execute SNI query with streaming output (shows complete raw LLM output).

    Args:
        agent: SNI Agent instance
        query: User query string
        max_iterations: Maximum number of agent iterations

    Returns:
        Query result dictionary with answer and metadata
    """
    messages = agent._create_prompt(query)
    tool_calls_made = []
    execution_trace = []
    final_answer = ""

    print("\n" + "="*80)
    print(f"Query: {query}")
    print("="*80)

    for iteration in range(max_iterations):
        print(f"\n[Iteration {iteration + 1}]")
        print("-"*80)
        print("LLM Raw Output Stream:")
        print()

        all_chunks = []
        has_tool_calls = False
        accumulated_text = ""

        for chunk in agent.llm_with_tools.stream(messages):
            all_chunks.append(chunk)

            if hasattr(chunk, 'content') and chunk.content:
                if isinstance(chunk.content, list):
                    for item in chunk.content:
                        if isinstance(item, dict):
                            if item.get('type') == 'text':
                                text = item.get('text', '')
                                print(text, end='', flush=True)
                                accumulated_text += text
                            elif item.get('type') == 'tool_use':
                                print(f"\n[Tool Use Decision: {item}]", flush=True)
                            elif item.get('type') == 'input_json_delta':
                                print(f"[JSON Delta: {item.get('partial_json', '')}]", end='', flush=True)
                            else:
                                print(f"\n[Content Item: {item}]", flush=True)
                elif isinstance(chunk.content, str):
                    print(chunk.content, end='', flush=True)
                    accumulated_text += chunk.content

            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                has_tool_calls = True

            if hasattr(chunk, 'response_metadata') and chunk.response_metadata:
                metadata = chunk.response_metadata
                if metadata.get('stop_reason'):
                    print(f"\n[Stop Reason: {metadata['stop_reason']}]", flush=True)
                if metadata.get('model_name'):
                    print(f"[Model: {metadata['model_name']}]", flush=True)

            if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                usage = chunk.usage_metadata
                print(f"\n[Token Usage: input={usage.get('input_tokens')}, output={usage.get('output_tokens')}, total={usage.get('total_tokens')}]", flush=True)

        print()
        print("-"*80)

        full_response = agent.llm_with_tools.invoke(messages)

        if not full_response.tool_calls:
            final_answer = full_response.content
            print("\n" + "="*80)
            print("Final Answer Generated")
            print("="*80)
            print(final_answer)
            print("="*80)

            return {
                "query": query,
                "answer": final_answer,
                "tool_calls": tool_calls_made,
                "iterations": iteration + 1,
                "trace": execution_trace,
            }

        messages.append(full_response)

        for tool_call in full_response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            print(f"\nTool Call: {tool_name}")
            print(f"Arguments: {tool_args}")

            tool_calls_made.append({
                "tool": tool_name,
                "args": tool_args,
            })

            tool_func = next(
                (t for t in agent.langchain_tools if t.name == tool_name),
                None
            )

            if tool_func:
                try:
                    print("Executing tool...", end="", flush=True)
                    tool_result = tool_func.invoke(tool_args)
                    print(" Done")
                    result_preview = str(tool_result)[:400]
                    print(f"Tool Result: {result_preview}")
                    if len(str(tool_result)) > 400:
                        print("... (truncated)")
                except Exception as e:
                    tool_result = {"error": str(e)}
                    print(f"\nTool Error: {e}")
            else:
                tool_result = {"error": f"Tool {tool_name} not found"}
                print(f"Tool Error: Tool {tool_name} not found")

            execution_trace.append({
                "iteration": iteration + 1,
                "tool": tool_name,
                "args": tool_args,
                "result": tool_result,
            })

            tool_message = ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_id,
            )
            messages.append(tool_message)

    print("\nMaximum iterations reached")
    print("="*80)

    return {
        "query": query,
        "answer": "Maximum iterations reached without final answer",
        "tool_calls": tool_calls_made,
        "iterations": max_iterations,
        "trace": execution_trace,
    }

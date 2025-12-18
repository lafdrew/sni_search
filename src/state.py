"""State definition for SNI RAG LangGraph."""

from typing import TypedDict, List, Dict, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator


class SNIGraphState(TypedDict):
    """SNI query workflow state.

    This TypedDict defines the state that flows through the LangGraph nodes.
    Each field represents a piece of information that may be updated by nodes.
    """

    # Input
    query: str  # User query

    # Intermediate state
    query_type: Optional[str]  # Query type: exact, vector, domain, batch
    intent: Optional[str]  # User intent description
    extracted_entities: Optional[Dict]  # Extracted entities (SNI names, etc.)

    # Tool calls
    tool_calls: List[Dict]  # Executed tool calls
    tool_results: List[Dict]  # Tool return results

    # Output
    answer: Optional[str]  # Final answer
    need_more_info: bool  # Whether more info is needed

    # Metadata
    messages: Annotated[List[BaseMessage], operator.add]  # Message history
    step_count: int  # Step counter
    error: Optional[str]  # Error message


def create_initial_state(query: str) -> SNIGraphState:
    """Create initial state for a new query.

    Args:
        query: User's query string

    Returns:
        Initial SNIGraphState with default values
    """
    return {
        "query": query,
        "query_type": None,
        "intent": None,
        "extracted_entities": None,
        "tool_calls": [],
        "tool_results": [],
        "answer": None,
        "need_more_info": False,
        "messages": [],
        "step_count": 0,
        "error": None,
    }

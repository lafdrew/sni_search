"""Tool for the SearchApi search API."""

import json
import logging
from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.searchapi_search.searchapi_search_api import SearchApiAPIWrapper

logger = logging.getLogger(__name__)


class SearchApiInput(BaseModel):
    """Input for the SearchApi tool."""

    query: str = Field(description="search query to look up")


class SearchApiSearchResults(BaseTool):
    """Tool that queries the SearchApi Search API and returns processed results."""

    name: str = "searchapi_search_results_json"
    description: str = (
        "A search engine powered by SearchApi. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query."
    )
    args_schema: Type[BaseModel] = SearchApiInput

    engine: str = "google"
    """Search engine to use (default: google)."""

    max_results: int = 7
    """Maximum number of results to return."""

    api_wrapper: SearchApiAPIWrapper = Field(default_factory=SearchApiAPIWrapper)
    response_format: Literal["content_and_artifact"] = "content_and_artifact"

    def __init__(self, **kwargs: Any) -> None:
        if "engine" in kwargs:
            engine = kwargs["engine"]
            kwargs["api_wrapper"] = SearchApiAPIWrapper(engine=engine)
            logger.debug(f"API wrapper initialized with engine: {engine}")

        super().__init__(**kwargs)

        logger.info(
            "\n============================================\n"
            "SearchApi Search Initialization\n"
            "============================================"
        )

        initialization_details = (
            f"\nTool Information:\n"
            f"Tool Name: {self.name}\n"
            f"Search Engine: {self.engine}\n"
            f"Max Results: {self.max_results}\n"
            f"Configuration Summary:\n"
            f"Response Format: {self.response_format}\n"
        )

        logger.info(initialization_details)
        logger.info("\n" + "*" * 70 + "\n")

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        """Use the tool."""
        try:
            logger.debug(f"Executing SearchApi search with engine={self.engine}")
            results = self.api_wrapper.raw_results(query, self.max_results)

            result_json = json.dumps(results, ensure_ascii=False)

            logger.info(
                f"SearchApi tool execution completed | "
                f"mode=synchronous | "
                f"results_count={len(results)}"
            )
            return result_json, {"results": results}
        except Exception as e:
            logger.error(
                f"SearchApi tool execution failed | "
                f"mode=synchronous | "
                f"error={str(e)}"
            )
            error_result = json.dumps({"error": repr(e)}, ensure_ascii=False)
            return error_result, {}

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        """Use the tool asynchronously."""
        if logger.isEnabledFor(logging.DEBUG):
            query_truncated = query[:50] + "..." if len(query) > 50 else query
            logger.debug(
                f"SearchApi tool execution started | "
                f"mode=asynchronous | "
                f"query={query_truncated}"
            )
        try:
            logger.debug(f"Executing async SearchApi search with engine={self.engine}")

            results = await self.api_wrapper.raw_results_async(query, self.max_results)

            result_json = json.dumps(results, ensure_ascii=False)

            logger.debug(
                f"SearchApi tool execution completed | "
                f"mode=asynchronous | "
                f"results_count={len(results)}"
            )

            return result_json, {"results": results}
        except Exception as e:
            logger.error(
                f"SearchApi tool execution failed | "
                f"mode=asynchronous | "
                f"error={str(e)}"
            )
            error_result = json.dumps({"error": repr(e)}, ensure_ascii=False)
            return error_result, {}

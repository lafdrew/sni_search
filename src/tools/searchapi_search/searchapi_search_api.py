"""SearchApi API wrapper implementation."""

import logging
import os
import urllib.parse
from typing import Dict, List, Any, Optional

import requests

logger = logging.getLogger(__name__)


class SearchApiAPIWrapper:
    """Wrapper for SearchApi API."""

    def __init__(self, engine: str = "google"):
        """Initialize the SearchApi API wrapper.

        Args:
            engine: Search engine to use (default: "google")
        """
        self.api_key = self._get_api_key()
        self.engine = engine
        self.api_url = "https://www.searchapi.io/api/v1/search"
        logger.info(f"SearchApi wrapper initialized with engine: {engine}")

    def _get_api_key(self) -> str:
        """Get API key from environment variable.

        Returns:
            API key string

        Raises:
            Exception: If API key is not found
        """
        api_key = os.getenv("SEARCHAPI_API_KEY")
        if not api_key:
            raise Exception(
                "SearchApi key not found. Please set the SEARCHAPI_API_KEY environment variable. "
                "You can get a key at https://www.searchapi.io/"
            )
        return api_key

    def raw_results(self, query: str, max_results: int = 7) -> List[Dict[str, Any]]:
        """Execute search and return raw results.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        params = {
            "q": query,
            "engine": self.engine,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-SearchApi-Source": "sni-search",
        }

        try:
            logger.debug(f"SearchApi request: query='{query[:50]}...', engine={self.engine}")
            response = requests.get(
                self.api_url + "?" + urllib.parse.urlencode(params),
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()

            search_results = response.json()
            organic_results = search_results.get("organic_results", [])

            logger.info(f"SearchApi returned {len(organic_results)} results")

            return self._process_results(organic_results, max_results)

        except requests.exceptions.RequestException as e:
            logger.error(f"SearchApi request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"SearchApi error: {e}")
            return []

    def _process_results(
        self,
        organic_results: List[Dict[str, Any]],
        max_results: int
    ) -> List[Dict[str, str]]:
        """Process and filter search results.

        Args:
            organic_results: Raw organic results from API
            max_results: Maximum number of results to return

        Returns:
            List of processed results
        """
        search_response = []

        for result in organic_results[:max_results]:
            link = result.get("link", "")

            # Filter out YouTube results
            if "youtube.com" in link:
                continue

            search_response.append({
                "title": result.get("title", ""),
                "url": link,
                "snippet": result.get("snippet", ""),
            })

        logger.debug(f"Processed {len(search_response)} results (filtered)")
        return search_response

    async def raw_results_async(
        self,
        query: str,
        max_results: int = 7
    ) -> List[Dict[str, Any]]:
        """Async version of raw_results.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        import aiohttp

        params = {
            "q": query,
            "engine": self.engine,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-SearchApi-Source": "sni-search",
        }

        try:
            logger.debug(f"SearchApi async request: query='{query[:50]}...', engine={self.engine}")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url + "?" + urllib.parse.urlencode(params),
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as response:
                    response.raise_for_status()
                    search_results = await response.json()

            organic_results = search_results.get("organic_results", [])
            logger.info(f"SearchApi async returned {len(organic_results)} results")

            return self._process_results(organic_results, max_results)

        except Exception as e:
            logger.error(f"SearchApi async error: {e}")
            return []

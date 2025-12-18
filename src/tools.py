"""SNI query tools for LangGraph."""

from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from langchain_core.tools import tool

from src.config import settings


class SNITools:
    """SNI query toolkit.

    Provides tools for querying SNI information from Qdrant vector database.
    """

    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        """Initialize SNI tools.

        Args:
            qdrant_url: Qdrant server URL
            collection_name: Collection name in Qdrant
            embedding_model: Sentence transformer model name
        """
        self.qdrant_url = qdrant_url or settings.QDRANT_URL
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.embedding_model_name = embedding_model or settings.EMBEDDING_MODEL

        self.client = QdrantClient(url=self.qdrant_url)
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load sentence transformer model."""
        if self._model is None:
            self._model = SentenceTransformer(self.embedding_model_name)
        return self._model

    def search_sni_exact(self, sni: str) -> Dict:
        """Exact match SNI name.

        Args:
            sni: Full SNI name

        Returns:
            SNI details or not found indicator
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="sni", match=MatchValue(value=sni))]
            ),
            limit=1,
            with_payload=True,
        )

        if not results[0]:
            return {"found": False, "sni": sni}

        point = results[0][0]
        return {
            "found": True,
            "sni": point.payload.get("sni"),
            "domain": point.payload.get("domain"),
            "all_related_snis": point.payload.get("all_snis", []),
            "protocols": point.payload.get("alpn_protocols", []),
            "total_count": point.payload.get("total_count"),
        }

    def search_sni_vector(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict]:
        """Vector similarity search for SNI.

        Args:
            query: Search keyword
            top_k: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            List of similar SNIs
        """
        query_vector = self.model.encode(query).tolist()

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        )

        return [
            {
                "sni": hit.payload.get("sni"),
                "domain": hit.payload.get("domain"),
                "score": round(hit.score, 3),
                "protocols": hit.payload.get("alpn_protocols", []),
            }
            for hit in results.points
        ]

    def search_by_domain(self, domain: str, limit: int = 20) -> List[Dict]:
        """Search all SNIs by domain.

        Args:
            domain: Main domain name
            limit: Maximum number of results

        Returns:
            All SNIs under this domain
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="domain", match=MatchValue(value=domain))]
            ),
            limit=limit,
            with_payload=True,
        )

        seen = set()
        unique_results = []
        for point in results[0]:
            sni = point.payload.get("sni")
            if sni not in seen:
                seen.add(sni)
                unique_results.append(
                    {
                        "sni": sni,
                        "domain": point.payload.get("domain"),
                        "protocols": point.payload.get("alpn_protocols", []),
                    }
                )

        return unique_results

    def batch_search_sni(self, sni_list: List[str]) -> Dict[str, Optional[Dict]]:
        """Batch search multiple SNIs.

        Args:
            sni_list: List of SNI names

        Returns:
            Dict mapping SNI to its details
        """
        results = {}
        for sni in sni_list:
            result = self.search_sni_exact(sni)
            results[sni] = result if result.get("found") else None
        return results

    def get_stats(self) -> Dict:
        """Get collection statistics.

        Returns:
            Collection statistics
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)

            # Sample to get domain distribution
            sample_results = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                with_payload=True,
            )

            domains = {}
            for point in sample_results[0]:
                domain = point.payload.get("domain")
                if domain:
                    domains[domain] = domains.get(domain, 0) + 1

            top_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "total_records": collection_info.points_count,
                "vector_dimension": collection_info.config.params.vectors.size,
                "top_domains": [{"domain": d[0], "count": d[1]} for d in top_domains],
                "collection_status": str(collection_info.status),
            }
        except Exception as e:
            return {"error": str(e)}


def create_langchain_tools(tools_instance: SNITools):
    """Create LangChain tool wrappers.

    Args:
        tools_instance: SNITools instance

    Returns:
        List of LangChain tools
    """

    @tool
    def search_sni_exact(sni: str) -> Dict:
        """Exact match SNI name.

        Use this tool when the user provides a complete SNI name.

        Args:
            sni: Full SNI name to search
        """
        return tools_instance.search_sni_exact(sni)

    @tool
    def search_sni_vector(query: str, top_k: int = 5) -> List[Dict]:
        """Vector similarity search for SNI.

        Use this tool for fuzzy search, partial matching, or when the input may contain typos.

        Args:
            query: Search keyword or partial SNI name
            top_k: Number of results to return
        """
        return tools_instance.search_sni_vector(query, top_k=top_k)

    @tool
    def search_by_domain(domain: str, limit: int = 20) -> List[Dict]:
        """Search all SNIs by domain.

        Use this tool when the user wants to see all SNIs under a specific domain.

        Args:
            domain: Main domain name (e.g., 'google.com')
            limit: Maximum number of results
        """
        return tools_instance.search_by_domain(domain, limit=limit)

    return [search_sni_exact, search_sni_vector, search_by_domain]

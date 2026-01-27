"""TGT standard library tools for managing canonical entity names."""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
    PayloadSchemaType,
)
from sentence_transformers import SentenceTransformer

from src.config import settings

logger = logging.getLogger(__name__)


class TGTLibraryTools:
    """TGT standard library toolkit.

    Provides tools for managing canonical entity names with vector-based
    similarity search and LLM-assisted entity resolution.
    """

    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        """Initialize TGT library tools.

        Args:
            qdrant_url: Qdrant server URL
            collection_name: Collection name in Qdrant
            embedding_model: Sentence transformer model name
        """
        self.qdrant_url = qdrant_url or settings.QDRANT_URL
        self.collection_name = collection_name or settings.QDRANT_TGT_COLLECTION
        self.embedding_model_name = embedding_model or settings.EMBEDDING_MODEL

        self.client = QdrantClient(url=self.qdrant_url)
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load sentence transformer model."""
        if self._model is None:
            self._model = SentenceTransformer(self.embedding_model_name)
        return self._model

    def create_collection(self, recreate: bool = False) -> bool:
        """Create TGT standard library collection.

        Args:
            recreate: If True, delete existing collection and recreate

        Returns:
            True if collection was created, False if it already exists
        """
        try:
            collections = self.client.get_collections().collections
            collection_exists = any(
                c.name == self.collection_name for c in collections
            )

            if collection_exists:
                if recreate:
                    logger.info(f"Deleting existing collection: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection already exists: {self.collection_name}")
                    return False

            vector_size = self.model.get_sentence_embedding_dimension()
            logger.info(f"Creating collection: {self.collection_name} with vector size: {vector_size}")

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

            # Create indexes for efficient filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="standard_name",
                field_schema=PayloadSchemaType.KEYWORD,
            )

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="aliases",
                field_schema=PayloadSchemaType.KEYWORD,
            )

            logger.info(f"Collection created successfully: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    def search_exact(self, tgt_name: str) -> Optional[Dict]:
        """Exact match for entity name or alias.

        Args:
            tgt_name: Entity name to search for

        Returns:
            Entity details if found, None otherwise
        """
        try:
            # Search in standard_name field
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    should=[
                        FieldCondition(
                            key="standard_name",
                            match=MatchValue(value=tgt_name)
                        ),
                        FieldCondition(
                            key="aliases",
                            match=MatchValue(value=tgt_name)
                        ),
                    ]
                ),
                limit=1,
                with_payload=True,
            )

            if not results[0]:
                return None

            point = results[0][0]
            return {
                "id": point.id,
                "standard_name": point.payload.get("standard_name"),
                "full_name": point.payload.get("full_name"),
                "aliases": point.payload.get("aliases", []),
                "verification_status": point.payload.get("verification_status"),
            }

        except Exception as e:
            logger.error(f"Error in exact search: {e}")
            return None

    def search_vector(
        self,
        tgt_name: str,
        top_k: int = 5,
        threshold: float = 0.75,
    ) -> List[Dict]:
        """Vector similarity search for entity names.

        Args:
            tgt_name: Entity name to search for
            top_k: Number of results to return
            threshold: Minimum similarity score

        Returns:
            List of similar entities with scores
        """
        try:
            query_vector = self.model.encode(tgt_name).tolist()

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                score_threshold=threshold,
                with_payload=True,
            )

            return [
                {
                    "id": hit.id,
                    "standard_name": hit.payload.get("standard_name"),
                    "full_name": hit.payload.get("full_name"),
                    "aliases": hit.payload.get("aliases", []),
                    "category": hit.payload.get("category"),
                    "description": hit.payload.get("description"),
                    "score": round(hit.score, 3),
                }
                for hit in results.points
            ]

        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    def search_keyword_fuzzy(self, tgt_name: str, limit: int = 10) -> List[Dict]:
        """Fuzzy keyword search - extract core keyword and search all entities.

        Args:
            tgt_name: Entity name to search for
            limit: Max results to return

        Returns:
            List of entities that contain the core keyword
        """
        try:
            import re

            # Extract core keywords (alphanumeric words longer than 3 chars)
            keywords = re.findall(r'\b[a-zA-Z0-9]{4,}\b', tgt_name)

            if not keywords:
                # For Chinese or short names, use the full name
                keywords = [tgt_name]

            logger.info(f"[TGT] Extracted keywords for fuzzy search: {keywords}")

            # Get all entities and filter locally
            all_results = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit * 10,  # Get more to filter
                with_payload=True,
            )

            matches = []
            for point in all_results[0]:
                payload = point.payload
                standard_name = payload.get("standard_name", "")
                aliases = payload.get("aliases", [])
                description = payload.get("description", "")

                # Check if any keyword matches
                text_to_search = f"{standard_name} {' '.join(aliases)} {description}".lower()

                for keyword in keywords:
                    if keyword.lower() in text_to_search:
                        matches.append({
                            "id": point.id,
                            "standard_name": standard_name,
                            "full_name": payload.get("full_name"),
                            "aliases": aliases,
                            "category": payload.get("category"),
                            "description": description,
                            "score": 0.5,  # Default score for fuzzy match
                            "match_type": "keyword"
                        })
                        break

                if len(matches) >= limit:
                    break

            return matches

        except Exception as e:
            logger.error(f"Error in fuzzy keyword search: {e}")
            return []

    def add_alias(self, standard_name: str, new_alias: str) -> bool:
        """Add an alias to an existing entity.

        Args:
            standard_name: Standard name of the entity
            new_alias: New alias to add

        Returns:
            True if alias was added successfully
        """
        try:
            # Find the entity
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="standard_name",
                            match=MatchValue(value=standard_name)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
            )

            if not results[0]:
                logger.warning(f"Entity not found: {standard_name}")
                return False

            point = results[0][0]
            aliases = point.payload.get("aliases", [])

            # Check if alias already exists
            if new_alias in aliases or new_alias == standard_name:
                logger.info(f"Alias already exists: {new_alias}")
                return True

            # Add new alias
            aliases.append(new_alias)

            # Update the point
            self.client.set_payload(
                collection_name=self.collection_name,
                payload={
                    "aliases": aliases,
                    "updated_at": datetime.utcnow().isoformat(),
                },
                points=[point.id],
            )

            logger.info(f"Added alias '{new_alias}' to entity '{standard_name}'")
            return True

        except Exception as e:
            logger.error(f"Error adding alias: {e}")
            return False

    def create_entity(self, tgt_data: Dict) -> str:
        """Create a new entity in the standard library.

        Args:
            tgt_data: Entity data dict containing:
                - standard_name: Required
                - full_name: Optional
                - aliases: Optional list
                - category: Optional
                - description: Optional
                - verification_status: Optional

        Returns:
            Entity ID
        """
        try:
            standard_name = tgt_data.get("standard_name")
            if not standard_name:
                raise ValueError("standard_name is required")

            # Generate vector from standard name, aliases, and description
            text_to_embed = standard_name
            aliases = tgt_data.get("aliases", [])
            if aliases:
                text_to_embed += " " + " ".join(aliases[:3])

            # Include description in embedding for better similarity matching
            description = tgt_data.get("description", "")
            if description:
                text_to_embed += " " + description

            vector = self.model.encode(text_to_embed).tolist()

            # Prepare payload
            now = datetime.utcnow().isoformat()
            payload = {
                "standard_name": standard_name,
                "full_name": tgt_data.get("full_name", standard_name),
                "aliases": aliases,
                "category": tgt_data.get("category"),
                "description": description,
                "verification_status": tgt_data.get("verification_status", "auto_generated"),
                "created_at": now,
                "updated_at": now,
            }

            # Create point
            entity_id = str(uuid.uuid4())
            point = PointStruct(
                id=entity_id,
                vector=vector,
                payload=payload,
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

            logger.info(f"Created new entity: {standard_name} (ID: {entity_id})")
            return entity_id

        except Exception as e:
            logger.error(f"Error creating entity: {e}")
            raise

    def check_specificity(self, tgt_name: str, llm) -> Dict:
        """Check if entity name is specific enough using LLM.

        Args:
            tgt_name: Entity name to check
            llm: LLM instance for judgment

        Returns:
            Dict with is_specific, confidence, reason, suggested_refinement
        """
        try:
            from src.prompts import apply_prompt_variables

            prompt = apply_prompt_variables(
                "tgt_specificity_check",
                variables={"tgt_name": tgt_name},
                locale="zh_CN",
            )

            response = llm.invoke([{"role": "user", "content": prompt}])
            result = self._parse_json_response(response.content)

            return {
                "is_specific": result.get("is_specific", False),
                "confidence": result.get("confidence", 0.0),
                "reason": result.get("reason", ""),
                "suggested_refinement": result.get("suggested_refinement"),
            }

        except Exception as e:
            logger.error(f"Error checking specificity: {e}")
            # Default to accepting if check fails
            return {
                "is_specific": True,
                "confidence": 0.5,
                "reason": f"Specificity check failed: {e}",
                "suggested_refinement": None,
            }

    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON from LLM response, handling markdown code blocks.

        Args:
            content: Raw LLM response

        Returns:
            Parsed JSON dict
        """
        # Remove markdown code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()
        return json.loads(content)

    def get_stats(self) -> Dict:
        """Get statistics about the standard library.

        Returns:
            Dict with collection statistics
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "total_entities": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

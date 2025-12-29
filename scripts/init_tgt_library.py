"""Initialize TGT standard library collection in Qdrant."""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Direct imports to avoid circular dependencies
import os
from dotenv import load_dotenv

load_dotenv()

# Import only what we need
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_config():
    """Get configuration from environment variables."""
    return {
        'qdrant_url': os.getenv('QDRANT_URL', 'http://localhost:6333'),
        'collection_name': os.getenv('QDRANT_TGT_COLLECTION', 'tgt_standard_library'),
        'embedding_model': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    }


def create_collection(client: QdrantClient, collection_name: str, model: SentenceTransformer) -> bool:
    """Create TGT standard library collection.

    Args:
        client: Qdrant client instance
        collection_name: Name of collection to create
        model: Embedding model for vector size

    Returns:
        True if collection was created, False if it already exists
    """
    try:
        collections = client.get_collections().collections
        collection_exists = any(c.name == collection_name for c in collections)

        if collection_exists:
            logger.info(f"Collection already exists: {collection_name}")
            return False

        vector_size = model.get_sentence_embedding_dimension()
        logger.info(f"Creating collection with vector size: {vector_size}")

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

        # Create indexes
        client.create_payload_index(
            collection_name=collection_name,
            field_name="standard_name",
            field_schema=PayloadSchemaType.KEYWORD,
        )

        client.create_payload_index(
            collection_name=collection_name,
            field_name="aliases",
            field_schema=PayloadSchemaType.KEYWORD,
        )

        logger.info(f"Collection created successfully: {collection_name}")
        return True

    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise


def main():
    """Initialize TGT standard library collection."""
    try:
        logger.info("="*60)
        logger.info("TGT Standard Library Initialization")
        logger.info("="*60)

        # Get configuration
        config = get_config()
        logger.info(f"Connecting to Qdrant: {config['qdrant_url']}")
        logger.info(f"Collection name: {config['collection_name']}")
        logger.info(f"Embedding model: {config['embedding_model']}")

        # Initialize client and model
        client = QdrantClient(url=config['qdrant_url'])
        model = SentenceTransformer(config['embedding_model'])

        # Create collection
        logger.info("\nCreating collection...")
        created = create_collection(client, config['collection_name'], model)

        if created:
            logger.info("Collection created successfully!")
        else:
            logger.info("Collection already exists, skipping creation")

        # Import seed data if available
        seed_file = Path(__file__).parent.parent / "data" / "tgt_seeds.json"
        if seed_file.exists():
            logger.info(f"\nImporting seed data from: {seed_file}")
            import_seed_data(client, config['collection_name'], model, seed_file)
        else:
            logger.info(f"\nNo seed data found at: {seed_file}")
            logger.info("You can create seed data later and import it manually")

        # Show stats
        collection_info = client.get_collection(config['collection_name'])
        logger.info("\nCollection Statistics:")
        logger.info(f"  - Total entities: {collection_info.points_count}")
        logger.info(f"  - Vector size: {collection_info.config.params.vectors.size}")

        logger.info("\n" + "="*60)
        logger.info("Initialization completed successfully!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"\nInitialization failed: {e}", exc_info=True)
        sys.exit(1)


def import_seed_data(client: QdrantClient, collection_name: str, model: SentenceTransformer, seed_file: Path):
    """Import seed data from JSON file.

    Args:
        client: Qdrant client instance
        collection_name: Name of collection
        model: Embedding model
        seed_file: Path to seed data JSON file
    """
    import uuid
    from datetime import datetime
    from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

    try:
        with open(seed_file, 'r', encoding='utf-8') as f:
            seed_data = json.load(f)

        logger.info(f"Found {len(seed_data)} seed entities")

        imported_count = 0
        skipped_count = 0

        for entity in seed_data:
            standard_name = entity.get("standard_name")
            if not standard_name:
                logger.warning("Skipping entity without standard_name")
                skipped_count += 1
                continue

            # Check if entity already exists
            results = client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="standard_name", match=MatchValue(value=standard_name))]
                ),
                limit=1,
                with_payload=True,
            )

            if results[0]:
                logger.info(f"  - Skipping existing entity: {standard_name}")
                skipped_count += 1
                continue

            # Create entity
            try:
                # Generate vector
                text_to_embed = standard_name
                aliases = entity.get("aliases", [])
                if aliases:
                    text_to_embed += " " + " ".join(aliases[:3])

                vector = model.encode(text_to_embed).tolist()

                # Prepare payload
                now = datetime.utcnow().isoformat()
                payload = {
                    "standard_name": standard_name,
                    "full_name": entity.get("full_name", standard_name),
                    "aliases": aliases,
                    "verification_status": entity.get("verification_status", "auto_generated"),
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

                client.upsert(
                    collection_name=collection_name,
                    points=[point],
                )

                logger.info(f"  - Imported: {standard_name} (ID: {entity_id})")
                imported_count += 1
            except Exception as e:
                logger.error(f"  - Failed to import {standard_name}: {e}")
                skipped_count += 1

        logger.info(f"\nImport summary:")
        logger.info(f"  - Imported: {imported_count}")
        logger.info(f"  - Skipped: {skipped_count}")

    except Exception as e:
        logger.error(f"Failed to import seed data: {e}")
        raise


if __name__ == "__main__":
    main()

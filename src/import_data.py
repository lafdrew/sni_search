"""Data importer for SNI RAG system."""

import json
import uuid
from pathlib import Path
from typing import Optional
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
)

from src.config import settings


class SNIDataImporter:
    """Import SNI data from JSON files to Qdrant."""

    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
    ):
        """Initialize importer.

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
            print(f"Loading embedding model: {self.embedding_model_name}")
            self._model = SentenceTransformer(self.embedding_model_name)
        return self._model

    def create_collection(self, recreate: bool = False) -> None:
        """Create Qdrant collection.

        Args:
            recreate: If True, delete existing collection first
        """
        # Check if collection exists
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if exists:
            if recreate:
                print(f"Deleting existing collection: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
            else:
                print(f"Collection {self.collection_name} already exists")
                return

        # Get vector dimension from model
        vector_size = self.model.get_sentence_embedding_dimension()
        print(f"Creating collection with vector size: {vector_size}")

        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

        # Create payload indexes
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="domain",
            field_schema=PayloadSchemaType.KEYWORD,
        )

        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="sni",
            field_schema=PayloadSchemaType.KEYWORD,
        )

        print(f"Collection '{self.collection_name}' created successfully")

    def process_json_files(self, data_dir: str, batch_size: int = 100) -> int:
        """Process JSON files and import to Qdrant.

        Args:
            data_dir: Directory containing JSON files
            batch_size: Batch size for upsert operations

        Returns:
            Number of points imported
        """
        data_path = Path(data_dir)
        json_files = list(data_path.glob("**/*.json"))

        if not json_files:
            print(f"No JSON files found in {data_dir}")
            return 0

        print(f"Found {len(json_files)} JSON files")

        points = []
        total_imported = 0

        for json_file in tqdm(json_files, desc="Processing files"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading {json_file}: {e}")
                continue

            domain = data.get("domain")
            sni_list = data.get("sni_list", [])
            total_count = data.get("total_count", 0)
            detailed_info = data.get("detailed_info", [])
            collection_time = data.get("collection_time", "")

            # Create a point for each SNI
            for sni in sni_list:
                # Find detailed info for this SNI
                sni_detail = next(
                    (item for item in detailed_info if item.get("sni") == sni),
                    {},
                )

                # Generate vector
                vector = self.model.encode(sni).tolist()

                # Build point
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "sni": sni,
                        "domain": domain,
                        "total_count": total_count,
                        "all_snis": sni_list,
                        "timestamp": sni_detail.get("timestamp", ""),
                        "alpn_protocols": sni_detail.get("alpn_protocols", []),
                        "collection_time": collection_time,
                    },
                )
                points.append(point)

                # Batch upsert
                if len(points) >= batch_size:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points,
                    )
                    total_imported += len(points)
                    points = []

        # Upsert remaining points
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            total_imported += len(points)

        print(f"Imported {total_imported} SNI records to Qdrant")
        return total_imported

    def run(
        self,
        data_dir: str,
        recreate: bool = False,
        batch_size: int = 100,
    ) -> int:
        """Run complete import process.

        Args:
            data_dir: Directory containing JSON files
            recreate: If True, recreate collection
            batch_size: Batch size for upsert operations

        Returns:
            Number of points imported
        """
        print("Starting SNI data import...")

        # Create collection
        self.create_collection(recreate=recreate)

        # Process files
        count = self.process_json_files(data_dir, batch_size=batch_size)

        print("Import completed!")
        return count

    def get_stats(self) -> dict:
        """Get collection statistics.

        Returns:
            Collection statistics
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": info.points_count,
                "vector_size": info.config.params.vectors.size,
                "status": str(info.status),
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """Main entry point for data import."""
    import argparse

    parser = argparse.ArgumentParser(description="Import SNI data to Qdrant")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=settings.DATA_DIR,
        help="Directory containing JSON files",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection if exists",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for upsert operations",
    )
    parser.add_argument(
        "--qdrant-url",
        type=str,
        default=settings.QDRANT_URL,
        help="Qdrant server URL",
    )

    args = parser.parse_args()

    importer = SNIDataImporter(qdrant_url=args.qdrant_url)
    count = importer.run(
        data_dir=args.data_dir,
        recreate=args.recreate,
        batch_size=args.batch_size,
    )

    # Print stats
    stats = importer.get_stats()
    print("\nCollection stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

"""Download embedding model to local directory.

This script downloads the sentence-transformers embedding model to a local directory,
allowing offline usage and faster loading times.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import from src
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sentence_transformers import SentenceTransformer
from src.config import settings


def download_embedding_model(
    model_name: str = None,
    output_dir: str = None
):
    """Download embedding model to local directory.

    Args:
        model_name: Model name to download (default: from EMBEDDING_MODEL env var)
        output_dir: Local directory to save model (default: PROJECT_ROOT/data/models/embeddings)
    """
    # Use model from config if not specified
    if model_name is None:
        model_name = settings.EMBEDDING_MODEL

    # Use default output directory if not specified (relative to project root)
    if output_dir is None:
        output_dir = str(PROJECT_ROOT / "data" / "models" / "embeddings")

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"{'='*80}")
    print(f"Downloading Embedding Model")
    print(f"{'='*80}")
    print(f"Model:     {model_name}")
    print(f"Output:    {output_path.absolute()}")
    print(f"{'='*80}\n")

    try:
        # Download model
        print("Starting download...")
        model = SentenceTransformer(model_name)

        # Save to local directory
        print(f"\nSaving model to: {output_path.absolute()}")
        model.save(str(output_path))

        model_size = sum(
            f.stat().st_size for f in output_path.rglob('*') if f.is_file()
        ) / (1024 * 1024)  # Convert to MB

        print(f"\n{'='*80}")
        print(f"[SUCCESS] Model downloaded successfully!")
        print(f"{'='*80}")
        print(f"Model size: {model_size:.2f} MB")
        print(f"Location:   {output_path.absolute()}")
        print(f"{'='*80}\n")

        print("To use this local model, update your .env file:")
        print(f"EMBEDDING_MODEL={output_path.absolute()}")
        print("\nOr run with environment variable:")
        print(f"export EMBEDDING_MODEL={output_path.absolute()}\n")

        return True

    except Exception as e:
        print(f"\n[ERROR] Error downloading model: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download embedding model to local directory"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name to download (default: from EMBEDDING_MODEL env var)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: PROJECT_ROOT/data/models/embeddings)"
    )

    args = parser.parse_args()

    success = download_embedding_model(
        model_name=args.model,
        output_dir=args.output
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

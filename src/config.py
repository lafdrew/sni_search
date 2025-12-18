"""Configuration module for SNI RAG system."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from dotenv import load_dotenv

# Load .env file first with override=True to prioritize .env over system env vars
load_dotenv(override=True)


class Settings(BaseSettings):
    """Application settings."""

    # Qdrant Configuration
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "sni_domain_mapping"

    # Claude API Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_BASE_URL: Optional[str] = None

    # Model Configuration
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # LangSmith (optional)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_PROJECT: str = "sni-recognition"
    LANGCHAIN_API_KEY: Optional[str] = None

    # Data paths
    DATA_DIR: str = "result/results"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

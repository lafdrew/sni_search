"""Configuration module for SNI RAG system."""

import os
import yaml
import enum
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)


def load_yaml_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_file: Path to the YAML configuration file

    Returns:
        Dictionary containing the configuration
    """
    config_path = Path(config_file)
    if not config_path.exists():
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except Exception as e:
        print(f"Warning: Failed to load config file {config_file}: {e}")
        return {}


class SearchEngine(enum.Enum):
    TAVILY = "tavily"
    INFOQUEST = "infoquest"
    SEARCHAPI = "searchapi"
    DUCKDUCKGO = "duckduckgo"
    BRAVE_SEARCH = "brave_search"
    ARXIV = "arxiv"
    SEARX = "searx"
    WIKIPEDIA = "wikipedia"
    SERPER = "serper"


class CrawlerEngine(enum.Enum):
    JINA = "jina"
    INFOQUEST = "infoquest"


class RAGProvider(enum.Enum):
    DIFY = "dify"
    RAGFLOW = "ragflow"
    VIKINGDB_KNOWLEDGE_BASE = "vikingdb_knowledge_base"
    MOI = "moi"
    MILVUS = "milvus"
    QDRANT = "qdrant"


SELECTED_SEARCH_ENGINE = os.getenv("SEARCH_API", SearchEngine.DUCKDUCKGO.value)
SELECTED_RAG_PROVIDER = os.getenv("RAG_PROVIDER")


class Settings(BaseSettings):
    """Application settings - loaded from .env file."""

    # Qdrant Configuration
    QDRANT_URL: str
    QDRANT_COLLECTION: str

    # TGT Standard Library Configuration
    QDRANT_TGT_COLLECTION: str = "tgt_standard_library"
    TGT_LIBRARY_ENABLED: bool = True
    TGT_VECTOR_THRESHOLD: float = 0.75
    TGT_LLM_CONFIDENCE_THRESHOLD: float = 0.8

    # LLM Provider Configuration
    LLM_PROVIDER: str = "claude"

    # Claude API Configuration
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_BASE_URL: Optional[str] = None

    # Model Configuration
    CLAUDE_MODEL: Optional[str] = None
    EMBEDDING_MODEL: str

    # OpenAI API Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: Optional[str] = None

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 9000

    # LangSmith (optional)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_PROJECT: str = "sni-recognition"
    LANGCHAIN_API_KEY: Optional[str] = None

    # Data paths
    DATA_DIR: str

    # Search and Crawler Configuration
    SEARCH_API: str
    MAX_SEARCH_RESULTS: int = 5

    CRAWLER_ENGINE: str
    CRAWLER_TIMEOUT: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode='after')
    def validate_llm_config(self) -> 'Settings':
        """Validate LLM configuration completeness."""
        provider = self.LLM_PROVIDER.lower()

        if provider == "claude":
            if not self.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=claude")
            if not self.CLAUDE_MODEL:
                raise ValueError("CLAUDE_MODEL is required when LLM_PROVIDER=claude")
        elif provider == "openai":
            if not self.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
            if not self.OPENAI_MODEL:
                raise ValueError("OPENAI_MODEL is required when LLM_PROVIDER=openai")
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider}. Must be 'claude' or 'openai'")

        return self


settings = Settings()

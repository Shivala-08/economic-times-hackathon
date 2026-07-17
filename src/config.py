"""AI for Industrial Knowledge Intelligence — Configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Industrial Knowledge Intelligence"
    app_version: str = "0.1.0"
    debug: bool = True

    # Paths
    project_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    corpus_dir: Path = data_dir / "corpus"
    benchmarks_dir: Path = data_dir / "benchmarks"

    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # ChromaDB
    chroma_persist_dir: str = str(
        Path(__file__).resolve().parent.parent / "data" / "chroma_db"
    )
    chroma_collection: str = "industrial_docs"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # RAG
    top_k: int = 5

    # LLM
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    llm_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024

    # spaCy
    spacy_model: str = "en_core_web_sm"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

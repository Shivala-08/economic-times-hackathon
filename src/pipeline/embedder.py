"""Text embedding using sentence-transformers."""

from sentence_transformers import SentenceTransformer
from loguru import logger

from src.config import settings


from functools import lru_cache

class TextEmbedder:
    """Generates embeddings for text chunks using sentence-transformers."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.dim = settings.embedding_dim
        logger.info(f"Embedding model loaded. Dimension: {self.dim}")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    @lru_cache(maxsize=128)
    def _cached_embed_query(self, query: str) -> list[float]:
        embedding = self.model.encode([query])
        return embedding[0].tolist()

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a single query."""
        return self._cached_embed_query(query)

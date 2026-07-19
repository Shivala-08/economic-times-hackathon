"""ChromaDB vector store wrapper for industrial documents."""

from pathlib import Path
import chromadb
from loguru import logger

from src.config import settings


class VectorStore:
    """Manages ChromaDB collections for document embeddings."""

    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or settings.chroma_collection
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"VectorStore initialized: collection='{self.collection_name}'")

    def add_documents(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]):
        """Add documents with embeddings to the collection."""
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(ids)} documents to vector store")

    def query(self, query_embedding: list[float], n_results: int = 5, where: dict = None) -> dict:
        """Query the collection for similar documents."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )
        return results

    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count()

    def delete_all(self):
        """Delete all documents from the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning("All documents deleted from vector store")

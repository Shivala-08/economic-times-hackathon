"""Text chunking for document ingestion."""

import re
from loguru import logger

from src.config import settings


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    doc_id: str = "unknown",
) -> list[dict]:
    """Split text into overlapping chunks.

    Args:
        text: Raw document text.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between consecutive chunks.
        doc_id: Document identifier for metadata.

    Returns:
        List of chunk dicts with id, text, and metadata.
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    if len(text) == 0:
        return []

    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence boundary within last 20% of chunk
            look_back = max(start + chunk_size - int(chunk_size * 0.2), start)
            last_period = text.rfind('. ', look_back, end + 50)
            if last_period > start:
                end = last_period + 1

        chunk_text_str = text[start:end].strip()

        if chunk_text_str:
            chunks.append({
                "id": f"{doc_id}_chunk_{chunk_idx:04d}",
                "text": chunk_text_str,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_index": chunk_idx,
                    "start_char": start,
                    "end_char": end,
                },
            })
            chunk_idx += 1

        start = end - chunk_overlap if end < len(text) else len(text)

    logger.info(f"Chunked document '{doc_id}': {len(chunks)} chunks from {len(text)} chars")
    return chunks

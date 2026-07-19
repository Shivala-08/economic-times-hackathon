"""Text chunking for document ingestion using token-based segmentation."""

import re
from loguru import logger

from src.config import settings

_tokenizer = None


def get_tokenizer():
    """Lazy load tokenizer corresponding to the embedding model."""
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer
        model_name = settings.embedding_model
        if "/" not in model_name:
            model_name = f"sentence-transformers/{model_name}"
        logger.info(f"Loading chunker tokenizer: {model_name}")
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
    return _tokenizer


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    doc_id: str = "unknown",
) -> list[dict]:
    """Split text into overlapping chunks based on token counts.

    Args:
        text: Raw document text.
        chunk_size: Target chunk size in tokens.
        chunk_overlap: Overlap in tokens between consecutive chunks.
        doc_id: Document identifier for metadata.

    Returns:
        List of chunk dicts with id, text, and metadata.
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    # Normalize horizontal whitespace and consecutive newlines, preserving layout
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    text = re.sub(r'\n+', '\n', text).strip()

    if not text:
        return []

    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(text, add_special_tokens=False)

    if not tokens:
        return []

    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = tokenizer.decode(chunk_tokens, clean_up_tokenization_spaces=True).strip()

        if chunk_text_str:
            chunks.append({
                "id": f"{doc_id}_chunk_{chunk_idx:04d}",
                "text": chunk_text_str,
                "metadata": {
                    "doc_id": doc_id,
                    "chunk_index": chunk_idx,
                    "start_char": start,  # Store token start index as metadata
                    "end_char": end,      # Store token end index as metadata
                },
            })
            chunk_idx += 1

        # Move window forward
        start = end - chunk_overlap if end < len(tokens) else len(tokens)

    logger.info(f"Chunked document '{doc_id}': {len(chunks)} chunks from {len(tokens)} tokens")
    return chunks

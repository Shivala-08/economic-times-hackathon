"""Ingestion pipeline to parse, chunk, embed, and store documents in ChromaDB.

Also performs entity extraction and knowledge graph construction.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from loguru import logger

from src.config import settings
from src.pipeline.parser import parse_file
from src.pipeline.chunker import chunk_text
from src.pipeline.embedder import TextEmbedder
from src.pipeline.extractor import extract_entities
from src.storage.chroma_store import VectorStore
from src.graph.knowledge_graph import get_knowledge_graph


class IngestionPipeline:
    """Orchestrates parsing, chunking, embedding, entity extraction, and storing files."""

    def __init__(self):
        self.embedder = TextEmbedder()
        self.store = VectorStore()
        self.kg = get_knowledge_graph()
        self.registry_path = settings.data_dir / "documents.json"
        self.uploads_dir = settings.corpus_dir / "uploads"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def _load_registry(self) -> dict:
        """Load document metadata registry from disk."""
        if not self.registry_path.exists():
            return {}
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load document registry: {e}")
            return {}

    def _save_registry(self, registry: dict):
        """Save document metadata registry to disk."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save document registry: {e}")

    def ingest_file(self, file_path: Path, copy_to_uploads: bool = False) -> dict:
        """Ingest a single file (PDF, DOCX, CSV, TXT) into the vector store.

        Args:
            file_path: Path to the file.
            copy_to_uploads: If True, copies the file to the uploads directory.

        Returns:
            Dictionary with status, doc_id, chunk_count.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = file_path.name
        doc_id = filename
        suffix = file_path.suffix.lower()

        logger.info(f"Starting ingestion for file: {filename}")

        # 1. Parse the file
        parsed_records = parse_file(file_path)

        # 2. Chunking
        chunks = []
        if suffix == ".csv":
            # For CSV, each row returned from parse_file is already a chunk
            chunks = parsed_records
        else:
            # For PDF, DOCX, TXT, chunk the full text content
            full_text = parsed_records[0]["text"]
            raw_chunks = chunk_text(full_text, doc_id=doc_id)
            for rc in raw_chunks:
                chunks.append({
                    "id": rc["id"],
                    "text": rc["text"],
                    "metadata": rc["metadata"]
                })

        if not chunks:
            logger.warning(f"No chunks created for {filename}. Skipping vector storage.")
            return {"doc_id": doc_id, "status": "skipped", "chunk_count": 0}

        # 3. Embed text chunks
        texts_to_embed = [c["text"] for c in chunks]
        embeddings = self.embedder.embed_texts(texts_to_embed)

        # 4. Save to ChromaDB
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        self.store.add_documents(ids, embeddings, texts_to_embed, metadatas)

        # 5. Entity extraction & knowledge graph construction
        try:
            # Combine all chunk texts for entity extraction
            all_text = "\n\n".join(c["text"] for c in chunks)
            # Also include metadata from CSV rows
            combined_metadata = {}
            if suffix == ".csv" and chunks:
                # Merge metadata from all CSV rows
                for c in chunks:
                    for k, v in c.get("metadata", {}).items():
                        if v and k not in combined_metadata:
                            combined_metadata[k] = v

            entities = extract_entities(all_text, combined_metadata)
            entity_count = sum(len(v) for v in entities.values())
            logger.info(f"Extracted {entity_count} entities from {filename}")

            # Add to knowledge graph
            self.kg.add_document_entities(doc_id, all_text, entities, combined_metadata)
        except Exception as e:
            logger.error(f"Entity extraction failed for {filename}: {e}")
            entities = {}
            entity_count = 0

        # 6. Persist file copy in data/corpus/uploads if requested
        dest_path = file_path
        if copy_to_uploads and file_path.resolve().parent != self.uploads_dir.resolve():
            dest_path = self.uploads_dir / filename
            shutil.copy2(file_path, dest_path)
            logger.info(f"Copied uploaded file to persistent storage: {dest_path}")

        # Determine relative path for registry storage
        try:
            rel_path = str(dest_path.relative_to(settings.project_root))
        except ValueError:
            rel_path = str(dest_path)

        # 7. Update document registry
        registry = self._load_registry()
        registry[doc_id] = {
            "doc_id": doc_id,
            "filename": filename,
            "file_path": rel_path,
            "type": suffix.lstrip("."),
            "upload_date": datetime.now().isoformat(),
            "chunk_count": len(chunks),
            "entities_found": entity_count,
        }
        self._save_registry(registry)

        # Save knowledge graph after each document
        self.kg.save()

        logger.info(f"Successfully ingested {filename} ({len(chunks)} chunks, {entity_count} entities)")
        return {
            "doc_id": doc_id,
            "status": "success",
            "chunk_count": len(chunks),
            "entities_found": entity_count,
        }

    def list_documents(self) -> list[dict]:
        """List all documents currently tracked in the registry."""
        registry = self._load_registry()
        return list(registry.values())

    def initialize_corpus(self) -> dict:
        """Clear vector database, knowledge graph, and re-ingest all corpus files.

        Scans:
        - data/corpus/real/ (Regulatory PDFs/TXTs)
        - data/corpus/synthetic/ (CSV Work Orders/Permits/Inspections)
        - data/corpus/uploads/ (User uploaded documents)
        """
        logger.info("Initializing vector store corpus...")

        # 1. Clear database and knowledge graph
        self.store.delete_all()
        self.kg.clear()
        if self.registry_path.exists():
            try:
                os.remove(self.registry_path)
            except Exception as e:
                logger.error(f"Failed to remove registry file: {e}")

        # 2. Find files in real/ and synthetic/
        real_dir = settings.corpus_dir / "real"
        synth_dir = settings.corpus_dir / "synthetic"
        uploads_dir = settings.corpus_dir / "uploads"

        dirs_to_scan = [real_dir, synth_dir, uploads_dir]
        ingested_count = 0
        total_chunks = 0
        details = []

        for d in dirs_to_scan:
            if not d.exists():
                continue
            for item in d.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    # Check for supported extensions
                    if item.suffix.lower() in [".txt", ".pdf", ".docx", ".csv"]:
                        try:
                            # Do not need to copy during initialization since they are already in the corpus directories
                            res = self.ingest_file(item, copy_to_uploads=False)
                            if res["status"] == "success":
                                ingested_count += 1
                                total_chunks += res["chunk_count"]
                                details.append(res)
                        except Exception as e:
                            logger.error(f"Error ingesting file {item.name}: {e}")

        # Save knowledge graph once after all files are ingested
        self.kg.save()

        logger.info(f"Corpus initialized successfully: {ingested_count} files, {total_chunks} chunks")
        return {
            "files_ingested": ingested_count,
            "total_chunks": total_chunks,
            "details": details
        }


if __name__ == "__main__":
    # Let's support running the script directly to initialize the corpus
    pipeline = IngestionPipeline()
    res = pipeline.initialize_corpus()
    print(f"Ingestion completed. Files: {res['files_ingested']}, Chunks: {res['total_chunks']}")

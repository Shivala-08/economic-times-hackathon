"""Industrial Knowledge Intelligence — Main API Application."""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from src.config import settings
from src.pipeline.ingest import IngestionPipeline
from src.pipeline.embedder import TextEmbedder
from src.pipeline.extractor import extract_entities
from src.storage.chroma_store import VectorStore
from src.graph.knowledge_graph import get_knowledge_graph

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="RAG-powered industrial knowledge intelligence system with vector search + knowledge graph.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Schema for incoming RAG queries."""
    question: str
    top_k: Optional[int] = settings.top_k


class QueryResponse(BaseModel):
    """Schema for RAG query response."""
    answer: str
    sources: List[dict]
    confidence: str
    entities_used: List[str] = []


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "version": settings.app_version}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }


# --- Knowledge Graph Endpoints ---

@app.get("/graph")
async def get_graph(max_nodes: int = Query(default=500, le=2000)):
    """Get the full knowledge graph as nodes/edges JSON for visualization."""
    try:
        kg = get_knowledge_graph()
        return kg.to_json(max_nodes=max_nodes)
    except Exception as e:
        logger.error(f"Error fetching knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/entity/{entity_id}")
async def get_entity_subgraph(entity_id: str, depth: int = Query(default=1, le=3)):
    """Get subgraph centered on one entity (e.g. one equipment tag)."""
    try:
        kg = get_knowledge_graph()
        return kg.get_entity_neighbors(entity_id, depth=depth)
    except Exception as e:
        logger.error(f"Error fetching entity subgraph for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entities")
async def get_entities():
    """List all extracted entities grouped by type."""
    try:
        kg = get_knowledge_graph()
        entities_by_type = kg.get_entities_by_type()
        stats = kg.get_stats()
        return {
            "entities": entities_by_type,
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"Error fetching entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Ingestion Endpoints ---

@app.post("/ingest/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and ingest one or more documents (PDF, DOCX, CSV, TXT)."""
    pipeline = IngestionPipeline()
    temp_dir = settings.data_dir / "temp_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    for file in files:
        safe_filename = Path(file.filename).name
        temp_file_path = temp_dir / safe_filename
        try:
            # Save file temporarily to disk
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Ingest file (it will copy to uploads persistently)
            logger.info(f"Uploading and ingesting: {safe_filename}")
            res = pipeline.ingest_file(temp_file_path, copy_to_uploads=True)
            results.append(res)
        except Exception as e:
            logger.error(f"Failed to ingest uploaded file {safe_filename}: {e}")
            results.append({"doc_id": safe_filename, "status": "error", "error": str(e)})
        finally:
            # Clean up temporary file
            if temp_file_path.exists():
                os.remove(temp_file_path)
                
    return {"results": results}


@app.post("/ingest/initialize")
async def initialize_corpus():
    """Clear database and ingest all files in default corpus directories."""
    try:
        pipeline = IngestionPipeline()
        stats = pipeline.initialize_corpus()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Error during corpus initialization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize corpus: {str(e)}")


# --- Document Information Endpoints ---

@app.get("/documents")
async def list_documents():
    """List all ingested documents with metadata."""
    pipeline = IngestionPipeline()
    return pipeline.list_documents()


@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get full details and chunks for a specific document."""
    store = VectorStore()
    
    # Query ChromaDB for all chunks where doc_id matches
    # Use ChromaDB client collection.get
    try:
        results = store.collection.get(where={"doc_id": doc_id})
        
        if not results or not results["ids"]:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found or has no chunks.")
            
        chunks = []
        for i in range(len(results["ids"])):
            chunks.append({
                "chunk_id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i]
            })
            
        # Sort chunks by chunk_index to ensure text is in order
        chunks.sort(key=lambda x: x["metadata"].get("chunk_index", 0))
        
        return {
            "doc_id": doc_id,
            "filename": doc_id,
            "chunk_count": len(chunks),
            "chunks": chunks
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Query Endpoint (Mock LLM / Vector-Search-Only for Day 2) ---

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Main RAG query endpoint. Performs similarity search + graph traversal."""
    try:
        logger.info(f"Received query: '{request.question}'")
        embedder = TextEmbedder()
        store = VectorStore()
        kg = get_knowledge_graph()
        
        # Check if vector store has any documents
        if store.count() == 0:
            return QueryResponse(
                answer="No documents found in the database. Please ingest some documents first via the UI or /ingest/initialize endpoint.",
                sources=[],
                confidence="Low",
                entities_used=[]
            )
            
        # 1. Embed query
        query_embedding = embedder.embed_query(request.question)
        
        # 2. Search ChromaDB (vector path)
        top_k = request.top_k or settings.top_k
        results = store.query(query_embedding, n_results=top_k)
        
        # 3. Extract entities from query for graph traversal
        query_entities = extract_entities(request.question)
        graph_context = []
        entities_used = []
        
        # Traverse graph for each found entity
        for eq in query_entities.get("equipment", []):
            neighbors = kg.get_entity_neighbors(eq, depth=1)
            if neighbors.get("neighbors"):
                entities_used.append(eq)
                for n in neighbors["neighbors"]:
                    graph_context.append(f"{eq} --[{n['relation']}]--> {n['id']} ({n['type']})")

        for reg in query_entities.get("regulations", []):
            neighbors = kg.get_entity_neighbors(reg, depth=1)
            if neighbors.get("neighbors"):
                entities_used.append(reg)
                for n in neighbors["neighbors"]:
                    graph_context.append(f"{reg} --[{n['relation']}]--> {n['id']} ({n['type']})")

        # 4. Process vector search results
        sources = []
        best_chunks = []
        
        if results and results["documents"] and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                doc_text = results["documents"][0][i]
                metadata = results["metadatas"][0][i]
                dist = results["distances"][0][i]
                
                src_doc = metadata.get("doc_id", "unknown")
                rec_id = metadata.get("record_id", "")
                
                citation = src_doc
                if rec_id:
                    citation = f"{src_doc} ({rec_id})"
                    
                sources.append({
                    "doc_id": src_doc,
                    "record_id": rec_id,
                    "excerpt": doc_text,
                    "distance": dist,
                    "citation": citation
                })
                
                if i < 2:
                    best_chunks.append(f"- From {citation}:\n  \"{doc_text[:300]}...\"")
                    
        # 5. Generate answer
        if best_chunks:
            answer_snippets = "\n\n".join(best_chunks)
            graph_info = ""
            if graph_context:
                graph_info = f"\n\n**Graph relationships found:**\n" + "\n".join(f"• {ctx}" for ctx in graph_context[:10])
            
            answer = (
                f"**[RAG Engine — Vector Search + Knowledge Graph]**\n\n"
                f"{answer_snippets}{graph_info}\n\n"
                f"*Note: Full LLM generation scheduled for Day 4. Currently showing vector search results with graph augmentation.*"
            )
            confidence = "High" if entities_used else "Medium"
        else:
            answer = "No matches found in the vector database for your query."
            confidence = "Low"
            
        return QueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            entities_used=entities_used
        )
    except Exception as e:
        logger.error(f"Error querying RAG engine: {e}")
        raise HTTPException(status_code=500, detail=str(e))

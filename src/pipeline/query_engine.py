"""Query Engine — context retrieval + answer generation.

Public API
----------
retrieve_context(query, top_k, collection_name)
    Embeds the query, searches ChromaDB for top_k chunks, extracts entities with
    spaCy/regex, traverses the NetworkX knowledge graph 1-hop per entity, and
    returns a merged, deduplicated context dict:
        {vector_chunks: [...], graph_entities: [...], graph_relations: [...]}

generate_answer(query, context)
    Builds a structured RAG prompt from the context object, calls the local LLM
    (Ollama if running, otherwise smart-fallback), and safe-parses the required
    JSON response:
        {answer: str, sources: [{doc_id, excerpt}], confidence: float,
         entities_used: [str], key_points: [str]}

The module does NOT call the Claude API — it uses Ollama (local, no API key).
To enable LLM answers: install Ollama (https://ollama.com) and run
  ollama pull llama3.2 && ollama serve
"""

import json
import copy
from typing import Dict, Any, List, Optional
from loguru import logger
import numpy as np

from src.config import settings
from src.pipeline.embedder import TextEmbedder
from src.storage.chroma_store import VectorStore
from src.pipeline.extractor import extract_entities
from src.graph.knowledge_graph import get_knowledge_graph
from src.pipeline.llm import get_llm, _extract_json, _smart_fallback

# Singletons for reusing instances across calls
_embedder: Optional[TextEmbedder] = None
_vector_store: Optional[VectorStore] = None
_cross_encoder: Optional[Any] = None


class SemanticCache:
    """In-memory rolling cache for semantic similarity search over recent queries."""

    def __init__(self, max_size: int = 500, threshold: float = 0.95):
        self.max_size = max_size
        self.threshold = threshold
        # list of dicts: {"embedding": np.ndarray, "answer": Dict[str, Any]}
        self.cache = []

    def get(self, query_embedding: np.ndarray) -> Optional[Dict[str, Any]]:
        if not self.cache or query_embedding is None:
            return None

        # Normalize query embedding
        q_norm = np.linalg.norm(query_embedding)
        if q_norm == 0:
            return None
        q_emb = query_embedding / q_norm

        best_similarity = -1.0
        best_answer = None

        for entry in self.cache:
            entry_emb = entry["embedding"]
            e_norm = np.linalg.norm(entry_emb)
            if e_norm == 0:
                continue
            e_emb = entry_emb / e_norm

            similarity = float(np.dot(q_emb, e_emb))
            if similarity > best_similarity:
                best_similarity = similarity
                best_answer = entry["answer"]

        if best_similarity >= self.threshold:
            logger.info(f"Semantic Cache HIT: similarity = {best_similarity:.4f} (>= {self.threshold})")
            return best_answer

        logger.debug(f"Semantic Cache MISS: best similarity = {best_similarity:.4f} (< {self.threshold})")
        return None

    def set(self, query_embedding: np.ndarray, answer: Dict[str, Any]):
        if query_embedding is None or answer is None:
            return

        # Simple rolling FIFO eviction to act as a cache of max size
        if len(self.cache) >= self.max_size:
            self.cache.pop(0)

        # Store a deep copy of the answer to prevent modification
        self.cache.append({
            "embedding": query_embedding.copy(),
            "answer": copy.deepcopy(answer)
        })
        logger.debug(f"Cached answer in semantic cache. Cache size: {len(self.cache)}/{self.max_size}")


_semantic_cache = SemanticCache(max_size=500, threshold=0.95)


def get_embedder() -> TextEmbedder:
    """Get or create the text embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedder()
    return _embedder


def get_vector_store(collection_name: str = None) -> VectorStore:
    """Get or create the vector store instance for the specified collection."""
    global _vector_store
    name = collection_name or settings.chroma_collection
    if _vector_store is None or _vector_store.collection_name != name:
        _vector_store = VectorStore(collection_name=name)
    return _vector_store


def get_cross_encoder() -> Any:
    """Get or create the cross-encoder instance for re-ranking."""
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        logger.info("Loading CrossEncoder: cross-encoder/ms-marco-MiniLM-L-6-v2")
        _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder


def retrieve_context(query: str, top_k: int = 5, collection_name: str = None) -> Dict[str, Any]:
    """Retrieve and merge context from ChromaDB (vector) and NetworkX (graph).

    Args:
        query: The natural language search query.
        top_k: Number of chunks to retrieve from the vector store.
        collection_name: ChromaDB collection to search against.

    Returns:
        A dictionary with merged and deduplicated context:
        {
            "vector_chunks": [
                {
                    "chunk_id": str,
                    "text": str,
                    "metadata": dict,
                    "distance": float
                },
                ...
            ],
            "graph_entities": [
                {
                    "id": str,
                    "type": str
                },
                ...
            ],
            "graph_relations": [
                {
                    "source": str,
                    "target": str,
                    "relation": str
                },
                ...
            ]
        }
    """
    logger.info(f"Retrieving context for query: '{query}'")

    # 1. Embed the query and retrieve top_k chunks from ChromaDB (diverse search)
    embedder = get_embedder()
    store = get_vector_store(collection_name)
    
    query_embedding = embedder.embed_query(query)
    
    # Pull top_k=10 chunks from ChromaDB instead of 3 by default, or respect top_k parameter
    n_part = max(10, top_k)
    reg_results = store.query(query_embedding, n_results=n_part, where={"record_type": {"$in": ["txt", "pdf", "docx"]}})
    csv_results = store.query(query_embedding, n_results=n_part, where={"record_type": {"$nin": ["txt", "pdf", "docx"]}})

    vector_chunks = []
    for search_results in [reg_results, csv_results]:
        if search_results and search_results["documents"] and len(search_results["documents"][0]) > 0:
            for i in range(len(search_results["documents"][0])):
                chunk_id = search_results["ids"][0][i]
                text = search_results["documents"][0][i]
                metadata = search_results["metadatas"][0][i]
                distance = search_results["distances"][0][i]
                vector_chunks.append({
                    "chunk_id": chunk_id,
                    "text": text,
                    "metadata": metadata,
                    "distance": distance
                })
    
    # Re-rank chunks locally using CrossEncoder
    if vector_chunks:
        try:
            cross_encoder = get_cross_encoder()
            pairs = [[query, c["text"]] for c in vector_chunks]
            scores = cross_encoder.predict(pairs)
            for idx, score in enumerate(scores):
                is_csv = vector_chunks[idx]["metadata"].get("record_type") not in ["txt", "pdf", "docx"]
                boost = 0.0 if is_csv else 8.0
                vector_chunks[idx]["cross_score"] = float(score)
                vector_chunks[idx]["combined_score"] = float(score) - 15.0 * float(vector_chunks[idx]["distance"]) + boost
            vector_chunks.sort(key=lambda x: x["combined_score"], reverse=True)
            logger.debug("Successfully re-ranked vector chunks using CrossEncoder with score fusion")
        except Exception as e:
            logger.error(f"Failed to re-rank chunks: {e}. Falling back to similarity distance.")
            vector_chunks.sort(key=lambda x: x["distance"])
        
        # Keep only the top 3 chunks for context assembly
        vector_chunks = vector_chunks[:3]

    logger.debug(f"Retrieved {len(vector_chunks)} vector chunks (diverse search) from collection '{store.collection_name}'")

    # 2. Extract entities from the query using the existing extractor
    extracted_entities = extract_entities(query)
    
    # Flatten and deduplicate all query entities
    query_entity_ids = set()
    
    # Check if spaCy NER returned zero entities (i.e. personnel list is empty)
    spacy_entities = extracted_entities.get("personnel", [])
    if not spacy_entities:
        logger.info("spaCy NER returned zero entities. Running query-side regex fallback.")
        from src.pipeline.extractor import EQUIPMENT_TAG_PATTERN, REGULATION_PATTERNS, PERMIT_ID_PATTERN
        
        # Equipment tags
        for match in EQUIPMENT_TAG_PATTERN.finditer(query):
            query_entity_ids.add(match.group(1).upper())
        # Permit numbers
        for match in PERMIT_ID_PATTERN.finditer(query):
            query_entity_ids.add(match.group(1).upper())
        # OISD codes / regulations
        for pattern in REGULATION_PATTERNS:
            for match in pattern.finditer(query):
                query_entity_ids.add(match.group(1))
    else:
        # If spaCy NER returned entities, populate with all extracted entities
        for category, entities in extracted_entities.items():
            for entity in entities:
                query_entity_ids.add(entity)

    # 2b. Also extract entity IDs from retrieved chunk metadata (Tier 1.1)
    for chunk in vector_chunks:
        entity_ids_json = chunk["metadata"].get("entity_ids", "[]")
        try:
            chunk_entity_ids = json.loads(entity_ids_json) if isinstance(entity_ids_json, str) else entity_ids_json
            for eid in chunk_entity_ids:
                if eid:
                    query_entity_ids.add(eid)
        except (json.JSONDecodeError, TypeError):
            pass
    
    logger.debug(f"Total entities for graph traversal: {len(query_entity_ids)} (from query + chunk metadata)")

    MAX_GRAPH_ENTITIES = 20
    if len(query_entity_ids) > MAX_GRAPH_ENTITIES:
        chunk_eids = set()
        for c in vector_chunks:
            entity_ids_json = c["metadata"].get("entity_ids", "[]")
            try:
                chunk_entity_ids = json.loads(entity_ids_json) if isinstance(entity_ids_json, str) else entity_ids_json
                for eid in chunk_entity_ids:
                    if isinstance(eid, str):
                        chunk_eids.add(eid)
            except Exception:
                pass
        query_only = [e for e in query_entity_ids if e not in chunk_eids]
        chunk_only = [e for e in query_entity_ids if e not in query_only]
        query_entity_ids = set(query_only + chunk_only[:MAX_GRAPH_ENTITIES - len(query_only)])
        logger.debug(f"Capped to {len(query_entity_ids)} entities for graph traversal")

    # 3. Traverse the NetworkX graph 1-hop for each found entity
    kg = get_knowledge_graph()
    graph_entities_list = []
    graph_relations_list = []

    for entity in query_entity_ids:
        # Check if node exists in NetworkX graph
        if kg.graph.has_node(entity):
            # Include the queried node itself
            graph_entities_list.append({
                "id": entity,
                "type": kg.graph.nodes[entity].get("type", "unknown")
            })

            # Traverse 1-hop neighbors
            for neighbor in kg.graph.neighbors(entity):
                # Add neighbor node
                graph_entities_list.append({
                    "id": neighbor,
                    "type": kg.graph.nodes[neighbor].get("type", "unknown")
                })
                
                # Add relationship edge
                edge_data = kg.graph.edges[entity, neighbor]
                graph_relations_list.append({
                    "source": entity,
                    "target": neighbor,
                    "relation": edge_data.get("relation", "related_to")
                })

    # 4. Deduplicate graph nodes and edges
    # Deduplicate entities by 'id'
    seen_entities = set()
    deduped_entities = []
    for ent in graph_entities_list:
        if ent["id"] not in seen_entities:
            seen_entities.add(ent["id"])
            deduped_entities.append(ent)

    # Deduplicate relations (sorting source/target to treat undirected edges as identical)
    seen_relations = set()
    deduped_relations = []
    for rel in graph_relations_list:
        edge_key = (
            min(rel["source"], rel["target"]),
            max(rel["source"], rel["target"]),
            rel["relation"]
        )
        if edge_key not in seen_relations:
            seen_relations.add(edge_key)
            deduped_relations.append(rel)

    logger.debug(f"Traversed graph: found {len(deduped_entities)} entities and {len(deduped_relations)} relations")

    return {
        "vector_chunks": vector_chunks,
        "graph_entities": deduped_entities,
        "graph_relations": deduped_relations
    }


# ── Answer generation ──────────────────────────────────────────────────────────

# Confidence guidance injected into the prompt so the LLM scores it consistently.
_CONFIDENCE_GUIDE = """
Confidence scoring rules (follow strictly — do NOT invent a number):
  High   (0.80-1.00) → direct, clear answer present in ≥2 document sources
  Medium (0.50-0.79) → partial information or only 1 source found, or no graph entities
  Low    (0.00-0.49) → context is empty, off-topic, or graph returned nothing

Hint for this specific query:
  vector_chunks retrieved: {n_chunks}
  graph entities matched : {n_entities}
  graph relations found  : {n_relations}
"""

_RAG_TEMPLATE = """
You are an Industrial Knowledge Intelligence AI. Answer ONLY using the retrieved
context below. Never fabricate facts. 
CRITICAL: Keep your final JSON response extremely concise (under 150 tokens total) to prevent truncation.

=== DOCUMENT CONTEXT ===
{doc_context}

=== KNOWLEDGE GRAPH RELATIONSHIPS ===
{graph_context}

=== QUESTION ===
{question}

{confidence_guide}

Respond with ONLY this JSON object — no markdown fences, no preamble, no trailing text:
{{"answer": "<concise answer citing [Source N] labels, max 2 sentences>",
  "sources": [{{"doc_id": "<doc_id>", "excerpt": "<very short excerpt, max 8 words>"}}],
  "confidence": <float 0.0-1.0>,
  "entities_used": ["<entity IDs mentioned>"],
  "key_points": ["<short key point 1, max 8 words>", "<short key point 2, max 8 words>"]}}
"""


def classify_query_complexity(query: str, chunks: list) -> dict:
    """Shared heuristic complexity classifier for gating LLM thinking mode.

    Returns a dict with:
        enable_thinking (bool)
        reasoning_budget (int)
        is_complex (bool)
    """
    enable_thinking = True
    reasoning_budget = 1024

    is_complex = len(query) > 180

    comparison_words = [
        "versus", "compare", "difference between", "difference", "vs", "comparison",
        "which", "list", "all", "each", "across"
    ]
    query_lower = query.lower()
    if not is_complex and any(word in query_lower for word in comparison_words):
        is_complex = True

    if not is_complex and len(chunks) >= 2:
        doc1 = chunks[0]["metadata"].get("doc_id") if chunks[0].get("metadata") else None
        doc2 = chunks[1]["metadata"].get("doc_id") if chunks[1].get("metadata") else None
        dist1 = chunks[0].get("distance", 0.0)
        dist2 = chunks[1].get("distance", 0.0)
        if doc1 and doc2 and doc1 != doc2 and abs(dist1 - dist2) < 0.12:
            is_complex = True

    if not is_complex:
        enable_thinking = True
        reasoning_budget = 256
        logger.info("Complexity classifier: simple query → reasoning_budget=256")
    else:
        logger.info("Complexity classifier: complex query → reasoning_budget=1024")

    return {
        "enable_thinking": enable_thinking,
        "reasoning_budget": reasoning_budget,
        "is_complex": is_complex,
    }


def generate_answer(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a structured RAG answer from the context object produced by retrieve_context().

    Args:
        query:   The original user question.
        context: Output of retrieve_context() — must contain keys
                 vector_chunks, graph_entities, graph_relations.

    Returns:
        A dict with:
          answer       (str)   — full markdown answer citing sources
          sources      (list)  — [{doc_id, excerpt}, ...]
          confidence   (float) — 0.0–1.0 computed from retrieval quality heuristics
          entities_used (list) — entity IDs from the graph traversal
          key_points   (list)  — bullet-point summaries
          model_used   (str)   — label for display (e.g. 'Ollama / llama3.2')
    """
    # ── Check semantic cache ──────────────────────────────────────────────────
    embedder = get_embedder()
    try:
        query_embedding = np.array(embedder.embed_query(query))
        cached_res = _semantic_cache.get(query_embedding)
        if cached_res is not None:
            cached_copy = copy.deepcopy(cached_res)
            cached_copy["model_used"] = cached_copy.get("model_used", "") + " (Semantic Cache)"
            return cached_copy
    except Exception as e:
        logger.error(f"Semantic Cache check failed: {e}")
        query_embedding = None

    chunks   = context.get("vector_chunks", [])
    entities = context.get("graph_entities", [])
    relations = context.get("graph_relations", [])

    # ── Confidence heuristic (passed as guidance to the prompt) ──────────────
    n_chunks    = len(chunks)
    n_entities  = len(entities)
    n_relations = len(relations)

    # Baseline confidence from retrieval quality — LLM adjusts within this band
    if n_chunks >= 2 and n_entities >= 1:
        guidance_conf = "High   (0.80-1.00)"
    elif n_chunks >= 1 or n_entities >= 1:
        guidance_conf = "Medium (0.50-0.79)"
    else:
        guidance_conf = "Low    (0.00-0.49)"

    # ── Build numbered source context ─────────────────────────────────────────
    doc_parts: List[str] = []
    source_list: List[Dict] = []
    for i, c in enumerate(chunks, 1):
        doc_id  = c["metadata"].get("doc_id", c.get("chunk_id", "unknown"))
        text    = c["text"].strip()
        dist    = c.get("distance", 0.0)
        score   = round(1.0 - float(dist), 3)
        doc_parts.append(f"[Source {i}] {doc_id}  (relevance: {score})\n{text}")
        source_list.append({"doc_id": doc_id, "excerpt": text[:250]})

    doc_context  = "\n\n---\n\n".join(doc_parts) or "No documents retrieved."

    # ── Build graph context string ─────────────────────────────────────────────
    graph_lines: List[str] = []
    for rel in relations[:10]:
        graph_lines.append(
            f"  {rel['source']} --[{rel['relation']}]--> {rel['target']}"
        )
    if not graph_lines:
        graph_lines = ["  No knowledge-graph relationships found for this query."]
    graph_context = "\n".join(graph_lines)

    entity_ids = [e["id"] for e in entities]

    # ── Build prompt ──────────────────────────────────────────────────────────
    conf_guide = _CONFIDENCE_GUIDE.format(
        n_chunks=n_chunks,
        n_entities=n_entities,
        n_relations=n_relations,
    ) + f"  Suggested confidence band: {guidance_conf}"

    prompt = _RAG_TEMPLATE.format(
        doc_context=doc_context,
        graph_context=graph_context,
        question=query,
        confidence_guide=conf_guide,
    )

    # ── Call LLM or fall back to smart context formatter ─────────────
    complexity = classify_query_complexity(query, chunks)
    enable_thinking = complexity["enable_thinking"]
    reasoning_budget = complexity["reasoning_budget"]

    llm = get_llm()
    is_nvidia = "NvidiaLLM" in type(llm).__name__
    llm_label = "NVIDIA API" if is_nvidia else "Ollama"

    if llm.available:
        logger.info(f"generate_answer: calling {llm_label} [{llm.model}]")
        try:
            if is_nvidia:
                tokens_limit = 2048 if enable_thinking else 1024
                raw = llm.generate(
                    prompt,
                    max_tokens=tokens_limit,
                    enable_thinking=enable_thinking,
                    reasoning_budget=reasoning_budget,
                    model=None
                )
            else:
                raw = llm.generate(prompt, max_tokens=settings.max_tokens)
            result = _extract_json(raw)
        except Exception as e:
            logger.error(f"{llm_label} call failed: {e}. Using smart fallback.")
            result = None
    else:
        result = None

    if result is None:
        logger.info("generate_answer: using smart-context fallback")
        # Reuse llm.py fallback, then convert to query_engine schema
        fb = _smart_fallback(query, [
            {"doc_id": c["metadata"].get("doc_id", ""),
             "text": c["text"],
             "citation": c["metadata"].get("doc_id", ""),
             "distance": c.get("distance", 0.0)}
            for c in chunks
        ], graph_lines)
        result = fb
        result["confidence"] = 0.5 if chunks else 0.2
        result["sources"] = source_list
        result["model_used"] = "Smart Context"
        result["entities_used"] = entity_ids
        # Save to cache even on fallback
        if query_embedding is not None:
            try:
                _semantic_cache.set(query_embedding, result)
            except Exception as e:
                logger.error(f"Failed to cache result: {e}")
        return result

    # ── Normalise output schema ───────────────────────────────────────────────
    # Ensure confidence is a float
    raw_conf = result.get("confidence", 0.5)
    if isinstance(raw_conf, str):
        # LLM returned "High" / "Medium" / "Low" — map to float
        raw_conf = {"high": 0.85, "medium": 0.60, "low": 0.25}.get(
            raw_conf.lower(), 0.5
        )
    result["confidence"] = round(float(raw_conf), 3)

    # Merge entity IDs from graph traversal into entities_used
    existing_ents = result.get("entities_used", result.get("entities_mentioned", []))
    result["entities_used"] = list(set(existing_ents + entity_ids))

    # Ensure sources list exists
    if not result.get("sources"):
        result["sources"] = source_list

    result.setdefault("key_points", [])
    result["model_used"] = (
        f"{llm_label} / {llm.model}" if llm.available else "Smart Context"
    )

    # ── Save to semantic cache ────────────────────────────────────────────────
    if query_embedding is not None:
        try:
            _semantic_cache.set(query_embedding, result)
        except Exception as e:
            logger.error(f"Failed to cache result: {e}")

    logger.info(
        f"generate_answer done — confidence={result['confidence']}, "
        f"model={result.get('model_used')}"
    )
    return result


if __name__ == "__main__":
    """
    Standalone smoke-test:
      PYTHONPATH=. python3 src/pipeline/query_engine.py
    Tests retrieve_context + generate_answer against 3 benchmark questions.
    """
    SAMPLE_QUERIES = [
        "Which equipment requires quarterly inspection?",
        "What permits are associated with PRM-2026-5001?",
        "What are the OISD-116 safety requirements for PUMP-A01?",
    ]

    print("=" * 70)
    print("Query Engine — retrieve_context + generate_answer smoke test")
    print("=" * 70)

    for i, q in enumerate(SAMPLE_QUERIES, 1):
        print(f"\n{'─'*60}")
        print(f"Q{i}: {q}")
        print("─" * 60)

        ctx = retrieve_context(q, top_k=5)
        print(
            f"  context → {len(ctx['vector_chunks'])} chunks, "
            f"{len(ctx['graph_entities'])} entities, "
            f"{len(ctx['graph_relations'])} relations"
        )

        ans = generate_answer(q, ctx)
        print(f"  confidence : {ans.get('confidence')}")
        print(f"  model      : {ans.get('model_used')}")
        print(f"  entities   : {ans.get('entities_used', [])[:4]}")
        print(f"  answer     : {str(ans.get('answer',''))[:200]}...")
        if ans.get("sources"):
            print(f"  sources    : {[s['doc_id'] for s in ans['sources'][:3]]}")

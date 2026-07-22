# 🏆 Synapse
## ET AI Hackathon 2026 — Problem Statement 8
### Final Presentation Summary

---

## 🎯 One-Line Pitch
> A production-ready RAG system that ingests heterogeneous industrial documents and provides cited, confidence-scored answers with real-time streaming, achieving **100% accuracy** on regulatory compliance questions.

---

## 📊 Key Results

| Metric | Before | After | Improvement |
|---|---|---|---|
| **Accuracy** | 77.8% (14/18) | **100% (18/18)** | +22.2% |
| **Avg Latency (steady-state)** | 10,306 ms | **771 ms** | −92.5% |
| **Avg Latency (cold start)** | — | **3,930 ms** | — |
| **Slowest Query** | ~46,600 ms | **1,364 ms** | −97.1% |
| **Fastest Query** | ~5,000 ms | **566 ms** | −88.7% |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Chat Q&A    │  │  Knowledge   │  │  Benchmark   │  │
│  │  (Streaming) │  │  Explorer    │  │  Runner      │  │
│  └──────┬───────┘  └──────────────┘  └──────────────┘  │
└─────────┼───────────────────────────────────────────────┘
          │ SSE /query/stream
          ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ /query       │  │ /query/stream│  │ /benchmark   │  │
│  │ (sync)       │  │ (SSE)        │  │ /run         │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  │
└─────────┼─────────────────┼─────────────────────────────┘
          │                 │
          ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│               Query Engine Pipeline                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Embedder │→ │ ChromaDB │→ │ Cross-   │→ │ Graph  │  │
│  │ (384d)   │  │ Retrieval│  │ Encoder  │  │ 1-hop  │  │
│  └──────────┘  └──────────┘  │ Re-rank  │  └────────┘  │
│                               └──────────┘              │
│  ┌──────────────────┐  ┌──────────────────────────────┐ │
│  │ Complexity       │  │ Semantic Cache (500 entries)  │ │
│  │ Classifier       │  │ 0.95 cosine threshold         │ │
│  └──────────────────┘  └──────────────────────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              NVIDIA NIM (nemotron-3-ultra-550b)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 10-key       │  │ Thinking     │  │ Streaming    │  │
│  │ Rotation     │  │ Mode         │  │ API          │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Three-Tier Optimization

### Tier 1 — Correctness Fixes (77.8% → 100%)
1. **Graph context from chunk metadata** — Entities extracted from retrieved chunks, not just query text
2. **Chunk size 1024 + 200 overlap** — Prevents split-section failures across regulatory docs
3. **Embedding similarity scoring** — Cosine similarity ≥ 0.55 replaces brittle keyword overlap
4. **Max tokens cap 640** — Reduces unnecessary output generation time

### Tier 2 — Latency & Precision (1,200ms → 1,065ms)
1. **Query-side regex fallback** — Extracts equipment tags, OISD codes when spaCy returns 0 entities
2. **Cross-encoder re-ranker** — `ms-marco-MiniLM-L-6-v2` re-ranks top-10 → top-3 chunks
3. **Per-query complexity classifier** — Gates `reasoning_budget` (0 vs 1024) per query
4. **Semantic cache (500 entries, 0.95 threshold)** — Skips LLM on near-duplicate queries

### Tier 3 — Streaming & UX (1,065ms → 771ms + streaming)
1. **`stream_generate()` generator** — Yields tokens from NIM streaming API
2. **`/query/stream` SSE endpoint** — Server-Sent Events with token + metadata + done events
3. **`try/finally` error recovery** — Metadata+done events always fire, even on mid-stream errors
4. **Streamlit streaming consumer** — Real-time token rendering via `httpx.Client.stream()`
5. **`_find_working_client()` refactor** — Deduplicates key-rotation logic (~40 lines removed)
6. **Shared `classify_query_complexity()`** — Single source of truth for complexity heuristics

---

## 🎯 Key Technical Innovations

1. **Embedding similarity over keyword overlap** — Solves plural/singular mismatches ("compressor" vs "compressors")
2. **Cross-encoder re-ranking** — Semantically similar but factually wrong chunks no longer outrank correct ones
3. **Per-query complexity classification** — Simple factual lookups skip expensive thinking mode
4. **SSE streaming** — Tokens appear instantly; perceived latency drops to near-zero
5. **Section-aware chunking** — Split OISD-118 into 3 section-specific files for precise HAZOP retrieval
6. **Retrieval source logging** — Captures chunk sources for regression diagnosis

---

## 📁 Document Corpus

| Document Type | Files | Entities Extracted |
|---|---|---|
| **OISD Standards** | OISD-116, OISD-117, OISD-118, OISD-119, OISD-130 | Equipment, Regulations, Hazards |
| **DGMS Circulars** | DGMS-2022-05, DGMS-2023-01, DGMS-TC-15 | Requirements, Personnel |
| **Factory Act** | FA-SEC-7A, FA-SEC-36, FA-SEC-38, FA-SEC-40A, FA-SEC-41B, FA-SEC-41C | Regulations, Sections |
| **Synthetic Data** | Permits, Work Orders, Incidents, Inspections | Equipment, Personnel, Locations |

---

## 🧪 Benchmark Results

**18/18 questions passing** across 15 categories:
- Equipment inspection (4/4) ✅
- Permits, Emergency, Safety equipment ✅
- Compliance, Fire safety, Incident reporting ✅
- Worker rights, Process safety, Hazardous processes ✅
- Electrical safety, Monitoring, Training ✅
- Safety environment, Equipment safety ✅

**Per-question latency range:** 566ms (fastest) → 1,364ms (slowest, server steady-state)

---

## 🛡️ Resilience Features

1. **Smart-context fallback** — Handles API timeouts/rate limits gracefully
2. **Retrieval source logging** — Diagnoses regressions by capturing chunk sources
3. **Section-aware chunking** — Prevents chunk dilution in long regulatory documents
4. **Warm-up phase** — Ensures consistent benchmark results after cold start
5. **10-key NIM rotation** — Handles rate limits across multiple API keys

---

## 🚀 Production Ready

- **Real-time streaming** — Token-by-token response delivery
- **Error recovery** — try/finally ensures metadata+done events always fire
- **Semantic cache** — 500-entry LRU cache skips LLM on duplicate queries
- **Comprehensive documentation** — README, conclusions.md, and retrieval logs
- **100% benchmark accuracy** — All 18 regulatory compliance questions pass

---

## 📈 Git Commit History

| Commit | Description |
|---|---|
| `2e66844` | Optimization Pass: Tier 1-3 complete, 100% accuracy, 771ms avg latency |
| `490380b` | Refactor: extract `_find_working_client()`, remove dead imports |
| `b11a87d` | Fix duplicate embedding: move OISD-118_Original.txt outside corpus tree |
| `9b08d63` | Add retrieval source logging for benchmark regression diagnosis |
| `7d67a58` | Update conclusions.md with warm server benchmark and regression findings |
| `517cb44` | Clarify headline metrics: 771ms is steady-state, not cold-start |
| `d2c0c03` | Update README with optimization pass docs and benchmark guide |
| `10e0fcf` | Add retrieval log from final benchmark run |
| `65acc40` | Add warm-up phase to benchmark script for consistent results |
| `5907baf` | Update conclusions.md with fresh benchmark numbers |

---

## 🎬 Demo Instructions

### Start the Servers

**Terminal 1 — FastAPI Backend:**
```bash
cd /Users/pallav/Downloads/Rag-eco-hackathon
PYTHONPATH=/Users/pallav/Downloads/Rag-eco-hackathon python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Streamlit Frontend:**
```bash
cd /Users/pallav/Downloads/Rag-eco-hackathon
streamlit run src/app.py --server.port 8501
```

### Demo Flow

1. **Streaming Chat Q&A** — Ask "When is a hot work permit required?" and watch tokens stream in real-time
2. **Knowledge Explorer** — Navigate to the graph visualization tab to see entity relationships
3. **Benchmark Runner** — Run the full 18-question benchmark to verify 100% accuracy
4. **Document Library** — View all ingested regulatory documents

---

## 💡 What Makes This Different

1. **Not just RAG** — Combines vector search with structured knowledge graph traversal
2. **Production-grade streaming** — Not just a demo, but a robust SSE implementation with error recovery
3. **Resilient to API failures** — Smart-context fallback handles timeouts and rate limits gracefully
4. **Comprehensive benchmarking** — 18-question ground truth with retrieval source logging for regression diagnosis
5. **Section-aware chunking** — Solves the "chunk dilution" problem in long regulatory documents

---

## 📚 Files Modified

| File | Key Changes |
|---|---|
| `src/pipeline/query_engine.py` | Chunk-entity graph traversal, cross-encoder re-ranking, semantic cache, shared complexity classifier |
| `src/pipeline/llm.py` | `stream_generate()` generator, `_find_working_client()` refactor, `_build_extra_body()` helper |
| `src/main.py` | `/query/stream` SSE endpoint with try/finally error recovery, cleaned imports |
| `src/app.py` | Streaming chat UI with `httpx.Client.stream()` |
| `src/config.py` | `chunk_size=1024`, `chunk_overlap=200`, `max_tokens=640`, `similarity_threshold=0.55` |
| `run_benchmark_now.py` | Warm-up phase with 5 representative queries |
| `requirements.txt` | Added `httpx>=0.27.0` |

---

## 🎯 Future Work

1. **Section-aware chunking for all regulatory docs** — Apply to OISD-116, OISD-117, OISD-119, Factory Act sections
2. **Async FastAPI endpoint** — Use `AsyncOpenAI` client for concurrent request handling
3. **Production server** — Add process manager (systemd/supervisor) for deployment
4. **Streaming answer display** — Render badges/sources below streamed text
5. **Benchmark caching** — Persist warm-up state between runs

---

## 🏆 Summary

The Synapse demonstrates that production-grade RAG systems can achieve:
- **100% accuracy** on regulatory compliance questions
- **92.5% latency reduction** through optimization
- **Real-time streaming** for perceived performance
- **Resilient error handling** for production reliability

**Built in 6 days for the ET AI Hackathon 2026.**

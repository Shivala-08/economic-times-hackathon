# AI for Industrial Knowledge Intelligence

**ET AI Hackathon 2026 — Problem Statement 8**

RAG-powered system that ingests industrial documents (PDFs, CSVs, DOCX) and provides cited, confidence-scored answers using both vector search and a knowledge graph.

## Architecture

```
Document Corpus → Ingestion Pipeline → [Embeddings + Entity Extraction]
                                       ↓              ↓
                                   Vector Store   Knowledge Graph
                                       ↓              ↓
                                   Query Engine (merge results)
                                       ↓
                                   Claude API (structured JSON)
                                       ↓
                                   Streamlit UI
```

## Quick Start

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate synthetic data
python data/synthetic_data_generator.py

# Generate regulatory templates
python data/regulatory_templates.py

# Run the API
PYTHONPATH=. uvicorn src.main:app --reload

# Test ChromaDB
PYTHONPATH=. python tests/test_chromadb.py
```

## Project Structure

```
├── src/                    # Source code
│   ├── main.py            # FastAPI application
│   ├── config.py          # Configuration
│   ├── api/               # API endpoints
│   ├── pipeline/          # Ingestion pipeline (chunking, embedding)
│   ├── graph/             # Knowledge graph (NetworkX)
│   ├── storage/           # Vector store (ChromaDB)
│   └── utils/             # Shared utilities
├── data/                  # Data directory
│   ├── corpus/            # Document corpus
│   │   ├── real/          # Regulatory documents
│   │   └── synthetic/     # Generated data (CSVs)
│   ├── benchmarks/        # Q&A benchmark pairs
│   └── chroma_db/         # ChromaDB persistence
└── tests/                 # Test files
```

## Day 1 Status

- [x] Python venv + requirements.txt
- [x] FastAPI skeleton with `/health`
- [x] ChromaDB integration tested
- [x] Synthetic data generator (work orders, permits, inspections, incidents)
- [x] Regulatory document templates (OISD, DGMS, Factory Act)
- [x] 18 benchmark Q&A pairs

## Day 2 Status

- [x] Parsers (pdfplumber, pandas, python-docx, TXT)
- [x] Chunking with overlap + sentence-boundary detection
- [x] Embedding with sentence-transformers (all-MiniLM-L6-v2)
- [x] ChromaDB vector store wrapper
- [x] `/ingest/upload` — upload PDF/DOCX/CSV/TXT
- [x] `/ingest/initialize` — clear + re-ingest all corpus files
- [x] `/documents` + `/documents/{doc_id}` — document listing and detail
- [x] `/query` — vector similarity search (mock LLM for Day 4)
- [x] Streamlit UI skeleton (chat, document library, control panel)
- [x] Full corpus indexed: 14 regulatory docs + 4 synthetic CSVs (19 docs, 250+ chunks)

## Day 3 Status

- [x] spaCy + regex entity extractor (`src/pipeline/extractor.py`)
  - Equipment tags (EQ-*, PUMP-*, COMP-*, TNK-*, etc.)
  - Permit IDs (PRM-*) and work order IDs (WO-*)
  - Regulation references (OISD-*, DGMS-*, Factory Act Section *)
  - Plants, hazards, incident types, permit types, personnel (spaCy NER)
- [x] NetworkX knowledge graph (`src/graph/knowledge_graph.py`)
  - Typed nodes: equipment, regulation, plant, permit, work_order, incident, inspection, person, hazard
  - Relationship edges: subject_to, located_at, has_hazard, issued_for, assigned_to, etc.
  - JSON persistence, subgraph traversal, entity-by-type lookup
- [x] Entity extraction integrated into ingestion pipeline
- [x] New API endpoints: `/graph`, `/graph/entity/{id}`, `/entities`
- [x] `/query` now augments vector search with graph traversal
- [x] Streamlit UI: Knowledge Graph visualization tab (streamlit-agraph)
- [x] Streamlit UI: Entity Explorer tab with type filtering and subgraph drill-down
- [x] Streamlit UI: Sidebar graph stats (nodes, edges, entity breakdown)
- [x] Graph-augmented query responses with entity badges
- [x] **454 nodes, 7,864 edges** in knowledge graph across 11 entity types

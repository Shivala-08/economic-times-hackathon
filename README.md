# AI for Industrial Knowledge Intelligence

**ET AI Hackathon 2026 — Problem Statement 8**

A premium, production-ready RAG-powered system that ingests heterogeneous industrial documents (regulatory guides, safety manuals, work orders, permits, incident reports) and provides cited, confidence-scored answers by merging semantic vector search with a structured knowledge graph.

---

## 🏗️ Architecture

```
┌─────────────────────┐
│   Document Corpus   │  PDFs, CSVs, DOCX (safety manuals, work orders,
│                     │  permits, regulatory docs, incident reports)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Ingestion Pipeline  │  Parse (pdfplumber/docx/pandas) → Clean → Chunk
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼─────┐ ┌───▼──────────┐
│ Embedding│ │    Entity    │
│ (all-    │ │  Extraction  │
│ MiniLM)  │ │ (spaCy+Regex)│
└────┬─────┘ └───┬──────────┘
     │           │
┌────▼─────┐ ┌───▼──────────┐
│  Vector  │ │  Knowledge   │
│  Store   │ │    Graph     │
│(ChromaDB)│ │ (NetworkX)   │
└────┬─────┘ └───┬──────────┘
     │           │
     └─────┬─────┘
           │
┌──────────▼──────────┐
│    Query Engine     │  Retrieve top-k chunks + traverse graph
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Claude API Call    │  Assembles context → structured JSON:
│                     │  {answer, sources[], confidence}
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│    Streamlit UI     │  Interactive Chat + Citations + Badges
│                     │  + Document Library + Upload Panel
└─────────────────────┘
```

---

## 📂 Repository Structure

The project codebase is organized as follows:

```
├── data/                       # Ingested and generated data
│   ├── benchmarks/             # Ground-truth Q&A pairs for evaluation
│   │   └── qa_pairs.json
│   ├── corpus/                 # Source document corpus
│   │   ├── real/               # Regulatory guides (OISD, DGMS, Factory Act)
│   │   ├── synthetic/          # Generated logs (CSV work orders, permits, etc.)
│   │   └── uploads/            # Persistent user-uploaded files
│   ├── chroma_db/              # ChromaDB vector store files
│   ├── documents.json          # Metadata registry tracking ingested documents
│   ├── regulatory_templates.py # Seed templates for circulars
│   └── synthetic_data_generator.py # faker-based generator for CSV logs
│
├── src/                        # System source code
│   ├── main.py                 # FastAPI application and endpoints
│   ├── config.py               # Pydantic configuration & environment variables
│   ├── app.py                  # Streamlit frontend application
│   ├── api/                    # API Route controllers
│   ├── pipeline/               # Ingestion pipeline modules
│   │   ├── parser.py           # TXT, PDF, DOCX, and CSV Row parsers
│   │   ├── chunker.py          # Paragraph/Sentence boundary chunker
│   │   ├── embedder.py         # local SentenceTransformer vector embedding
│   │   └── ingest.py           # Ingestion pipeline coordinator
│   ├── storage/                # Database wrappers
│   │   └── chroma_store.py     # ChromaDB vector collection manager
│   ├── graph/                  # Knowledge graph components (Upcoming)
│   └── utils/                  # Shared helper scripts
│
├── tests/                      # Verification suites
│   ├── test_chromadb.py        # Core vector store integration test
│   └── verify_endpoints.py     # FastAPI backend end-to-end endpoint verification
│
├── requirements.txt            # System dependencies
└── README.md                   # Project documentation
```

---

## 🛠️ Status & Progress

### Day 1 — Foundations (Completed)
- [x] Initialized project repository and Python virtual environment (`.venv`).
- [x] Configured project settings using `pydantic-settings` loaded from `.env`.
- [x] Generated seed templates for regulatory guidelines (OISD, DGMS Circulars, and Factory Act sections).
- [x] Implemented Faker-based generator for synthetic plant data (work orders, work permits, inspection logs, and incident reports).
- [x] Prepared ground-truth dataset comprising 18 complex Q&A pairs for system evaluation.
- [x] Configured and verified local vector database connectivity (ChromaDB).

### Day 2 — Ingestion Pipeline & UI Skeleton (Completed)
- [x] **Document Parsing Module (`parser.py`)**:
  - Structured parsers for plain text, PDFs (`pdfplumber`), and Word files (`python-docx`).
  - Implemented row-by-row parsing for CSVs where each row becomes a self-contained, fully-attributed text record.
- [x] **Ingestion Pipeline Coordinator (`ingest.py`)**:
  - Integrates the parsers, sentence boundary chunker (`chunker.py`), and SentenceTransformer models (`embedder.py`).
  - Tracks document status, size, and indexing timestamps inside a metadata registry (`documents.json`).
- [x] **FastAPI Ingestion & Search Server (`main.py`)**:
  - `POST /ingest/initialize` to scan the corpus directories and populate the vector store.
  - `POST /ingest/upload` to dynamically upload and register custom files.
  - `GET /documents` and `GET /documents/{doc_id}` to retrieve document metadata and chunks.
  - `POST /query` to execute semantic vector similarity searches against indexed documents.
- [x] **Streamlit Web UI (`app.py`)**:
  - A premium, responsive interface featuring dynamic navigation tabs.
  - **Chat Q&A**: Handles queries, showing responses alongside interactive citation cards and distance scores.
  - **Document Library**: Lists all indexed documents with active chunk expanders to inspect what the AI reads.
  - **Control Center**: Triggers default indexing or uploads new manuals via drag-and-drop.
- [x] **Verification Suites**:
  - `tests/test_chromadb.py` and `tests/verify_endpoints.py` to confirm everything runs flawlessly.

---

## 🚀 Quick Start

### 1. Set Up Environment
Ensure you have Python 3.10+ installed:
```bash
# Clone the repository
git clone https://github.com/Shivala-08/economic-times-hackathon.git
cd economic-times-hackathon

# Initialize virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Ingest the Data
Populate the local vector database with the pre-bundled industrial documents and generated plant logs:
```bash
PYTHONPATH=. python src/pipeline/ingest.py
```

### 3. Launch the Backend
Start the FastAPI server:
```bash
PYTHONPATH=. uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 4. Launch the Frontend
In a separate terminal tab (with active virtual environment), run:
```bash
streamlit run src/app.py --server.port 8501
```
Open **`http://localhost:8501`** in your browser to interact with the application.

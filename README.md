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
│                     │  + Document Library + Upload Panel + Graph View
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
│   ├── knowledge_graph.json    # Serialized NetworkX knowledge graph
│   ├── regulatory_templates.py # Seed templates for circulars
│   └── synthetic_data_generator.py # Faker-based generator for CSV logs
│
├── src/                        # System source code
│   ├── main.py                 # FastAPI application and endpoints
│   ├── config.py               # Pydantic configuration & environment variables
│   ├── app.py                  # Streamlit frontend application (agraph-visualized)
│   ├── api/                    # API Route controllers
│   ├── pipeline/               # Ingestion pipeline modules
│   │   ├── parser.py           # TXT, PDF, DOCX, and CSV Row parsers
│   │   ├── chunker.py          # Paragraph/Sentence boundary chunker
│   │   ├── embedder.py         # Local SentenceTransformer vector embedding
│   │   ├── extractor.py        # spaCy + Regex entity extraction
│   │   ├── compliance.py       # Regulatory gap analysis
│   │   └── ingest.py           # Ingestion pipeline coordinator
│   ├── storage/                # Database wrappers
│   │   └── chroma_store.py     # ChromaDB vector collection manager
│   ├── graph/                  # Knowledge graph components
│   │   └── knowledge_graph.py  # NetworkX knowledge graph constructor & query
│   └── utils/                  # Shared helper scripts
│
├── tests/                      # Verification suites
│   ├── test_chromadb.py        # Core vector store integration test
│   ├── test_knowledge_graph.py # Knowledge graph construction and traversal test
│   └── verify_endpoints.py     # FastAPI backend end-to-end endpoint verification
│
├── requirements.txt            # System dependencies
└── README.md                   # Project documentation
```

---

## 🛠️ Key Components & Status

### 1. Document Ingestion & Parsing
- Parses PDF files page-by-page using `pdfplumber`.
- Parses Microsoft Word files (.docx) using `python-docx`.
- Parses plain text files (.txt) using standardized encoders.
- Parses industrial logs (.csv) using `pandas` row-by-row. Each row (e.g. work orders, incident reports, permits) is transformed into a self-describing, search-friendly textual block and embedded individually.

### 2. Entity Extraction & NLP
- Integrated **spaCy** (`en_core_web_sm`) alongside pre-compiled domain-specific **Regex patterns**.
- Automatically extracts:
  - **Equipment tags** (e.g., `EQ-1001`, `PUMP-A01`, `TNK-T02`, `COMP-C01`)
  - **Work permits** (e.g., `PRM-2026-5000`)
  - **Work orders** (e.g., `WO-2026-1000`)
  - **Inspection logs** (e.g., `INS-2026-8000`)
  - **Incident reports** (e.g., `INC-2026-9000`)
  - **Regulation references** (e.g., `OISD-116`, `DGMS Circular 2022-05`, `Factory Act Section 36`)
  - **Plants & Locations** (e.g., `Refinery Unit A`, `Steel Mill D`)
  - **Hazards & Injury Severities** (e.g., `Fire hazard`, `Lost Time`)
  - **Personnel** (using spaCy NER `PERSON`)

### 3. Knowledge Graph
- Constructed using **NetworkX** to map relationships between files, equipment, regulations, hazards, and plants.
- Establishes explicit links (e.g., `EQUIPMENT --[REGULATED_BY]--> REGULATION`, `WORK_ORDER --[PERFORMS_ON]--> EQUIPMENT`, `INCIDENT --[OCCURRED_AT]--> PLANT`).
- Serialized to `data/knowledge_graph.json` and supports graph traversal queries for context expansion.

### 4. Regulatory Compliance Checker
- Automated compliance check module comparing regulatory requirements against ingested plant procedures to identify gaps, compliance status, and highlight supporting evidence.

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

### 2. Ingest the Data & Build the Graph
Populate the vector database and construct the knowledge graph from the pre-bundled document corpus:
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

---

## 🧪 Running Verification Tests

Run the following test commands to verify system health:
```bash
# Verify ChromaDB vector store
PYTHONPATH=. python tests/test_chromadb.py

# Verify Knowledge Graph construction and query traversal
PYTHONPATH=. python tests/test_knowledge_graph.py

# Verify FastAPI endpoint integrations
PYTHONPATH=. python tests/verify_endpoints.py
```

# Hasamex AI Engineer Technical Case: Expert Interview Transcript Analysis AI Agent

A production-grade, grounded RAG application that ingests expert-call transcripts and an interview guide to provide exact quote extraction, timestamped evidence verification, cross-expert consensus/conflict synthesis, and arbitrary cross-transcript Q&A.

---

## Key Features

1. **Guided Q&A Matrix**: Maps each canonical question from the interview guide to all expert transcripts, generating structured per-expert answers.
2. **Exact Verbatim Quote & Timestamp Extraction**: Every claim cites exact verbatim quotes from the transcript paired with start/end timestamps (e.g., `01:05 - 02:02`).
3. **Cross-Expert Synthesis**: Automatically extracts common consensus themes and highlights explicit market disagreements (e.g., Germany vs. UK vs. France).
4. **Arbitrary Cross-Transcript RAG**: Allows users to execute ad-hoc natural language queries across all loaded transcripts.
5. **Zero-Hallucination Evidence Validation Pipeline**: Uses a Python post-processing verification engine to validate LLM-claimed quotes against source chunks using verbatim substring and fuzzy string matching.

---

## Technical Architecture

```text
                               ┌──────────────────────────────────────────────────────────┐
                               │                    USER INTERFACE                        │
                               │  Streamlit Multi-Tab Dashboard (Matrix, Synthesis, Q&A)   │
                               └────────────────────────────┬─────────────────────────────┘
                                                            │ User Query / Actions
                                                            ▼
                               ┌──────────────────────────────────────────────────────────┐
                               │                   FASTAPI BACKEND API                    │
                               └──────────────┬────────────────────────────▲──────────────┘
                                              │ Ingest Files               │ Return Verified Response
                                              ▼                            │
┌─────────────────────────┐    ┌─────────────────────────┐                 │
│  RAW DATA INGESTION     │    │  TRANSCRIPT PARSER      │                 │
│                         │    │  (Regex Engine)         │                 │
│ - Transcript Files      ├────► - Metadata Extractor    │                 │
│ - Interview Guide File  │    │ - Timestamp Anchor      │                 │
│                         │    │   Identifier            │                 │
└─────────────────────────┘    └──────────────┬──────────┘                 │
                                              │ Document Structure         │
                                              ▼                            │
                               ┌─────────────────────────┐                 │
                               │  TURN-AWARE CHUNKER     │                 │
                               │  - Preserves Turn Boundaries│               │
                               │  - Aggregates Q&A Pairs │                 │
                               │  - Binds Metadata       │                 │
                               └──────────────┬──────────┘                 │
                                              │ Chunks with Metadata       │
                                              ▼                            │
                               ┌─────────────────────────┐                 │
                               │  EMBEDDING ENGINE       │                 │
                               │  Gemini text-embedding  │                 │
                               └──────────────┬──────────┘                 │
                                              │ Dense Vectors + Metadata   │
                                              ▼                            │
                               ┌─────────────────────────┐                 │
                               │  IN-MEMORY VECTOR STORE │                 │
                               │  ChromaDB / FAISS       │                 │
                               └──────────────┬──────────┘                 │
                                              │ Metadata-Filtered          │
                                              │ Semantic Search            │
                                              ▼                            │
                               ┌─────────────────────────┐                 │
                               │  RAG REASONING ENGINE   │                 │
                               │  - Gemini LLM           │                 │
                               │  - Pydantic JSON Schema │                 │
                               └──────────────┬──────────┘                 │
                                              │ Unvalidated Claims & Quotes│
                                              ▼                            │
                               ┌─────────────────────────┐                 │
                               │  EVIDENCE VALIDATOR     │─────────────────┘
                               │  - Substring Matcher    │
                               │  - Timestamp Verifier   │
                               │  - Hallucination Filter │
                               └─────────────────────────┘
```

---

## Local Setup & Run Instructions

### Prerequisites
- Python 3.10+
- (Optional) `GEMINI_API_KEY` for live Gemini API calls. If unconfigured, the system automatically uses fallback semantic search and deterministic extraction.

### Installation

1. **Clone Repository & Navigate to Folder**:
   ```bash
   cd hasamex-transcript-ai
   ```

2. **Create Virtual Environment & Install Dependencies**:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Configure Environment Variables** (Optional):
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY inside .env
   ```

4. **Run Unit Tests**:
   ```bash
   pytest
   ```

5. **Launch Backend API**:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```

6. **Launch Frontend Dashboard**:
   ```bash
   streamlit run frontend/app.py
   ```
   Open `http://localhost:8501` in your browser.

---

## Technical Deep-Dive

### How Timestamps & Citations are Handled
Standard character/word sliding window chunkers cut sentences mid-thought and detach timestamp headers from speaker turns. 
We implement **Turn-Aware Dialogue Chunking**:
- The regex parser identifies timestamp anchors (`01:05`) and speaker prefixes (`Dr. Carter:`).
- Each Interviewer Question is paired atomically with the Expert's full turn response.
- `start_timestamp` and `end_timestamp` are bound directly to the chunk metadata alongside `expert_id`, `name`, `role`, and `market`.

### How Hallucinations are Reduced / Eliminated
1. **Strict Context Enforcement**: LLM prompt instructs model to reply using *only* retrieved context chunks.
2. **Pydantic Structured Output**: Force JSON response adhering to `{ summary_answer: str, evidence: [{ quote: str, speaker: str, timestamp: str }] }`.
3. **Verbatim Substring & Timestamp Validation Pipeline**: Every extracted quote is run against the raw source `verbatim_text` of the retrieved chunk. If exact or fuzzy string matching ($\ge 80\%$) fails, the quote is flagged as `UNVERIFIED_HALLUCINATION` or dropped.

### Scaling from 3 Transcripts to 30+
1. **Vector Store Scaling**: Transition from in-memory ChromaDB/Numpy vector index to a production persistent vector database (e.g. Qdrant / Pgvector) with metadata filtering on `market`, `role`, and `project_id`.
2. **Hierarchical / Agentic Summarization**: For 30+ transcripts, matrix generation can be parallelized across map-reduce workers, generating per-market clusters (e.g. DACH, UKI, Nordics) before final cross-market synthesis.
3. **Async Batch Processing**: Implement background queue workers (Celery / Redis / Temporal) for transcript parsing, chunking, and embedding generation upon file upload.

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

from backend.app.config import DATA_DIR
from backend.app.schemas import (
    QuestionAnswerResult,
    SynthesisResult,
    CustomQARequest,
    CustomQAResponse,
    ExpertMetadata,
    TranscriptChunk,
    RAGAnswerResponse
)
from backend.app.services.parser import parse_interview_guide, parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.services.vector_store import vector_store
from backend.app.services.rag_engine import rag_engine

# In-memory storage state
STATE: Dict[str, Any] = {
    "interview_guide_objective": "",
    "interview_questions": [],
    "experts": [],
    "all_chunks": [],
    "raw_transcripts": {}
}


def load_initial_data():
    """Ingests data files from the data directory on startup."""
    guide_path = DATA_DIR / "interview_guide.txt"
    if guide_path.exists():
        objective, questions = parse_interview_guide(guide_path.read_text(encoding="utf-8"))
        STATE["interview_guide_objective"] = objective
        STATE["interview_questions"] = questions

    STATE["experts"] = []
    STATE["all_chunks"] = []
    STATE["raw_transcripts"] = {}
    vector_store.clear()

    transcript_files = list(DATA_DIR.glob("expert_*.txt"))
    for tf in sorted(transcript_files):
        content = tf.read_text(encoding="utf-8")
        STATE["raw_transcripts"][tf.name] = content
        
        parsed = parse_transcript(content, tf.name)
        metadata: ExpertMetadata = parsed["metadata"]
        STATE["experts"].append(metadata)
        
        chunks = create_turn_chunks(parsed)
        STATE["all_chunks"].extend(chunks)
        vector_store.add_chunks(chunks)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_initial_data()
    yield


app = FastAPI(
    title="Hasamex Expert Interview Transcript Analysis API",
    version="2.0.0",
    description="Backend service for grounded RAG analysis of expert call transcripts with SSE streaming.",
    lifespan=lifespan
)

# Enable CORS for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "experts_loaded": len(STATE["experts"]),
        "total_chunks": len(STATE["all_chunks"]),
        "questions_loaded": len(STATE["interview_questions"])
    }


@app.get("/api/transcripts")
def get_transcripts():
    """Returns metadata and raw text for all loaded transcripts."""
    return {
        "guide_objective": STATE["interview_guide_objective"],
        "questions": STATE["interview_questions"],
        "experts": STATE["experts"],
        "raw_transcripts": STATE["raw_transcripts"]
    }


@app.post("/api/transcripts/upload")
async def upload_transcript(file: UploadFile = File(...)):
    """
    Accepts an uploaded transcript .txt file, parses expert metadata, creates turn chunks,
    indexes into the in-memory vector store, and registers into live app state.
    """
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt transcript files are supported.")

    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8")
        filename = file.filename

        # Parse transcript turns and metadata
        parsed = parse_transcript(content, filename)
        metadata: ExpertMetadata = parsed["metadata"]
        chunks = create_turn_chunks(parsed)

        # Update in-memory state
        STATE["raw_transcripts"][filename] = content
        # Prevent duplicate entries for same expert ID
        STATE["experts"] = [e for e in STATE["experts"] if e.expert_id != metadata.expert_id]
        STATE["experts"].append(metadata)
        STATE["all_chunks"].extend(chunks)

        # Add chunks to vector store
        vector_store.add_chunks(chunks)

        return {
            "status": "success",
            "message": f"Successfully parsed and indexed {metadata.name} ({metadata.market}) with {len(chunks)} turns.",
            "expert": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process transcript file: {str(e)}")


@app.get("/api/matrix", response_model=List[QuestionAnswerResult])
def get_matrix_answers():
    """
    Evaluates all 6 interview-guide questions for every loaded expert transcript.
    """
    if not STATE["interview_questions"] or not STATE["experts"]:
        raise HTTPException(status_code=400, detail="Transcripts or interview guide not loaded.")

    results: List[QuestionAnswerResult] = []
    for question in STATE["interview_questions"]:
        for expert in STATE["experts"]:
            res = rag_engine.answer_guided_question(
                question=question,
                expert=expert,
                all_expert_chunks=STATE["all_chunks"]
            )
            results.append(res)
            
    return results


@app.get("/api/synthesis", response_model=SynthesisResult)
def get_synthesis():
    """
    Identifies common themes and disagreements across all expert transcripts.
    """
    if not STATE["all_chunks"]:
        raise HTTPException(status_code=400, detail="No transcript chunks available for synthesis.")

    return rag_engine.synthesize_themes_and_disagreements(STATE["all_chunks"])


@app.post("/api/qa", response_model=CustomQAResponse)
def execute_custom_qa(request: CustomQARequest):
    """
    Executes an ad-hoc cross-transcript RAG query.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    return rag_engine.custom_qa(
        query=request.query,
        target_expert_ids=request.target_expert_ids
    )


@app.post("/api/chat/stream")
async def stream_chat_response(request: CustomQARequest):
    """
    Server-Sent Events (SSE) endpoint to stream Claude/Gemini-style token-by-token
    typing effects for AI answers paired with verified evidence cards.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    async def event_generator():
        # Execute RAG retrieval and reasoning
        res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(
            query=request.query,
            expert_id=request.target_expert_ids[0] if request.target_expert_ids else None
        )

        full_text = res.answer
        words = full_text.split(" ")

        # Stream summary text word-by-word with realistic typing delay
        for i in range(len(words)):
            chunk = words[i] + (" " if i < len(words) - 1 else "")
            payload = json.dumps({"type": "token", "content": chunk})
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0.03)

        # Stream evidence cards payload after text completion
        evidence_payload = json.dumps({
            "type": "evidence",
            "confidence": res.confidence,
            "is_grounded": res.is_grounded,
            "evidence": [ev.dict() for ev in res.evidence]
        })
        yield f"data: {evidence_payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

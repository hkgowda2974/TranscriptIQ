import pytest
from backend.app.schemas import RAGAnswerResponse
from backend.app.services.rag_engine import rag_engine, REFUSAL_MESSAGE
from backend.app.services.vector_store import vector_store
from backend.app.services.parser import parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.config import DATA_DIR


@pytest.fixture(autouse=True)
def setup_vector_store():
    """Initializes vector store with all 3 expert transcripts."""
    vector_store.clear()
    for tf in sorted(DATA_DIR.glob("expert_*.txt")):
        parsed = parse_transcript(tf)
        chunks = create_turn_chunks(parsed)
        vector_store.add_chunks(chunks)


def test_refusal_for_unmentioned_brand():
    """Questions about unmentioned competitor/brand names must be refused."""
    res = rag_engine.execute_rag_pipeline("What is the market share of Intuitive Surgical in Germany?")
    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


def test_refusal_for_unmentioned_topic_topically_adjacent():
    """
    Questions asking for specific details not in transcripts (e.g. warranty period)
    must be refused rather than generating an answer from adjacent chunks.
    """
    res = rag_engine.execute_rag_pipeline("What is the warranty period for robotic instruments in France?")
    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


def test_refusal_for_unmentioned_country():
    """Questions about unsupported countries must be refused."""
    res = rag_engine.execute_rag_pipeline("How does reimbursement work for robotic surgery in Japan?")
    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


def test_valid_question_with_sufficient_evidence():
    """Valid questions with direct transcript evidence must be answered with verified quotes."""
    res = rag_engine.execute_rag_pipeline("How important is reimbursement in France?")
    assert res.answer != REFUSAL_MESSAGE
    assert len(res.evidence) >= 1
    assert any("expert_1.txt" in ev.source for ev in res.evidence)
    assert res.confidence == "HIGH"

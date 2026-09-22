import pytest
from backend.app.schemas import InterviewQuestion, ExpertMetadata
from backend.app.services.rag_engine import rag_engine
from backend.app.services.vector_store import vector_store
from backend.app.services.parser import parse_transcript
from backend.app.services.chunker import create_turn_chunks

SAMPLE_TRANSCRIPT_1 = """Expert 1 – Dr. Jean-Luc Dubois
Role: Chief of Surgical Services
Market: France

00:00
Interviewer: What are the main barriers?

01:08
Dr. Dubois: The initial capital investment remains high, but reimbursement restrictions under Sécurité Sociale present the biggest hurdle.
"""


def test_rag_guided_question():
    parsed = parse_transcript(SAMPLE_TRANSCRIPT_1, "expert_1.txt")
    chunks = create_turn_chunks(parsed)
    vector_store.clear()
    vector_store.add_chunks(chunks)

    q = InterviewQuestion(question_id=2, question_text="What are the main barriers to adoption?")
    meta = parsed["metadata"]

    result = rag_engine.answer_guided_question(q, meta, chunks)
    assert result.question_id == 2
    assert result.expert_id == "expert_1"
    assert len(result.evidence) > 0
    assert result.evidence[0].timestamp == "01:08"

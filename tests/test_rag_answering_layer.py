import pytest
from backend.app.config import DATA_DIR
from backend.app.schemas import TranscriptChunk, RAGAnswerResponse
from backend.app.services.parser import parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.services.vector_store import vector_store
from backend.app.services.validator import validate_and_bind_evidence, validate_evidence_list
from backend.app.services.rag_engine import rag_engine, REFUSAL_MESSAGE


@pytest.fixture(autouse=True)
def setup_vector_store():
    """Initializes vector store with all 3 expert transcripts prior to test execution."""
    vector_store.clear()
    transcript_files = list(DATA_DIR.glob("expert_*.txt"))
    for tf in sorted(transcript_files):
        parsed = parse_transcript(tf)
        chunks = create_turn_chunks(parsed)
        vector_store.add_chunks(chunks)


def test_1_clearly_answered_question():
    """
    Test Case 1: A question clearly answered in transcripts.
    Expects a valid summary answer, HIGH/MEDIUM confidence, and non-empty verified evidence.
    """
    query = "What are the main barriers to adoption of robotic surgery in Germany?"
    response: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query=query, expert_id="expert_2")

    assert response.answer != REFUSAL_MESSAGE
    assert len(response.answer) > 20
    assert len(response.evidence) >= 1
    
    first_ev = response.evidence[0]
    assert first_ev.source == "expert_2.txt"
    assert first_ev.timestamp in ["00:16", "01:10", "01:05", "03:05"]
    assert first_ev.verification_status in ["VERIFIED_EXACT_MATCH", "VERIFIED_FUZZY_MATCH"]


def test_2_unanswered_out_of_scope_question():
    """
    Test Case 2: A question not discussed at all in transcripts.
    Expects the exact refusal message, LOW confidence, and empty evidence list.
    """
    query = "What is the market share of quantum computing in space exploration?"
    response: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query=query)

    assert response.answer == REFUSAL_MESSAGE
    assert response.confidence == "LOW"
    assert len(response.evidence) == 0
    assert response.is_grounded is True


def test_3_quote_exactness_check():
    """
    Test Case 3: Verifies that returned quote exists verbatim in source chunk text.
    Rejects/flags hallucinated or fabricated quotes.
    """
    source_chunk = TranscriptChunk(
        chunk_id="expert_3_turn_02",
        source_file="expert_3.txt",
        expert_id="expert_3",
        expert_name="Dr. Emily Carter",
        expert_role="Consultant Urologist",
        market="United Kingdom",
        question_context="What are the main barriers?",
        speaker="Dr. Carter",
        start_timestamp="01:05",
        end_timestamp="02:02",
        verbatim_text="Dr. Carter: Funding is important, but I would say training capacity is just as important. You can buy a system, but if you cannot train enough surgeons and theatre staff, adoption stalls.",
        raw_lines=["01:05", "Funding is important..."]
    )

    # Valid verbatim quote
    verbatim_quote = "Funding is important, but I would say training capacity is just as important."
    valid_ev = validate_and_bind_evidence(verbatim_quote, "Dr. Carter", "01:05", [source_chunk])
    assert valid_ev.verification_status == "VERIFIED_EXACT_MATCH"

    # Fabricated / hallucinated quote
    hallucinated_quote = "Robotic systems are mandatory across all NHS hospitals by law."
    invalid_ev = validate_and_bind_evidence(hallucinated_quote, "Dr. Carter", "01:05", [source_chunk])
    assert invalid_ev.verification_status == "UNVERIFIED_HALLUCINATION"
    assert invalid_ev.source == "unverified"


def test_4_timestamp_accuracy_check():
    """
    Test Case 4: Verifies that the returned timestamp matches source metadata exactly.
    """
    source_chunk = TranscriptChunk(
        chunk_id="expert_1_turn_02",
        source_file="expert_1.txt",
        expert_id="expert_1",
        expert_name="Dr. Jean-Luc Dubois",
        expert_role="Chief of Surgical Services",
        market="France",
        question_context="What are the main barriers?",
        speaker="Dr. Dubois",
        start_timestamp="01:08",
        end_timestamp="02:00",
        verbatim_text="Dr. Dubois: The initial capital investment remains high, but reimbursement restrictions under the French national health system (Sécurité Sociale) present the biggest hurdle.",
        raw_lines=["01:08", "The initial capital investment..."]
    )

    verbatim_quote = "reimbursement restrictions under the French national health system"
    
    # Even if LLM provides wrong timestamp "05:00", validator binds the verified source timestamp "01:08"
    ev = validate_and_bind_evidence(verbatim_quote, "Dr. Dubois", "05:00", [source_chunk])
    
    assert ev.verification_status == "VERIFIED_EXACT_MATCH"
    assert ev.timestamp == "01:08"  # Timestamp matches source chunk metadata exactly
    assert ev.source == "expert_1.txt"

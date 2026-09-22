import pytest
from backend.app.config import DATA_DIR
from backend.app.schemas import TranscriptChunk, RAGAnswerResponse, SynthesisResult
from backend.app.services.parser import parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.services.vector_store import vector_store
from backend.app.services.validator import normalize_text
from backend.app.services.rag_engine import rag_engine, REFUSAL_MESSAGE


@pytest.fixture(autouse=True)
def setup_vector_store():
    """Initializes vector store with all 3 real expert transcripts prior to test execution."""
    vector_store.clear()
    transcript_files = list(DATA_DIR.glob("expert_*.txt"))
    for tf in sorted(transcript_files):
        parsed = parse_transcript(tf)
        chunks = create_turn_chunks(parsed)
        vector_store.add_chunks(chunks)


def test_1_supported_question():
    """
    Test 1: Supported question — clearly answered in transcripts.
    Expects grounded answer + valid evidence quote from France (expert_1).
    """
    query = "What are the main barriers to adoption in France?"
    response: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query=query, expert_id="expert_1")

    assert response.answer != REFUSAL_MESSAGE
    assert len(response.answer) > 20
    assert len(response.evidence) >= 1

    first_ev = response.evidence[0]
    assert first_ev.source == "expert_1.txt"
    assert first_ev.timestamp in ["01:08", "00:15"]
    assert first_ev.verification_status in ["VERIFIED_EXACT_MATCH", "VERIFIED_FUZZY_MATCH"]


def test_2_unsupported_question():
    """
    Test 2: Unsupported question — not discussed anywhere in transcripts.
    Expects exact refusal message, LOW confidence, and empty evidence list.
    """
    query = "What is the policy on artificial intelligence in autonomous vehicle manufacturing in Japan?"
    response: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query=query)

    assert response.answer == REFUSAL_MESSAGE
    assert response.confidence == "LOW"
    assert len(response.evidence) == 0
    assert response.is_grounded is True


def test_3_exact_quote_test():
    """
    Test 3: Exact-quote test — verifies every returned evidence quote exists verbatim in source text.
    """
    query = "What are the main barriers to adoption across European hospitals?"
    response: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query=query, top_k=5)

    assert len(response.evidence) >= 1
    for ev in response.evidence:
        # Locate corresponding source chunk in vector store
        matching_chunks = [c for c in vector_store.chunks if c.source_file == ev.source]
        assert len(matching_chunks) > 0

        # Verify quote exists as normalized substring inside source chunk verbatim text
        quote_norm = normalize_text(ev.quote)
        found_in_source = any(quote_norm in normalize_text(c.verbatim_text) for c in matching_chunks)
        assert found_in_source is True, f"Quote '{ev.quote}' not found verbatim in source {ev.source}"
        assert ev.verification_status in ["VERIFIED_EXACT_MATCH", "VERIFIED_FUZZY_MATCH"]


def test_4_timestamp_test():
    """
    Test 4: Timestamp test — verifies every returned timestamp matches source metadata exactly.
    """
    query = "How long does purchasing decision timeline take in Germany?"
    response: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query=query, expert_id="expert_2")

    assert len(response.evidence) >= 1
    for ev in response.evidence:
        matching_chunks = [c for c in vector_store.chunks if c.source_file == ev.source and c.start_timestamp == ev.timestamp]
        assert len(matching_chunks) > 0, f"Timestamp '{ev.timestamp}' does not match any source chunk metadata in {ev.source}"


def test_5_cross_call_test():
    """
    Test 5: Cross-call test — a question that requires pulling evidence from more than one expert.
    """
    query = "How do training capacity and surgeon adoption compare across UK and Germany?"
    response: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query=query, top_k=5)

    assert len(response.evidence) >= 2
    sources = set(ev.source for ev in response.evidence)
    assert len(sources) >= 2, f"Cross-call query only pulled from {sources}, expected multiple expert sources."


def test_6_disagreement_test():
    """
    Test 6: Disagreement test — verifies known opposing-views case (pure economics vs balanced clinical ROI)
    is correctly identified as a disagreement and not silently merged into a false common theme.
    """
    synthesis: SynthesisResult = rag_engine.synthesize_themes_and_disagreements(vector_store.chunks)

    assert len(synthesis.disagreements) >= 1
    disagreement = synthesis.disagreements[0]

    assert disagreement.relationship_type in ["DIRECT_DISAGREEMENT", "DIFFERENT_EMPHASIS", "PARTIAL_AGREEMENT"]
    positions_experts = [pos.expert_id for pos in disagreement.expert_positions]
    assert "expert_2" in positions_experts or "expert_3" in positions_experts

    # Verify that opposing view is NOT falsely listed as a common theme title
    theme_titles = [t.theme_title.lower() for t in synthesis.common_themes]
    assert not any("economic case decides" in t for t in theme_titles)

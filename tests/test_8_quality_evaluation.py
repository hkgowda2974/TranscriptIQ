import pytest
from backend.app.schemas import RAGAnswerResponse
from backend.app.services.rag_engine import rag_engine, REFUSAL_MESSAGE
from backend.app.services.vector_store import vector_store
from backend.app.services.parser import parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.config import DATA_DIR


@pytest.fixture(autouse=True, scope="module")
def setup_dataset():
    vector_store.clear()
    for tf in sorted(DATA_DIR.glob("expert_*.txt")):
        parsed = parse_transcript(tf)
        chunks = create_turn_chunks(parsed)
        vector_store.add_chunks(chunks)


def test_q1_cross_market_barriers():
    """
    TEST 1:
    'What are the main barriers to robotic surgery adoption across France, Germany, and the UK, and where do the experts differ?'
    Expected:
    - France evidence about capital/reimbursement
    - Germany evidence about cost/utilization
    - UK evidence about training/procedure volume
    - exact quotes, timestamps, expert names
    - no unrelated procurement/growth evidence
    """
    query = "What are the main barriers to robotic surgery adoption across France, Germany, and the UK, and where do the experts differ?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert res.confidence == "HIGH"
    assert len(res.evidence) >= 3

    sources = {ev.source for ev in res.evidence}
    assert "expert_1.txt" in sources  # France
    assert "expert_2.txt" in sources  # Germany
    assert "expert_3.txt" in sources  # UK

    for ev in res.evidence:
        assert ev.verification_status == "VERIFIED_EXACT_MATCH"
        # No unrelated procurement duration in evidence
        assert "9 to 18 months" not in ev.quote
        assert "12 to 18 percent" not in ev.quote


def test_q2_surgeon_training():
    """
    TEST 2:
    'What do the experts say about surgeon training requirements? Give me the exact quotes, expert names, and timestamps.'
    Expected:
    - France: supervised-case/proctorship evidence
    - Germany: training/utilization evidence
    - UK: trained staff/procedure-volume evidence
    - NO procurement timeline
    - NO unrelated adoption-growth statistics
    """
    query = "What do the experts say about surgeon training requirements? Give me the exact quotes, expert names, and timestamps."
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert len(res.evidence) >= 3

    evidence_text = " ".join([ev.quote.lower() for ev in res.evidence])
    assert "proctorship" in evidence_text or "supervised cases" in evidence_text or "training" in evidence_text
    assert "theatre staff" in evidence_text or "trained" in evidence_text or "training capacity" in evidence_text

    # Verify absence of unrelated procurement timeline or growth stats
    assert "9 to 18 months" not in res.answer
    assert "nine to eighteen" not in res.answer.lower()
    assert "12 to 18 percent" not in res.answer


def test_q3_reimbursement_france():
    """
    TEST 3:
    'How important is reimbursement for robotic surgery adoption in France?'
    Expected:
    - France only
    - reimbursement evidence (DRG/tariff)
    - exact quote, timestamp
    - NO UK evidence, NO Germany evidence, NO generic France adoption statistics
    """
    query = "How important is reimbursement for robotic surgery adoption in France?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert len(res.evidence) >= 1

    for ev in res.evidence:
        assert ev.source == "expert_1.txt"
        assert "France" in ev.expert
        assert any(k in ev.quote.lower() for k in ["reimbursement", "drg", "tariffs", "sécurité sociale"])

    assert not any("expert_2.txt" in ev.source for ev in res.evidence)
    assert not any("expert_3.txt" in ev.source for ev in res.evidence)
    assert "35 percent" not in res.answer


def test_q4_why_adopt_despite_high_cost():
    """
    TEST 4:
    'According to the experts, why might hospitals adopt robotic surgery despite the high initial cost?'
    Expected:
    - only evidence directly supporting benefits/reasons for adoption
    - clinical outcomes, patient benefits, strategic benefits, recruitment, etc. ONLY if directly present in evidence
    - NO procurement timeline unless directly relevant
    - NO unrelated cost statements
    """
    query = "According to the experts, why might hospitals adopt robotic surgery despite the high initial cost?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert len(res.evidence) >= 1

    evidence_text = " ".join([ev.quote.lower() for ev in res.evidence])
    assert any(w in evidence_text for w in ["complication", "length of stay", "length-of-stay", "patient demand", "minimally invasive", "recruitment", "clinical position"])
    assert "9 to 18 months" not in res.answer


def test_q5_intuitive_surgical_market_share_germany():
    """
    TEST 5 - CRITICAL:
    'What is the current market share of Intuitive Surgical in Germany?'
    Expected:
    - REFUSAL: 'I couldn't find sufficient evidence in the provided transcripts to answer this question.'
    - Evidence must be empty.
    - Confidence must be LOW.
    """
    query = "What is the current market share of Intuitive Surgical in Germany?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"
    assert res.is_grounded is True


def test_q6_barriers_more_than_one_expert():
    """
    TEST 6:
    'Which barriers to adoption were mentioned by more than one expert?'
    Expected:
    - only barriers supported by at least 2 distinct experts
    - evidence from every expert used to establish the common theme
    - no unsupported 'all three experts agree' claim without evidence
    """
    query = "Which barriers to adoption were mentioned by more than one expert?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert len(res.evidence) >= 2

    experts = {ev.expert for ev in res.evidence}
    assert len(experts) >= 2  # At least 2 distinct experts


def test_q7_cost_disagreement():
    """
    TEST 7:
    'Do the experts disagree on the importance of cost as a barrier? Explain using evidence from the transcripts.'
    Expected:
    - distinguish disagreement vs different emphasis
    - use evidence from the relevant experts
    - do not manufacture disagreement
    """
    query = "Do the experts disagree on the importance of cost as a barrier? Explain using evidence from the transcripts."
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert "different emphasis" in res.answer.lower()
    assert len(res.evidence) >= 2


def test_q8_intuitive_surgical_revenue():
    """
    TEST 8:
    'What was the 2025 revenue of Intuitive Surgical?'
    Expected:
    - REFUSAL: 'I couldn't find sufficient evidence in the provided transcripts to answer this question.'
    - Evidence empty, confidence LOW
    """
    query = "What was the 2025 revenue of Intuitive Surgical?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"

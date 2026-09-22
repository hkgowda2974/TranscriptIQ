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


def test_acceptance_criteria_a_answerable_german_utilization():
    """
    CRITERIA A: Answerable specific question:
    'What does the German expert say about hospital utilization of robotic systems?'
    (and 'What does the German expert say about hospital utilization?')
    MUST answer using the German utilization evidence.
    """
    queries = [
        "What does the German expert say about hospital utilization of robotic systems?",
        "What does the German expert say about hospital utilization?"
    ]
    for q in queries:
        res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(q)
        assert res.answer != REFUSAL_MESSAGE
        assert res.confidence == "HIGH"
        assert len(res.evidence) >= 1
        assert any(ev.source == "expert_2.txt" for ev in res.evidence)
        assert any("03:05" in ev.timestamp for ev in res.evidence)
        assert any("utilisation will be poor" in ev.quote.lower() for ev in res.evidence)
        assert "Anna Keller" in res.answer or "Germany" in res.answer


def test_acceptance_criteria_b_related_but_insufficient_selling_price():
    """
    CRITERIA B: Related-but-insufficient question:
    'What is the average selling price of a robotic surgical system in Germany?'
    The retrieved TCO evidence mentions cost considerations but contains NO selling price.
    MUST refuse because TCO evidence does not provide a selling price.
    """
    query = "What is the average selling price of a robotic surgical system in Germany?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


def test_acceptance_criteria_c_numeric_year_question_without_data():
    """
    CRITERIA C: Numeric question:
    'How many robotic surgery procedures were performed in Germany in 2025?'
    MUST refuse because no 2025 procedure count exists in transcripts.
    """
    query = "How many robotic surgery procedures were performed in Germany in 2025?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


def test_acceptance_criteria_d_cross_market_training_synthesis():
    """
    CRITERIA D: Cross-market question:
    'How do experts describe training across France, Germany and the UK?'
    MUST retrieve and synthesize relevant training evidence from all required markets.
    """
    query = "How do experts describe training across France, Germany and the UK?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert res.confidence == "HIGH"
    assert len(res.evidence) >= 3

    sources = {ev.source for ev in res.evidence}
    assert "expert_1.txt" in sources  # France
    assert "expert_2.txt" in sources  # Germany
    assert "expert_3.txt" in sources  # United Kingdom

    for ev in res.evidence:
        assert ev.verification_status == "VERIFIED_EXACT_MATCH"


def test_acceptance_criteria_e_unsupported_unrelated_question():
    """
    CRITERIA E: Unsupported unrelated question:
    'What is the population of Germany?'
    MUST refuse.
    """
    query = "What is the population of Germany?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


def test_acceptance_criteria_f_every_claim_has_direct_supporting_evidence():
    """
    CRITERIA F: Every factual claim in the final answer must have direct supporting evidence.
    No ungrounded department counts, timelines, or unevidenced expert positions.
    """
    query = "Where do the experts disagree about cost?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    evidence_text_corpus = " ".join([ev.quote.lower() for ev in res.evidence])
    evidence_experts = {ev.expert.lower() for ev in res.evidence}

    # Verify that every expert cited in referenced_experts or claims has evidence
    for claim in res.claims:
        assert any(claim.expert_name.lower() in exp for exp in evidence_experts)

    # Verify no ungrounded claims about timelines or departments
    assert "4 hospital departments" not in res.answer
    assert "9 to 18 months" not in res.answer

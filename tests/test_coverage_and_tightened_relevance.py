import pytest
from backend.app.schemas import RAGAnswerResponse, AnswerClaimItem
from backend.app.services.rag_engine import rag_engine, REFUSAL_MESSAGE
from backend.app.services.vector_store import vector_store
from backend.app.services.parser import parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.services.coverage_validator import CoverageValidator
from backend.app.services.query_analyzer import QueryAnalyzer
from backend.app.config import DATA_DIR


@pytest.fixture(autouse=True, scope="module")
def setup_dataset():
    vector_store.clear()
    for tf in sorted(DATA_DIR.glob("expert_*.txt")):
        parsed = parse_transcript(tf)
        chunks = create_turn_chunks(parsed)
        vector_store.add_chunks(chunks)


def test_cost_disagreement_claim_evidence_coverage():
    """
    BUG REPRODUCTION & RESOLUTION TEST:
    Query: 'Where do the experts disagree about cost?'
    Assert that every expert named or referenced in the narrative text or Bottom Line
    has at least one matching evidence item in the response evidence list.
    Specifically, all 3 experts (France, Germany, UK) must have citations attached.
    """
    query = "Where do the experts disagree about cost?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert len(res.evidence) >= 3

    evidence_sources = {ev.source for ev in res.evidence}
    assert "expert_1.txt" in evidence_sources, "Missing France (Dr. Dubois) evidence citation"
    assert "expert_2.txt" in evidence_sources, "Missing Germany (Anna Keller) evidence citation"
    assert "expert_3.txt" in evidence_sources, "Missing UK (Dr. Carter) evidence citation"

    # Verify coverage invariant: every expert referenced in text must have an evidence item
    text_lower = res.answer.lower()
    if "dubois" in text_lower or "france" in text_lower:
        assert any("expert_1.txt" in ev.source for ev in res.evidence)
    if "keller" in text_lower or "germany" in text_lower:
        assert any("expert_2.txt" in ev.source for ev in res.evidence)
    if "carter" in text_lower or "united kingdom" in text_lower or "uk" in text_lower:
        assert any("expert_3.txt" in ev.source for ev in res.evidence)


def test_cost_disagreement_alternative_phrasing_coverage():
    """
    Query: 'Do the experts disagree on the importance of cost as a barrier? Explain using evidence from the transcripts.'
    Assert claim-evidence coverage across all mentioned experts.
    """
    query = "Do the experts disagree on the importance of cost as a barrier? Explain using evidence from the transcripts."
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    evidence_sources = {ev.source for ev in res.evidence}
    assert len(evidence_sources) >= 2

    # Check that any expert mentioned in the answer has a matching citation
    text_lower = res.answer.lower()
    if "dubois" in text_lower or "france" in text_lower:
        assert any("expert_1.txt" in ev.source for ev in res.evidence)
    if "keller" in text_lower or "germany" in text_lower:
        assert any("expert_2.txt" in ev.source for ev in res.evidence)
    if "carter" in text_lower or "uk" in text_lower or "united kingdom" in text_lower:
        assert any("expert_3.txt" in ev.source for ev in res.evidence)


def test_tightened_training_relevance():
    """
    RELEVANCE TIGHTENING TEST:
    Query: 'What do the experts say about surgeon training requirements? Give me the exact quotes, expert names, and timestamps.'
    Assert that:
    1. Loose procurement-economics quotes mentioning training in passing (e.g. Keller 02:08) are NOT in evidence.
    2. Evidence is trimmed/capped to top direct training quotes.
    3. Direct training quotes (Dubois 03:06, Keller 03:05, Carter 01:05) are returned.
    """
    query = "What do the experts say about surgeon training requirements? Give me the exact quotes, expert names, and timestamps."
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE

    for ev in res.evidence:
        # Keller 02:08 should NOT be present (loose procurement quote)
        assert "total cost of ownership" not in ev.quote.lower(), "Tangential procurement quote Keller 02:08 found in training evidence"
        assert "economic case decides" not in ev.quote.lower(), "Tangential economic approval quote found in training evidence"

    # Verify presence of direct training quotes
    quotes_text = " ".join([ev.quote.lower() for ev in res.evidence])
    assert "proctorship" in quotes_text or "supervised cases" in quotes_text  # Dubois 03:06
    assert "comfortable using it" in quotes_text or "utilisation will be poor" in quotes_text  # Keller 03:05
    assert "training capacity" in quotes_text or "train enough" in quotes_text  # Carter 01:05


def test_option_b_claim_stripping_when_evidence_unfindable():
    """
    Asserts Option B behavior: if narrative text claims an expert for which NO evidence exists in the corpus,
    the unsupported claim is stripped from the text and a warning is logged.
    """
    synthetic_answer = (
        "Here are the expert viewpoints:\n\n"
        "* **Dr. Emily Carter (United Kingdom)**: \"Funding is important, but I would say training capacity is just as important.\"\n\n"
        "* **Dr. Phantom (Japan)**: \"Robotic surgery is completely unsupported in our market.\"\n\n"
        "📌 **Bottom Line**: The UK is constrained by training capacity, while Japan is constrained by lack of approval."
    )
    synthetic_claims = [
        AnswerClaimItem(expert_name="Dr. Emily Carter", market="United Kingdom", claim_text="Funding vs training"),
        AnswerClaimItem(expert_name="Dr. Phantom", market="Japan", claim_text="Robotic surgery unsupported")
    ]
    from backend.app.schemas import RAGEvidenceItem
    synthetic_evidence = [
        RAGEvidenceItem(
            expert="Dr. Emily Carter (United Kingdom)",
            timestamp="01:05",
            quote="Funding is important, but I would say training capacity is just as important.",
            source="expert_3.txt",
            verification_status="VERIFIED_EXACT_MATCH"
        )
    ]
    query = QueryAnalyzer.analyze("What are the training barriers in the UK?")

    final_answer, final_claims, final_refs, final_ev = CoverageValidator.enforce_claim_evidence_coverage(
        answer_text=synthetic_answer,
        claims=synthetic_claims,
        evidence=synthetic_evidence,
        query=query,
        all_chunks=vector_store.chunks
    )

    # Japan / Dr. Phantom must be stripped
    assert "Phantom" not in final_answer
    assert len(final_ev) == 1
    assert final_ev[0].source == "expert_3.txt"

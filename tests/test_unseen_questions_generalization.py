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


# 1. Direct factual question
def test_1_direct_factual_question():
    query = "What supervised case volume is required for a surgeon to operate independently in France?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert "30 to 50" in res.answer
    assert any(ev.source == "expert_1.txt" for ev in res.evidence)
    assert any("03:06" in ev.timestamp for ev in res.evidence)


# 2. Specific topic
def test_2_specific_topic_length_of_stay():
    query = "How does robotic surgery affect hospital length of stay and complication rates according to the experts?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    evidence_text = " ".join([ev.quote.lower() for ev in res.evidence])
    assert "length of stay" in evidence_text or "length-of-stay" in evidence_text
    assert "complication" in evidence_text


# 3. Single market
def test_3_single_market_germany():
    query = "What did Anna Keller say about competing capital priorities and adoption pace in Germany?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    for ev in res.evidence:
        assert ev.source == "expert_2.txt"
        assert "Germany" in ev.expert
    assert not any("expert_1.txt" in ev.source for ev in res.evidence)
    assert not any("expert_3.txt" in ev.source for ev in res.evidence)


# 4. Multi-market
def test_4_multi_market_purchase_timelines():
    query = "How long can the purchase process take in Germany compared to France?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    sources = {ev.source for ev in res.evidence}
    assert "expert_1.txt" in sources  # France (6 to 9 months)
    assert "expert_2.txt" in sources  # Germany (9 to 18 months)


# 5. Common theme
def test_5_common_theme_sustainability():
    query = "Which barriers or operational factors are shared between Germany and the UK regarding training?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert len(res.evidence) >= 2
    experts = {ev.expert for ev in res.evidence}
    assert len(experts) >= 2


# 6. Disagreement / Difference in emphasis
def test_6_disagreement_procurement_philosophy():
    query = "How do the procurement philosophies in Germany and the UK contrast regarding pure financial metrics?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    evidence_text = " ".join([ev.quote.lower() for ev in res.evidence])
    assert "economic case" in evidence_text or "finance alone" in evidence_text or "balanced" in evidence_text


# 7. Multi-part question
def test_7_multipart_question_with_unsupported_part():
    query = "What is the capital investment barrier in France, and what is the exact 2026 robotic surgery budget for Paris hospitals?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    # France capital investment barrier is answered, and unsupported part is noted
    assert res.answer != REFUSAL_MESSAGE
    assert "expert_1.txt" in [ev.source for ev in res.evidence]
    assert "transcripts do not contain" in res.answer.lower() or "not supported" in res.answer.lower()


# 8. Numerical question
def test_8_numerical_question():
    query = "How many supervised cases does a surgeon need before operating independently?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert "30 to 50" in res.answer
    assert any("30 to 50" in ev.quote for ev in res.evidence)


# 9. Unsupported entity
def test_9_unsupported_entity_medtronic():
    query = "How many Medtronic Hugo systems are currently installed in German hospitals?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


# 10. Unsupported metric
def test_10_unsupported_metric_profit_margin():
    query = "What is the exact profit margin for robotic surgery procedures in UK NHS trusts?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


# 11. Unsupported country
def test_11_unsupported_country_spain():
    query = "What are the reimbursement tariffs for robotic surgery in Spain?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


# 12. Temporal question
def test_12_unsupported_temporal_question():
    query = "What was the robotic surgery adoption percentage across Europe in 2015?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


# 13. Partially answerable question
def test_13_partially_answerable_question():
    query = "How long does a purchase decision take in France, and what is the exact brand preference of Paris surgeons?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    assert any("05:05" in ev.timestamp for ev in res.evidence)
    assert "transcripts do not contain" in res.answer.lower() or "not supported" in res.answer.lower()


# 14. Ambiguous / out of domain question
def test_14_ambiguous_out_of_domain():
    query = "What is the average weather and temperature in Paris during the spring?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer == REFUSAL_MESSAGE
    assert len(res.evidence) == 0
    assert res.confidence == "LOW"


# 15. Question requiring comparison
def test_15_comparison_private_vs_public():
    query = "How does the adoption pace differ between private clinics and public university hospitals in France?"
    res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query)

    assert res.answer != REFUSAL_MESSAGE
    evidence_text = " ".join([ev.quote.lower() for ev in res.evidence])
    assert "private clinics" in evidence_text
    assert "public university hospitals" in evidence_text or "chus" in evidence_text

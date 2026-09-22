from backend.app.schemas import RAGAnswerResponse
from backend.app.services.rag_engine import rag_engine, REFUSAL_MESSAGE
from backend.app.services.parser import parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.services.vector_store import vector_store
from backend.app.config import DATA_DIR


def setup_data():
    vector_store.clear()
    for tf in sorted(DATA_DIR.glob("expert_*.txt")):
        content = tf.read_text(encoding="utf-8")
        parsed = parse_transcript(content, tf.name)
        chunks = create_turn_chunks(parsed)
        vector_store.add_chunks(chunks)


def test_10_required_questions():
    setup_data()

    questions = [
        "What are the main adoption barriers in Germany vs the UK?",
        "What do the experts say about surgeon training and training requirements?",
        "How important are financial considerations when hospitals decide whether to purchase a robotic surgery system?",
        "What factors do hospitals consider when evaluating the ROI of robotic surgery?",
        "How important is reimbursement in France?",
        "Which barriers were mentioned by more than one expert?",
        "Give me the strongest evidence that training is a barrier to adoption.",
        "According to the experts, why might a hospital want to adopt robotic surgery despite the high initial cost?",
        "Which issues appear to be market-specific rather than common across all three countries?",
        "What is the current market share of Intuitive Surgical in Germany?"
    ]

    results = []

    for idx, q in enumerate(questions, 1):
        res: RAGAnswerResponse = rag_engine.execute_rag_pipeline(query=q)
        results.append((idx, q, res))

        print(f"\n==========================================")
        print(f"Q{idx}: {q}")
        print(f"------------------------------------------")
        print(f"ANSWER:\n{res.answer}")
        print(f"CONFIDENCE: {res.confidence} | GROUNDED: {res.is_grounded}")
        print(f"EVIDENCE QUOTES ({len(res.evidence)}):")
        for ev in res.evidence:
            print(f" - [{ev.expert} | {ev.timestamp} | {ev.source}]: \"{ev.quote}\" ({ev.verification_status})")

    q5_res = results[4][2]
    assert q5_res.answer != REFUSAL_MESSAGE
    assert any("expert_1.txt" in ev.source for ev in q5_res.evidence)
    assert not any("expert_2.txt" in ev.source for ev in q5_res.evidence)

    q10_res = results[9][2]
    assert q10_res.answer == REFUSAL_MESSAGE
    assert len(q10_res.evidence) == 0
    assert q10_res.confidence == "LOW"


if __name__ == "__main__":
    test_10_required_questions()

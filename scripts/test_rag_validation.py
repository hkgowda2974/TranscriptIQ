import sys
import json
from pathlib import Path

# Force UTF-8 output encoding for Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import DATA_DIR
from backend.app.services.parser import parse_interview_guide, parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.services.vector_store import vector_store
from backend.app.services.rag_engine import rag_engine


def main():
    print("=" * 80)
    print("PHASE 4 AUDIT: RAG REASONING & EVIDENCE VALIDATION TEST")
    print("=" * 80)

    # 1. Ingest Data into Vector Store
    vector_store.clear()
    objective, questions = parse_interview_guide(DATA_DIR / "interview_guide.txt")
    
    transcript_files = list(DATA_DIR.glob("expert_*.txt"))
    all_chunks = []
    experts = []

    for tf in sorted(transcript_files):
        parsed = parse_transcript(tf)
        experts.append(parsed["metadata"])
        chunks = create_turn_chunks(parsed)
        all_chunks.extend(chunks)
        vector_store.add_chunks(chunks)

    print(f"\n[INGESTION COMPLETE] {len(experts)} experts loaded, {len(all_chunks)} chunks indexed.")
    print("=" * 80)

    # 2. Test Guided Q&A Answer Generation for Question 2 across Experts
    q2 = questions[1] # Q2: What are the main barriers to adoption?
    print(f"\n>>> AUDIT 1: GUIDED Q&A MATRIX ANSWER (Question: '{q2.question_text}')")
    
    for expert in experts:
        res = rag_engine.answer_guided_question(q2, expert, all_chunks)
        print(f"\n--- Expert: {res.expert_name} ({res.market}) ---")
        print(f"Summary Answer: {res.summary_answer}")
        print(f"Evidence Quotes Count: {len(res.evidence)}")
        for ev in res.evidence:
            print(f"  * Quote: \"{ev.quote}\"")
            print(f"    Speaker: {ev.speaker} | Timestamp: {ev.start_timestamp} - {ev.end_timestamp} | Status: {ev.verification_status}")

    # 3. Test Cross-Expert Synthesis (Themes & Disagreements)
    print("\n" + "=" * 80)
    print(">>> AUDIT 2: CROSS-EXPERT SYNTHESIS (THEMES & DISAGREEMENTS)")
    print("=" * 80)

    synthesis = rag_engine.synthesize_themes_and_disagreements(all_chunks)
    
    print("\n[COMMON THEMES FOUND]")
    for theme in synthesis.common_themes:
        print(f"\n[THEME] {theme.theme_title}")
        print(f"  Description: {theme.description}")
        print(f"  Supporting Experts: {', '.join(theme.supporting_experts)}")
        for ev in theme.key_evidence:
            print(f"  * Key Quote: \"{ev.quote}\" (Speaker: {ev.speaker}, Timestamp: {ev.start_timestamp}, Status: {ev.verification_status})")

    print("\n[DISAGREEMENTS / DIFFERENCES FOUND]")
    for dis in synthesis.disagreements:
        print(f"\n[CONFLICT] Topic: {dis.topic}")
        print(f"  Description: {dis.description}")
        for pos in dis.expert_positions:
            print(f"  * {pos.expert_name} ({pos.market}): {pos.position_summary}")
            print(f"    Quote: \"{pos.verbatim_quote}\" (Timestamp: {pos.timestamp})")

    # 4. Test Custom Cross-Transcript Q&A
    print("\n" + "=" * 80)
    print(">>> AUDIT 3: CUSTOM AD-HOC CROSS-TRANSCRIPT Q&A")
    print("=" * 80)

    query = "How long does purchasing decision take in Germany vs UK?"
    qa_res = rag_engine.custom_qa(query)
    
    print(f"\nUser Query: '{qa_res.query}'")
    print(f"Answer Summary: {qa_res.answer_summary}")
    print(f"Evidence Quotes:")
    for ev in qa_res.evidence:
        print(f"  * \"{ev.quote}\" ({ev.speaker} @ {ev.start_timestamp}, Status: {ev.verification_status})")

    print("\n" + "=" * 80)
    print("PHASE 4 RAG REASONING & VALIDATION AUDIT COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()

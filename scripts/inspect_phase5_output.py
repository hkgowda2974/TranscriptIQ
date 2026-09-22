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
    print("PHASE 5 AUDIT: CROSS-TRANSCRIPT ANALYSIS SAMPLES")
    print("=" * 80)

    # Ingest All Transcripts
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

    # 1. Sample Output: One Interview-Guide Question Answered (Q2)
    q2 = questions[1] # Q2: What are the main barriers to adoption?
    print(f"\n1. SAMPLE INTERVIEW-GUIDE QUESTION ANSWERED")
    print(f"   Question ID: Q{q2.question_id}")
    print(f"   Question Text: '{q2.question_text}'")
    print("-" * 80)

    for expert in experts:
        res = rag_engine.answer_guided_question(q2, expert, all_chunks)
        print(f"\n[EXPERT]: {res.expert_name} ({res.market}) - Role: {expert.role}")
        print(f"  Summary Answer: {res.summary_answer}")
        print(f"  Key Findings:")
        for kf in res.key_findings:
            print(f"    - {kf}")
        print(f"  Supporting Evidence:")
        for ev in res.evidence:
            print(f"    * Quote: \"{ev.quote}\"")
            print(f"      Source: {ev.source} | Timestamp: {ev.timestamp} | Status: {ev.verification_status}")

    # 2. Sample Output: One Common Theme (Multi-Transcript Supported)
    synthesis = rag_engine.synthesize_themes_and_disagreements(all_chunks)
    theme = synthesis.common_themes[0]
    
    print("\n" + "=" * 80)
    print(f"2. SAMPLE COMMON THEME (Multi-Transcript Supported)")
    print("-" * 80)
    print(f"Title: {theme.theme_title}")
    print(f"Description: {theme.description}")
    print(f"Supporting Experts: {', '.join(theme.supporting_experts)}")
    print(f"Per-Expert Evidence:")
    for pe in theme.per_expert_evidence:
        print(f"\n  [Expert]: {pe.expert_name} ({pe.market})")
        print(f"  Position Summary: {pe.position_summary}")
        for ev in pe.evidence_quotes:
            print(f"  * Verbatim Quote: \"{ev.quote}\"")
            print(f"    Source: {ev.source} | Timestamp: {ev.timestamp} | Status: {ev.verification_status}")

    # 3. Sample Output: One Disagreement / Difference
    disagreement = synthesis.disagreements[0]
    print("\n" + "=" * 80)
    print(f"3. SAMPLE DISAGREEMENT / DIFFERENCE FINDING")
    print("-" * 80)
    print(f"Topic: {disagreement.topic}")
    print(f"Relationship Type: {disagreement.relationship_type}")
    print(f"Description: {disagreement.description}")
    print(f"Expert Positions:")
    for pos in disagreement.expert_positions:
        print(f"\n  [Expert]: {pos.expert_name} ({pos.market})")
        print(f"  Position Summary: {pos.position_summary}")
        print(f"  Verbatim Quote: \"{pos.verbatim_quote}\"")
        print(f"  Source: {pos.source} | Timestamp: {pos.timestamp}")

    print("\n" + "=" * 80)
    print("PHASE 5 AUDIT COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()

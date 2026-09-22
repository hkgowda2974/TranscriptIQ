import sys
import json
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import DATA_DIR
from backend.app.services.parser import parse_interview_guide, parse_transcript
from backend.app.services.chunker import create_turn_chunks


def main():
    print("=" * 80)
    print("PHASE 2 DATA PROCESSING AUDIT: PARSED INTERVIEW GUIDE & TRANSCRIPT CHUNKS")
    print("=" * 80)

    # 1. Parse Interview Guide
    guide_path = DATA_DIR / "interview_guide.txt"
    objective, questions = parse_interview_guide(guide_path)
    print(f"\n[INTERVIEW GUIDE]")
    print(f"Objective: {objective}")
    print(f"Questions Count: {len(questions)}")
    for q in questions:
        print(f"  Q{q.question_id}: {q.question_text}")

    print("\n" + "=" * 80)
    print("TRANSCRIPT PARSED CHUNKS SAMPLES")
    print("=" * 80)

    # 2. Parse all 3 Expert Transcripts
    transcript_files = list(DATA_DIR.glob("expert_*.txt"))
    for tf in sorted(transcript_files):
        parsed = parse_transcript(tf)
        metadata = parsed["metadata"]
        chunks = create_turn_chunks(parsed)
        
        print(f"\n--------------------------------------------------------------------------------")
        print(f"EXPERT FILE: {tf.name}")
        print(f"EXPERT ID: {metadata.expert_id} | NAME: {metadata.name} | MARKET: {metadata.market} | ROLE: {metadata.role}")
        print(f"TOTAL TURNS: {len(parsed['turns'])} | TOTAL CHUNKS: {len(chunks)}")
        print(f"--------------------------------------------------------------------------------")

        # Show sample chunk (e.g. Chunk 2 or Chunk 1)
        sample_chunks = chunks[:2] if len(chunks) >= 2 else chunks
        for idx, chunk in enumerate(sample_chunks, 1):
            print(f"\n--- Sample Chunk #{idx} ({chunk.chunk_id}) ---")
            print(json.dumps(chunk.dict(), indent=2))

if __name__ == "__main__":
    main()

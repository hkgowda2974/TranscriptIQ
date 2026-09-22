import sys
import json
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.config import DATA_DIR
from backend.app.services.parser import parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.services.vector_store import vector_store


def main():
    print("=" * 80)
    print("PHASE 3 RETRIEVAL TEST & SANITY-CHECK AUDIT")
    print("=" * 80)

    # 1. Load and Index Transcripts
    vector_store.clear()
    transcript_files = list(DATA_DIR.glob("expert_*.txt"))
    total_indexed = 0

    for tf in sorted(transcript_files):
        parsed = parse_transcript(tf)
        chunks = create_turn_chunks(parsed)
        vector_store.add_chunks(chunks)
        total_indexed += len(chunks)

    print(f"\n[INDEXING COMPLETED] Indexed {total_indexed} chunks across {len(transcript_files)} expert transcripts.")
    print("=" * 80)

    # 2. Test Queries
    test_queries = [
        {
            "title": "Query 1: Unfiltered Global Search across all experts",
            "query": "What are the main barriers to adoption of robotic surgery?",
            "filter_expert": None,
            "top_k": 3
        },
        {
            "title": "Query 2: Metadata-Filtered Search (Germany - Expert 2)",
            "query": "How long does the purchasing decision timeline take?",
            "filter_expert": "expert_2",
            "top_k": 2
        },
        {
            "title": "Query 3: Metadata-Filtered Search (UK - Expert 3)",
            "query": "How important is surgeon training and NHS adoption?",
            "filter_expert": "expert_3",
            "top_k": 2
        },
        {
            "title": "Query 4: Metadata-Filtered Search (France - Expert 1)",
            "query": "What are the reimbursement restrictions under national health system?",
            "filter_expert": "expert_1",
            "top_k": 2
        }
    ]

    for q_item in test_queries:
        print(f"\n>>> {q_item['title']}")
        print(f"    Query Text: '{q_item['query']}'")
        print(f"    Metadata Filter (expert_id): {q_item['filter_expert']}")
        
        results = vector_store.search(
            query=q_item['query'],
            top_k=q_item['top_k'],
            expert_id=q_item['filter_expert']
        )

        print(f"    Retrieved {len(results)} Chunks:")
        for idx, chunk in enumerate(results, 1):
            print(f"\n    Match #{idx}: [{chunk.chunk_id}]")
            print(f"      Expert: {chunk.expert_name} ({chunk.market})")
            print(f"      Timestamps: {chunk.start_timestamp} - {chunk.end_timestamp}")
            print(f"      Context Question: {chunk.question_context}")
            print(f"      Verbatim Text Snippet: {chunk.verbatim_text[:160]}...")

    print("\n" + "=" * 80)
    print("RETRIEVAL SANITY-CHECK COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()

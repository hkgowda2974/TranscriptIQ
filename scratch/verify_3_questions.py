import sys
import io
import os

sys.path.insert(0, os.path.abspath("."))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.app.services.rag_engine import rag_engine, REFUSAL_MESSAGE
from backend.app.services.vector_store import vector_store
from backend.app.services.parser import parse_transcript
from backend.app.services.chunker import create_turn_chunks
from backend.app.config import DATA_DIR

vector_store.clear()
for tf in sorted(DATA_DIR.glob("expert_*.txt")):
    parsed = parse_transcript(tf)
    chunks = create_turn_chunks(parsed)
    vector_store.add_chunks(chunks)

questions = [
    "How important is reimbursement for robotic surgery adoption in France?",
    "What do the experts say about surgeon training requirements?",
    "What is the current market share of Intuitive Surgical in Germany?"
]

for idx, q in enumerate(questions, 1):
    res = rag_engine.execute_rag_pipeline(query=q)
    print(f"\n==========================================")
    print(f"Q{idx}: {q}")
    print(f"------------------------------------------")
    print(f"ANSWER:\n{res.answer}")
    print(f"CONFIDENCE: {res.confidence} | GROUNDED: {res.is_grounded}")
    print(f"EVIDENCE QUOTES ({len(res.evidence)}):")
    for ev in res.evidence:
        print(f" - [{ev.expert} | {ev.timestamp} | {ev.source}]: \"{ev.quote}\" ({ev.verification_status})")

"""
Intent detection and chunk relevance adapter.
Wraps QueryAnalyzer and EvidenceEvaluator for modular evidence qualification.
"""
from typing import List, Optional, Tuple, Dict, Any
from backend.app.schemas import TranscriptChunk
from backend.app.services.query_analyzer import (
    QueryAnalyzer,
    StructuredQuery,
    QueryIntent,
    SUPPORTED_MARKETS,
    UNSUPPORTED_ENTITIES,
    UNSUPPORTED_METRICS,
    UNSUPPORTED_GEOGRAPHIES,
    UNSUPPORTED_TOPICS
)
from backend.app.services.evidence_evaluator import EvidenceEvaluator, is_chunk_relevant


def detect_query_intent(query: str) -> StructuredQuery:
    """Entrypoint function preserving full backward compatibility."""
    return QueryAnalyzer.analyze(query)

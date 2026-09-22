import re
import logging
from difflib import SequenceMatcher
from typing import List, Tuple
from backend.app.schemas import RAGEvidenceItem, TranscriptChunk

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Removes punctuation and extra whitespaces for resilient substring matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def validate_and_bind_evidence(
    claimed_quote: str,
    claimed_expert: str,
    claimed_timestamp: str,
    retrieved_chunks: List[TranscriptChunk]
) -> RAGEvidenceItem:
    """
    Validates an LLM-claimed quote against actual retrieved source chunks.
    Verifies verbatim text integrity, binds exact source metadata and timestamp, and assigns match status.
    """
    if not claimed_quote or not claimed_quote.strip():
        return RAGEvidenceItem(
            expert=claimed_expert if claimed_expert else "Unknown Expert",
            timestamp=claimed_timestamp if claimed_timestamp else "00:00",
            quote="",
            source="unknown",
            verification_status="UNVERIFIED_HALLUCINATION"
        )

    claimed_norm = normalize_text(claimed_quote)
    best_match_chunk = None
    best_score = 0.0
    exact_found = False

    for chunk in retrieved_chunks:
        chunk_text_norm = normalize_text(chunk.verbatim_text)

        # 1. Exact Substring Verification
        if claimed_norm in chunk_text_norm or normalize_text(claimed_quote) in chunk_text_norm:
            best_match_chunk = chunk
            exact_found = True
            best_score = 1.0
            break

        # 2. Sequence Similarity for minor whitespace/punctuation variations
        similarity = SequenceMatcher(None, claimed_norm, chunk_text_norm).ratio()
        if similarity > best_score:
            best_score = similarity
            best_match_chunk = chunk

    if exact_found and best_match_chunk:
        logger.info(f"Verified exact quote match in chunk {best_match_chunk.chunk_id}.")
        return RAGEvidenceItem(
            expert=f"{best_match_chunk.expert_name} ({best_match_chunk.market})",
            timestamp=best_match_chunk.start_timestamp,  # Bind verified source timestamp
            quote=claimed_quote.strip(),
            source=best_match_chunk.source_file,
            verification_status="VERIFIED_EXACT_MATCH"
        )
    elif best_score >= 0.80 and best_match_chunk:
        logger.info(f"Verified fuzzy quote match (score={best_score:.2f}) in chunk {best_match_chunk.chunk_id}.")
        return RAGEvidenceItem(
            expert=f"{best_match_chunk.expert_name} ({best_match_chunk.market})",
            timestamp=best_match_chunk.start_timestamp,
            quote=claimed_quote.strip(),
            source=best_match_chunk.source_file,
            verification_status="VERIFIED_FUZZY_MATCH"
        )
    else:
        logger.warning(f"Quote failed validation (best score={best_score:.2f}). Flagged as UNVERIFIED_HALLUCINATION.")
        return RAGEvidenceItem(
            expert=claimed_expert if claimed_expert else "Unknown Expert",
            timestamp=claimed_timestamp if claimed_timestamp else "00:00",
            quote=claimed_quote.strip(),
            source="unverified",
            verification_status="UNVERIFIED_HALLUCINATION"
        )


def validate_evidence_list(
    raw_evidence_list: List[dict],
    retrieved_chunks: List[TranscriptChunk]
) -> Tuple[List[RAGEvidenceItem], bool]:
    """
    Validates a list of raw evidence dictionaries against retrieved source chunks.
    Returns (validated_evidence_items, is_fully_grounded).
    """
    validated_items: List[RAGEvidenceItem] = []
    is_grounded = True

    for item in raw_evidence_list:
        quote = item.get("quote", "")
        expert = item.get("expert", "Expert")
        timestamp = item.get("timestamp", "00:00")

        if not quote:
            continue

        item_result = validate_and_bind_evidence(quote, expert, timestamp, retrieved_chunks)
        if item_result.verification_status == "UNVERIFIED_HALLUCINATION":
            is_grounded = False
        else:
            validated_items.append(item_result)

    return validated_items, is_grounded

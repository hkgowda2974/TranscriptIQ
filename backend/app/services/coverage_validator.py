import re
import logging
from typing import List, Dict, Any, Tuple, Set, Optional
from backend.app.schemas import (
    RAGEvidenceItem,
    AnswerClaimItem,
    TranscriptChunk
)
from backend.app.services.query_analyzer import StructuredQuery
from backend.app.services.evidence_evaluator import EvidenceEvaluator
from backend.app.services.validator import validate_evidence_list

logger = logging.getLogger(__name__)

EXPERT_MAP = {
    "expert_1": {"name": "Dr. Jean-Luc Dubois", "market": "France", "file": "expert_1.txt", "aliases": ["dubois", "france", "jean-luc"]},
    "expert_2": {"name": "Anna Keller", "market": "Germany", "file": "expert_2.txt", "aliases": ["keller", "germany", "anna"]},
    "expert_3": {"name": "Dr. Emily Carter", "market": "United Kingdom", "file": "expert_3.txt", "aliases": ["carter", "united kingdom", "uk", "emily"]}
}


class CoverageValidator:
    """
    Claim-Evidence Coverage Validation Layer.
    Enforces the invariant:
    EVERY EXPERT REFERENCED IN THE ANSWER OR BOTTOM LINE MUST HAVE AT LEAST
    ONE VALIDATED, RELEVANT EVIDENCE ITEM IN THE RESPONSE'S EVIDENCE LIST.

    If an expert is referenced in narrative text/claims but lacks evidence:
    - Option A: Re-queries retrieval specifically for that expert and attaches supporting evidence.
    - Option B: If no supporting evidence exists, strips the unsupported claim from the text with a logged warning.
    """

    @staticmethod
    def extract_referenced_experts(answer_text: str, claims: List[AnswerClaimItem]) -> Set[str]:
        """
        Extracts expert labels referenced in either structured claims or free text narrative.
        """
        referenced_labels = set()

        # 1. From structured claims
        for claim in claims:
            if claim.expert_name:
                referenced_labels.add(claim.expert_name.strip())

        # 2. From narrative bullet headers e.g. "* **Dr. Emily Carter (United Kingdom)**:"
        bullet_headers = re.findall(r"\*\s+\*\*([^*:\n]+)\*\*:", answer_text)
        for h in bullet_headers:
            clean_h = h.strip()
            if not any(stop in clean_h.lower() for stop in ["bottom line", "where the experts differ", "takeaway"]):
                referenced_labels.add(clean_h)

        return referenced_labels

    @staticmethod
    def _is_expert_evidenced(label: str, evidence: List[RAGEvidenceItem]) -> bool:
        """Checks if a given expert label has at least one matching evidence item."""
        label_lower = label.lower()
        for ev in evidence:
            ev_expert = ev.expert.lower()
            ev_source = ev.source.lower()
            # Direct name overlap or filename match
            if any(part in ev_expert for part in re.findall(r"\w+", label_lower) if len(part) > 3):
                return True
            for exp_id, meta in EXPERT_MAP.items():
                if any(alias in label_lower for alias in meta["aliases"]) and (meta["file"] in ev_source or any(alias in ev_expert for alias in meta["aliases"])):
                    return True
        return False

    @staticmethod
    def enforce_claim_evidence_coverage(
        answer_text: str,
        claims: List[AnswerClaimItem],
        evidence: List[RAGEvidenceItem],
        query: StructuredQuery,
        all_chunks: List[TranscriptChunk]
    ) -> Tuple[str, List[AnswerClaimItem], List[str], List[RAGEvidenceItem]]:
        """
        Validates that every referenced expert has supporting evidence.
        Applies Option A (targeted retrieval attachment) and Option B (unsupported claim stripping).
        """
        referenced_labels = CoverageValidator.extract_referenced_experts(answer_text, claims)
        from backend.app.services.vector_store import vector_store

        missing_labels = [
            lbl for lbl in referenced_labels
            if not CoverageValidator._is_expert_evidenced(lbl, evidence)
        ]

        # -------------------------------------------------------------
        # OPTION A: Re-query retrieval for missing known experts
        # -------------------------------------------------------------
        still_missing: Set[str] = set()

        for label in missing_labels:
            matched_exp_id = None
            lbl_lower = label.lower()
            for exp_id, meta in EXPERT_MAP.items():
                if any(alias in lbl_lower for alias in meta["aliases"]):
                    matched_exp_id = exp_id
                    break

            if matched_exp_id:
                logger.info(f"CoverageValidator [Option A Re-query]: Searching evidence for {matched_exp_id} ({label}).")
                target_chunks = vector_store.search(
                    query=query.raw_query,
                    top_k=3,
                    expert_id=matched_exp_id
                )
                candidate_quotes = []
                for chunk in target_chunks:
                    cat, quotes, reason = EvidenceEvaluator.evaluate_chunk(chunk, query)
                    if cat == "DIRECT_SUPPORT" and quotes:
                        candidate_quotes.extend(quotes)

                if candidate_quotes:
                    validated_quotes, is_grounded = validate_evidence_list([candidate_quotes[0]], all_chunks)
                    if validated_quotes:
                        evidence.extend(validated_quotes)
                        logger.info(f"CoverageValidator [Option A Success]: Attached quote for {label} at {validated_quotes[0].timestamp}.")
                        continue

            still_missing.add(label)

        # -------------------------------------------------------------
        # OPTION B: Strip unsupported claims for any still-missing expert
        # -------------------------------------------------------------
        final_answer = answer_text
        if still_missing:
            for unbacked_label in still_missing:
                logger.warning(
                    f"CoverageValidator [Option B Executed]: Stripping unsupported claim for '{unbacked_label}' "
                    f"because no supporting evidence could be found in the transcripts."
                )

                # Strip bullet points mentioning this unbacked expert
                escaped_label = re.escape(unbacked_label)
                bullet_pattern = rf"\*\s+\*\*{escaped_label}\*\*.*?(?=(\n\*|\n\n📌|\Z))"
                final_answer = re.sub(bullet_pattern, "", final_answer, flags=re.IGNORECASE | re.DOTALL)

                # Strip mention from Bottom Line if present
                for term in [unbacked_label] + re.findall(r"\w+", unbacked_label):
                    if len(term) > 3:
                        bl_pattern = rf"(?:,\s*)?(?:while\s+)?{re.escape(term)}\s+is\s+constrained[^,.]*"
                        final_answer = re.sub(bl_pattern, "", final_answer, flags=re.IGNORECASE)

            # Clean up residual whitespace/newlines
            final_answer = re.sub(r"\n{3,}", "\n\n", final_answer).strip()

        # Build final evidenced claims list
        final_claims = [
            c for c in claims
            if CoverageValidator._is_expert_evidenced(c.expert_name, evidence)
        ]

        # Build final referenced expert names from evidence
        final_referenced_experts = list({ev.expert for ev in evidence})

        return final_answer, final_claims, final_referenced_experts, evidence

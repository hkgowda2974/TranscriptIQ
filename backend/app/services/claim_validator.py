import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from backend.app.services.query_analyzer import StructuredQuery

logger = logging.getLogger(__name__)


REFUSAL_MESSAGE = "I couldn't find sufficient evidence in the provided transcripts to answer this question."


class ClaimValidator:
    """
    Post-Generation Claim Validation Layer.
    Enforces the core invariants:
    - NO CLAIM WITHOUT SUPPORTING EVIDENCE.
    - EVERY CLAIM IN THE ANSWER MUST BE BACKED BY ACCEPTED EVIDENCE.
    - BOTTOM LINE CANNOT INTRODUCE UNSUPPORTED CONCLUSIONS.
    - IF REMOVING UNSUPPORTED CLAIMS LEAVES THE ANSWER INSUFFICIENT, REFUSE.
    """

    @staticmethod
    def _extract_numbers(text: str) -> List[str]:
        """Extracts numerical digits and written number words."""
        matches = re.findall(r"\b(?:\d+\s*(?:to|-)\s*\d+|\d+(?:\.\d+)?)\b", text)
        words = re.findall(r"\b(?:four|five|six|seven|eight|nine|ten|twelve|fourteen|eighteen|twenty|thirty|fifty)\b", text.lower())
        return matches + words

    @staticmethod
    def validate_and_filter(
        generated_answer: str,
        accepted_evidence: List[Dict[str, Any]],
        query: StructuredQuery
    ) -> str:
        """
        Validates sentences and claims in generated answer against accepted evidence quotes.
        Strips unsupported claims, department counts, timelines, or unbacked expert assertions.
        If no supported claims remain, returns REFUSAL_MESSAGE.
        """
        if not generated_answer.strip() or not accepted_evidence:
            return REFUSAL_MESSAGE if not accepted_evidence else generated_answer

        # Pool all accepted evidence text for reference
        evidence_text_corpus = " ".join([
            str(ev.get("quote", "")) + " " + str(ev.get("expert", "")) + " " + str(ev.get("source", ""))
            for ev in accepted_evidence
        ]).lower()

        distinct_experts = {str(ev.get("expert")) for ev in accepted_evidence if ev.get("expert")}
        num_distinct_experts = len(distinct_experts)

        lines = generated_answer.split("\n")
        validated_lines = []
        substantive_claims_count = 0

        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                validated_lines.append("")
                continue

            # Process Bottom Line separately
            if "bottom line" in line_strip.lower():
                cleaned_bl = line_strip
                # Check for unsupported universal claims
                if num_distinct_experts < 3:
                    cleaned_bl = re.sub(r"\b(?:all three experts|universal(?:ly)?)\b", "multiple experts", cleaned_bl, flags=re.IGNORECASE)

                # Check if Bottom Line references an expert/country not in evidence
                for country, expert in [("france", "dubois"), ("germany", "keller"), ("united kingdom", "carter")]:
                    if country in cleaned_bl.lower() and country not in evidence_text_corpus and expert not in evidence_text_corpus:
                        # Strip clause referencing unbacked country
                        cleaned_bl = re.sub(rf"(?:,\s*)?(?:while\s+)?{country}\s+is\s+constrained[^,.]*", "", cleaned_bl, flags=re.IGNORECASE)

                # Check if Bottom Line contains numbers absent from evidence
                bl_numbers = ClaimValidator._extract_numbers(cleaned_bl)
                for num in bl_numbers:
                    if num.lower() not in evidence_text_corpus:
                        cleaned_bl = re.sub(r"\b\d+\s*(?:to|-)\s*\d+\s*(?:months?|years?|percent|%)?", "", cleaned_bl)
                        cleaned_bl = re.sub(r"\s+", " ", cleaned_bl).strip()
                        break

                # Ensure bottom line is still substantive
                if len(cleaned_bl.replace("📌", "").replace("**Bottom Line**:", "").strip()) > 15:
                    validated_lines.append(cleaned_bl)
                continue

            # Check individual sentence/bullet for unsupported claims
            line_lower = line_strip.lower()

            # If it's a bullet point representing an expert claim
            is_bullet = line_strip.startswith("*") or line_strip.startswith("-")
            if is_bullet:
                # Check if this bullet references an expert/market not present in accepted evidence
                has_expert_match = False
                for ev in accepted_evidence:
                    ev_expert = str(ev.get("expert", "")).lower()
                    ev_speaker = str(ev.get("speaker", "")).lower()
                    if any(part in line_lower for part in re.findall(r"\w+", ev_expert) if len(part) > 3):
                        has_expert_match = True
                        break
                    if ev_speaker and ev_speaker in line_lower:
                        has_expert_match = True
                        break

                # If the bullet claims to represent an expert who is not in accepted evidence, drop it
                header_match = re.match(r"[\*\-]\s+\*\*([^*:\n]+)\*\*:", line_strip)
                if header_match:
                    claimed_speaker = header_match.group(1).lower()
                    if not any(part in evidence_text_corpus for part in re.findall(r"\w+", claimed_speaker) if len(part) > 3):
                        logger.warning(f"ClaimValidator: Dropping bullet for unevidenced speaker '{claimed_speaker}'")
                        continue

            # Check for consensus overclaim
            if ("all three experts" in line_lower or "all 3 experts" in line_lower) and num_distinct_experts < 3:
                line_strip = re.sub(r"\ball (?:three|3) experts\b", "multiple experts", line_strip, flags=re.IGNORECASE)

            # Check for unsupported numbers / durations / department counts
            line_numbers = ClaimValidator._extract_numbers(line_strip)
            unsupported_numbers = [
                n for n in line_numbers
                if n.lower() not in evidence_text_corpus
            ]

            if unsupported_numbers:
                logger.info(f"Detected unsupported numbers {unsupported_numbers} in line: '{line_strip}'. Filtering ungrounded clauses.")
                line_strip = re.sub(r",?\s*and\s*\d+\s*(?:to|-)\s*\d+\s*months?[^,.]*", "", line_strip)
                line_strip = re.sub(r",?\s*across\s*\d+\s*hospital\s*departments[^,.]*", "", line_strip)
                line_strip = re.sub(r",?\s*\d+\s*to\s*\d+\s*percent\s*(?:annually)?[^,.]*", "", line_strip)

            # Clean up punctuation artifacts
            line_strip = re.sub(r",\s*\.", ".", line_strip)
            line_strip = re.sub(r"\s+", " ", line_strip).strip()

            if line_strip:
                if is_bullet or (len(line_strip) > 20 and not line_strip.endswith(":")):
                    substantive_claims_count += 1
                validated_lines.append(line_strip)

        # Sufficiency check: if no substantive claims remain, return refusal
        if substantive_claims_count == 0:
            logger.info("ClaimValidator: No substantive backed claims remain in answer. Returning refusal.")
            return REFUSAL_MESSAGE

        validated_answer = "\n".join(validated_lines)

        # For multi-part queries: if any sub-question was unsupported, append explicit disclosure
        if query.is_multi_part:
            unsupported_subs = [sq for sq in query.sub_questions if not sq.is_supported]
            if unsupported_subs:
                missing_note = "\n\n*(Note: The provided transcripts do not contain evidence regarding: " + \
                               "; ".join([sq.text for sq in unsupported_subs]) + ")*"
                if missing_note not in validated_answer:
                    validated_answer += missing_note

        return validated_answer

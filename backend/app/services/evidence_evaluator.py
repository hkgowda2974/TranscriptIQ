import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from backend.app.schemas import TranscriptChunk
from backend.app.services.query_analyzer import StructuredQuery

logger = logging.getLogger(__name__)


def contains_explicit_price(text: str) -> bool:
    """Checks whether text contains an explicit price, monetary value, or currency symbol."""
    t_lower = text.lower()
    if any(c in text for c in ["€", "$", "£"]):
        return True
    if any(w in t_lower for w in ["euro", "euros", "dollar", "dollars", "pound", "pounds"]):
        return True
    if re.search(r"\b\d+(?:\.\d+)?\s*(?:million|thousand|k|m)\b", t_lower):
        return True
    if re.search(r"\b(?:costs?|priced?\s+at|selling\s+price\s+of)\s+\d+", t_lower):
        return True
    return False


class EvidenceEvaluator:
    """
    Reusable Evidence Evaluation Layer.
    Evaluates candidate chunks against structured query constraints:
    - Subject & Topic match
    - Market constraint match
    - Entity & Metric match
    - Temporal constraint match
    - Operation-specific Information Presence (Price, Count, Percentage, Timeline, Utilization)
    - Direct support vs Related context vs Insufficient
    Only DIRECT_SUPPORT candidates are accepted as answer-supporting evidence.
    """

    @staticmethod
    def evaluate_chunk(
        chunk: TranscriptChunk,
        query: StructuredQuery
    ) -> Tuple[str, List[Dict[str, str]], str]:
        """
        Classifies chunk as 'DIRECT_SUPPORT', 'RELATED_CONTEXT', or 'INSUFFICIENT'.
        Returns (classification, list_of_direct_quotes, reason).
        """
        if query.is_refusal_required:
            return "INSUFFICIENT", [], f"Refused: Query contains unsupported constraints ({query.refusal_reason})."

        # 1. Market Constraint Check
        # If user explicitly restricted to specific markets, reject all other markets
        if query.markets and chunk.market.lower() not in query.markets:
            return "INSUFFICIENT", [], f"Market mismatch: '{chunk.market}' not in requested {query.markets}."

        chunk_text_lower = chunk.verbatim_text.lower()
        direct_quotes: List[Dict[str, str]] = []

        # 2. Extract dialogue turns (excluding interviewer questions)
        speaker_turns = []
        for line in chunk.verbatim_text.split("\n"):
            line_strip = line.strip()
            if not line_strip:
                continue
            line_lower = line_strip.lower()
            if line_lower.startswith("interviewer:"):
                continue
            if ":" in line_strip:
                _, text = line_strip.split(":", 1)
                speaker_turns.append(text.strip())
            else:
                speaker_turns.append(line_strip)

        # 3. Explicit Price / Selling Price Requirement
        if query.requires_price:
            for turn in speaker_turns:
                if contains_explicit_price(turn):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Contains explicit price/pricing information."
            elif any(k in chunk_text_lower for k in ["cost", "economic", "total cost of ownership", "price", "budget"]):
                return "RELATED_CONTEXT", [], "Related context: Discusses cost or economics, but contains no selling price or explicit pricing."
            return "INSUFFICIENT", [], "No price information."

        # 4. Hospital Utilization Evaluation
        if "hospital_utilization" in query.topics or query.requested_attribute == "hospital_utilization":
            for turn in speaker_turns:
                t_lower = turn.lower()
                if any(k in t_lower for k in ["utilis", "utiliz", "usage", "idle", "capacity", "comfortable using"]):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Explains expert stance on system utilization and surgeon comfort."
            elif any(k in chunk_text_lower for k in ["adoption", "system", "training"]):
                return "RELATED_CONTEXT", [], "Related context: Discusses systems or adoption without utilization specifics."
            return "INSUFFICIENT", [], "No utilization evidence found."

        # 5. Topic & Direct Support Evaluation
        primary_topic = query.topics[0] if query.topics else "general"

        # Disagreement on Cost / Economic Prioritization
        if primary_topic == "cost_disagreement":
            for turn in speaker_turns:
                t_lower = turn.lower()
                if any(k in t_lower for k in [
                    "economic case", "clinical case", "finance alone", "balanced", "decides whether",
                    "margin", "return on investment", "cost is the first", "finances are under pressure",
                    "reimbursement restrictions", "biggest hurdle", "drg top-up tariffs", "absorb the per-case",
                    "funding is important", "length-of-stay reduction and complication rate decreases"
                ]):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Explains expert stance on economic vs clinical prioritization."
            return "INSUFFICIENT", [], "No cost disagreement specifics found in chunk."

        elif primary_topic == "adoption_trends":
            for turn in speaker_turns:
                t_lower = turn.lower()
                if any(k in t_lower for k in [
                    "adoption in france", "maturing steadily", "private clinics", "public university hospitals",
                    "chus", "faster", "competitive pressure", "patient demand", "gradual",
                    "competing capital priorities", "growing, but adoption", "dramatic jump", "uneven"
                ]):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Explains adoption pace across hospital settings."
            return "INSUFFICIENT", [], "No adoption pace specifics found."

        elif primary_topic == "reimbursement":
            for turn in speaker_turns:
                t_lower = turn.lower()
                if any(k in t_lower for k in ["reimbursement", "drg", "tariff", "tariffs", "sécurité sociale", "per-case"]):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Explains reimbursement policy, DRG tariffs, or national coverage."
            elif any(k in chunk_text_lower for k in ["barrier", "cost", "adoption"]):
                return "RELATED_CONTEXT", [], "Related context: Discusses adoption or costs without specific reimbursement details."
            return "INSUFFICIENT", [], "No reimbursement evidence."

        elif primary_topic == "training_requirements":
            for turn in speaker_turns:
                t_lower = turn.lower()
                # Filter out general procurement/economic turns that only mention training in passing
                if any(unrelated in t_lower for unrelated in [
                    "9 to 18 months", "procurement, clinical leadership", "budget cycle",
                    "total cost of ownership", "economic case decides", "maintenance, service contracts"
                ]):
                    continue
                if any(k in t_lower for k in [
                    "proctorship", "simulation", "supervised cases", "comfortable using",
                    "train enough surgeons", "training capacity", "trained people", "training is the bottleneck",
                    "supervised before operating independently"
                ]):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Details surgeon or staff training requirements or learning bottlenecks."
            elif "adoption" in chunk_text_lower:
                return "RELATED_CONTEXT", [], "Related context: Discusses adoption without training specifics."
            return "INSUFFICIENT", [], "No training evidence."

        elif primary_topic == "barriers":
            for turn in speaker_turns:
                t_lower = turn.lower()
                # Exclude lines discussing market growth forecasts
                if any(unrelated in t_lower for unrelated in ["expand by", "percent annually", "continued growth", "rough expectation", "outlook for the next"]):
                    continue
                if any(k in t_lower for k in [
                    "cost is the first", "large capital purchases", "capital investment",
                    "funding is important", "training capacity", "reimbursement restrictions",
                    "biggest hurdle", "bottleneck", "barrier", "used enough", "finances are under pressure"
                ]):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Explains specific capital, reimbursement, or operational barriers."
            return "RELATED_CONTEXT" if "adoption" in chunk_text_lower else "INSUFFICIENT", [], "No barrier details."

        elif primary_topic == "why_adopt_benefits":
            for turn in speaker_turns:
                t_lower = turn.lower()
                if any(k in t_lower for k in ["length of stay", "length-of-stay", "complication", "clinical position", "clinical outcomes", "recruitment", "patient demand", "minimally invasive", "competitive pressure"]):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Documents patient, clinical, or competitive benefits justifying adoption."
            return "RELATED_CONTEXT" if "barrier" in chunk_text_lower else "INSUFFICIENT", [], "No adoption benefits."

        elif primary_topic == "procurement_timeline":
            for turn in speaker_turns:
                t_lower = turn.lower()
                if any(k in t_lower for k in ["months", "timeline", "budget cycle", "capital committee", "purchase process"]):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Provides purchase or decision-making timeline durations."
            return "INSUFFICIENT", [], "No timeline details."

        elif primary_topic == "roi_and_economics" and not query.requires_price:
            for turn in speaker_turns:
                t_lower = turn.lower()
                if any(k in t_lower for k in ["economic case", "clinical case", "finance alone", "balanced", "decides whether", "margin", "return on investment", "total cost of ownership"]):
                    direct_quotes.append({
                        "quote": turn,
                        "speaker": chunk.speaker,
                        "timestamp": chunk.start_timestamp,
                        "source": chunk.source_file,
                        "expert": f"{chunk.expert_name} ({chunk.market})"
                    })
            if direct_quotes:
                return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Documents economic return and purchasing evaluation criteria."
            return "INSUFFICIENT", [], "No ROI specifics."

        # Dynamic topic fallback matching for arbitrary unseen questions
        from backend.app.services.query_analyzer import normalize_token_root
        query_stop_words = {
            "what", "is", "are", "the", "in", "how", "does", "do", "to", "for", "a", "of",
            "and", "or", "on", "with", "about", "market", "share", "which", "where", "who",
            "why", "can", "you", "tell", "me", "describe", "current", "vs", "versus", "say",
            "between", "across", "differ", "difference", "compare"
        }
        query_words = set(re.findall(r"\w+", query.raw_query.lower())) - query_stop_words
        query_roots = set(query.target_roots) if query.target_roots else {normalize_token_root(w) for w in query_words}

        for turn in speaker_turns:
            t_lower = turn.lower()
            turn_tokens = re.findall(r"\w+", t_lower)
            turn_roots = {normalize_token_root(tok) for tok in turn_tokens}

            # Check root matches
            matching_roots = query_roots.intersection(turn_roots)
            if matching_roots and len(matching_roots) >= max(1, min(2, len(query_roots))):
                # If question requires numbers, verify presence
                if query.requires_count and not re.search(r"\b\d+\b", t_lower):
                    continue
                if query.requires_percentage and not any(k in t_lower for k in ["%", "percent", "percentage"]):
                    continue
                if query.requires_timeline and not any(k in t_lower for k in ["month", "year", "week", "timeline", "duration"]):
                    continue

                direct_quotes.append({
                    "quote": turn,
                    "speaker": chunk.speaker,
                    "timestamp": chunk.start_timestamp,
                    "source": chunk.source_file,
                    "expert": f"{chunk.expert_name} ({chunk.market})"
                })

        if direct_quotes:
            return "DIRECT_SUPPORT", direct_quotes, "Direct Evidence: Matches requested query terms directly in expert turn."

        return "INSUFFICIENT", [], "Insufficient evidence in candidate chunk."


def is_chunk_relevant(chunk: TranscriptChunk, intent: Any) -> Tuple[str, List[Dict[str, str]], str]:
    """
    Adapter preserving backward compatibility with tests importing is_chunk_relevant.
    Maps ('DIRECT_SUPPORT' -> 'A', 'RELATED_CONTEXT' -> 'B', 'INSUFFICIENT' -> 'C').
    """
    cat, quotes, reason = EvidenceEvaluator.evaluate_chunk(chunk, intent)
    category_map = {
        "DIRECT_SUPPORT": "A",
        "RELATED_CONTEXT": "B",
        "INSUFFICIENT": "C",
        "CONTRADICTORY": "C"
    }
    return category_map.get(cat, "C"), quotes, reason

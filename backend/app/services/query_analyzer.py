import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

SUPPORTED_MARKETS = ["france", "germany", "united kingdom"]

# Known unsupported entities, metrics, geographies, and out-of-domain topics
UNSUPPORTED_ENTITIES = [
    "intuitive", "intuitive surgical", "da vinci", "medtronic", "hugo",
    "cmr", "versius", "stryker", "mako", "cyberknife", "johnson & johnson",
    "monarch", "globus"
]
UNSUPPORTED_METRICS = [
    "market share", "revenue", "sales volume", "stock price", "unit sales",
    "annual revenue", "share price", "profit margin", "installed base count",
    "exact percentage of market share"
]
UNSUPPORTED_GEOGRAPHIES = [
    "japan", "spain", "italy", "china", "usa", "united states", "india",
    "canada", "australia", "brazil", "netherlands", "sweden", "switzerland"
]
UNSUPPORTED_TOPICS = [
    "salary", "technician wage", "warranty", "stock option", "weather",
    "temperature", "bonus", "compensation package", "brand preference",
    "preferred brand", "exact budget"
]


@dataclass
class SubQuestion:
    text: str
    topic: str
    target_market: Optional[str] = None
    target_metric: Optional[str] = None
    target_entity: Optional[str] = None
    target_temporal: Optional[str] = None
    is_supported: bool = True


@dataclass
class StructuredQuery:
    raw_query: str
    subject: str
    topics: List[str]
    intent_type: str  # FACTUAL, COMPARISON, COMMON_THEMES, DISAGREEMENT, WHY_ADOPT, TIMELINE, GENERAL
    primary_intent: str  # Kept for backward compatibility
    entities: List[str]
    unsupported_entities: List[str]
    metrics: List[str]
    unsupported_metrics: List[str]
    markets: List[str]
    unsupported_geographies: List[str]
    time_period: Optional[str]
    unsupported_temporal: bool
    comparison_required: bool
    is_multi_part: bool
    sub_questions: List[SubQuestion]
    is_refusal_required: bool
    refusal_reason: Optional[str] = None
    target_concepts: List[str] = field(default_factory=list)
    negative_concepts: List[str] = field(default_factory=list)
    operation: str = "FACTUAL_GENERAL"
    requested_attribute: Optional[str] = None
    target_roots: List[str] = field(default_factory=list)
    requires_price: bool = False
    requires_count: bool = False
    requires_percentage: bool = False
    requires_timeline: bool = False
    requires_why: bool = False
    requires_importance: bool = False


# Backward-compatible alias
QueryIntent = StructuredQuery


def normalize_token_root(token: str) -> str:
    """Normalizes token to handle British/American variations and basic inflections."""
    t = token.lower().strip()
    # British/US s/z normalization
    t = re.sub(r"([a-z]+)iz([a-z]+)", r"\1is\2", t)
    # Suffixes
    for suffix in ["isations", "isation", "izations", "ization", "ments", "ment", "ting", "tingly", "ing", "ers", "er", "ies", "ed", "es", "s"]:
        if t.endswith(suffix) and len(t) - len(suffix) >= 3:
            t = t[:-len(suffix)]
            break
    return t


class QueryAnalyzer:
    """
    Generalized Query Analyzer.
    Extracts structured constraints, subjects, topics, entities, metrics, markets,
    temporal bounds, requested operations, target attributes, and linguistic roots.
    """

    @staticmethod
    def analyze(query: str) -> StructuredQuery:
        query_clean = query.strip()
        query_lower = query_clean.lower()

        # 1. Detect Unsupported Constraints
        detected_unsupported_entities = [e for e in UNSUPPORTED_ENTITIES if e in query_lower]
        detected_unsupported_metrics = [m for m in UNSUPPORTED_METRICS if m in query_lower]
        detected_unsupported_geos = [g for g in UNSUPPORTED_GEOGRAPHIES if g in query_lower]
        detected_bad_topics = [t for t in UNSUPPORTED_TOPICS if t in query_lower]

        # Check for unsupported temporal queries (any specific 4-digit calendar year like 2015, 2024, 2026)
        unsupported_temporal = False
        years_mentioned = re.findall(r"\b(19\d\d|20\d\d)\b", query_lower)
        if years_mentioned:
            unsupported_temporal = True

        # 2. Market Detection
        detected_markets = []
        if any(w in query_lower for w in ["france", "french", "paris"]):
            detected_markets.append("france")
        if any(w in query_lower for w in ["germany", "german", "berlin", "munich"]):
            detected_markets.append("germany")
        if any(w in query_lower for w in ["uk", "united kingdom", "britain", "british", "nhs", "london"]):
            detected_markets.append("united kingdom")

        # 3. Operation & Requirement Detection
        requires_price = any(k in query_lower for k in [
            "selling price", "average selling price", "purchase price", "unit price",
            "cost per system", "cost of a system", "price of a", "price of the",
            "system price", "what is the price", "what is the average price"
        ]) or (
            "price" in query_lower and any(w in query_lower for w in ["what", "how much", "average", "unit"])
        )
        requires_count = any(k in query_lower for k in ["how many", "count of", "number of", "total number"])
        requires_percentage = any(k in query_lower for k in ["what percentage", "what percent", "percentage of", "what proportion", "market share"])
        requires_timeline = any(k in query_lower for k in ["how long", "timeline", "duration", "how many months", "how many years", "decision timeline", "purchase process take"])
        requires_why = any(k in query_lower for k in ["why", "reasons", "justify", "benefits", "advantages"])
        requires_importance = any(k in query_lower for k in ["how important", "importance of", "significance of"])

        is_comparison = any(k in query_lower for k in ["differ", "difference", "compare", "comparison", "across", "versus", "vs", "contrast", "where do the experts differ"])
        is_common = any(k in query_lower for k in ["more than one", "common", "shared", "all three", "multiple experts", "both", "consensus"])
        is_disagreement = any(k in query_lower for k in ["disagree", "disagreement", "conflict", "different emphasis", "philosophies"])
        is_cost_query = any(k in query_lower for k in ["cost", "economic", "finance", "financial", "budget", "roi", "price", "funding"])

        # Determine generalized operation
        if requires_price:
            operation = "PRICE_VALUE"
        elif requires_count:
            operation = "NUMERIC_COUNT"
        elif requires_percentage:
            operation = "WHAT_PERCENTAGE"
        elif requires_timeline:
            operation = "WHEN_TIMELINE"
        elif is_disagreement:
            operation = "DISAGREEMENT"
        elif is_comparison:
            operation = "COMPARE"
        elif is_common:
            operation = "COMMON_THEMES"
        elif requires_why:
            operation = "WHY_REASONS"
        elif requires_importance:
            operation = "HOW_IMPORTANT"
        elif any(k in query_lower for k in ["say about", "say regarding", "describe", "view on", "opinion on", "what do the experts say", "what does the"]):
            operation = "EXPERT_OPINION"
        else:
            operation = "FACTUAL_GENERAL"

        # If a question asks across experts/markets in general without naming a specific market, default to all supported markets
        if (is_comparison or is_common or is_disagreement or "experts" in query_lower) and not detected_markets:
            detected_markets = list(SUPPORTED_MARKETS)

        # 4. Extract Topics & Attribute Dynamically
        topics = []
        target_concepts = []
        negative_concepts = []
        requested_attribute = None

        if requires_price:
            requested_attribute = "selling_price"
            topics.append("selling_price")
            target_concepts.extend(["price", "selling price", "euro", "€", "$", "£", "cost of the system"])

        if any(k in query_lower for k in ["utilis", "utiliz", "usage", "capacity", "idle", "comfortable using"]):
            topics.append("hospital_utilization")
            requested_attribute = "hospital_utilization"
            target_concepts.extend(["utilisation", "utilization", "comfortable using", "poor", "business case", "buys a system"])

        if is_disagreement and is_cost_query and not requires_price:
            topics.append("cost_disagreement")
            topics.append("roi_and_economics")
            requested_attribute = "cost_disagreement"
            target_concepts.extend([
                "economic case", "clinical case", "finance alone", "balanced", "decides whether",
                "margin", "return on investment", "length of stay", "complication rate",
                "cost is the first", "finances are under pressure", "reimbursement restrictions",
                "biggest hurdle", "drg top-up tariffs", "absorb", "funding is important"
            ])
            negative_concepts.extend(["9 to 18 months", "proctorship"])

        if any(k in query_lower for k in ["reimbursement", "drg", "tariff", "tariffs", "sécurité sociale", "public coverage"]):
            topics.append("reimbursement")
            if not requested_attribute:
                requested_attribute = "reimbursement"
            target_concepts.extend(["reimbursement", "drg", "tariff", "tariffs", "sécurité sociale", "absorb", "per-case"])
            negative_concepts.extend(["timeline", "months", "expand by 12 to 18 percent"])

        if any(k in query_lower for k in ["training", "trained", "curriculum", "proctorship", "simulation", "supervised", "theatre staff"]):
            topics.append("training_requirements")
            if not requested_attribute:
                requested_attribute = "training_requirements"
            target_concepts.extend(["training", "trained", "proctorship", "simulation", "supervised", "curriculum", "theatre staff", "utilisation", "comfortable"])
            negative_concepts.extend(["9 to 18 months", "procurement timeline", "expand by 12 to 18 percent", "annual growth", "total cost of ownership", "economic case decides"])

        if any(k in query_lower for k in ["barrier", "barriers", "hurdle", "hurdles", "holding back", "obstacle"]):
            topics.append("barriers")
            if not requested_attribute:
                requested_attribute = "barriers"
            target_concepts.extend(["barrier", "capital", "cost", "funding", "reimbursement", "training", "utilisation", "finances under pressure", "hurdle"])
            negative_concepts.extend(["expand by 12 to 18 percent", "annual growth"])

        if any(k in query_lower for k in ["why", "despite", "advantage", "benefit", "benefits", "reasons", "justify", "clinical justification", "length of stay", "complication"]):
            topics.append("why_adopt_benefits")
            if not requested_attribute:
                requested_attribute = "why_adopt_benefits"
            target_concepts.extend(["length of stay", "complication", "clinical position", "clinical outcomes", "recruitment", "patient demand", "minimally invasive", "competitive pressure"])
            negative_concepts.extend(["9 to 18 months", "drg top-up tariffs"])

        if any(k in query_lower for k in ["timeline", "how long", "duration", "purchase process", "decision timeline", "decision-making", "take in"]):
            topics.append("procurement_timeline")
            if not requested_attribute:
                requested_attribute = "procurement_timeline"
            target_concepts.extend(["six to nine months", "9 to 18 months", "nine to eighteen months", "budget cycle", "capital committee"])
            negative_concepts.extend(["reimbursement", "simulation"])

        if any(k in query_lower for k in ["adoption pace", "adoption trend", "private clinics", "public university hospitals", "adoption in"]):
            topics.append("adoption_trends")
            if not requested_attribute:
                requested_attribute = "adoption_trends"
            target_concepts.extend(["adoption in france", "maturing steadily", "private clinics", "public university hospitals", "chus", "faster", "competitive pressure", "patient demand"])

        if is_cost_query and not requires_price and "roi_and_economics" not in topics and "cost_disagreement" not in topics:
            topics.append("roi_and_economics")
            if not requested_attribute:
                requested_attribute = "roi_and_economics"
            target_concepts.extend(["return on investment", "margin", "horizon", "economic case", "total cost of ownership", "length of stay", "finance alone", "balanced"])

        if any(k in query_lower for k in ["procedure volume", "cases", "supervised cases", "volume"]):
            topics.append("procedure_volume")
            if not requested_attribute:
                requested_attribute = "procedure_volume"
            target_concepts.extend(["procedure volume", "supervised cases", "cases", "sustainable", "30 to 50"])

        # Linguistic root extraction for query concepts
        stop_words = {
            "what", "is", "are", "the", "in", "how", "does", "do", "to", "for", "a", "of",
            "and", "or", "on", "with", "about", "market", "which", "where", "who", "why",
            "can", "you", "tell", "me", "describe", "current", "vs", "versus", "say",
            "between", "across", "differ", "difference", "compare", "expert", "experts",
            "robotic", "surgery", "surgical", "system", "systems", "hospital", "hospitals",
            "give", "exact", "quotes", "names", "timestamps", "according"
        }
        query_tokens = [w for w in re.findall(r"\w+", query_lower) if w not in stop_words and len(w) > 2]
        target_roots = [normalize_token_root(w) for w in query_tokens]

        # 5. Multi-Part Question Decomposition
        sub_questions = []
        is_multi_part = False
        parts = re.split(r"\band\b|\?+", query_clean)
        clean_parts = [p.strip() for p in parts if len(p.strip()) > 10]
        if len(clean_parts) > 1 and any(q_word in query_lower for q_word in ["what", "how", "why", "which", "where"]):
            is_multi_part = True
            for part in clean_parts:
                part_lower = part.lower()
                sub_unsupported = any(e in part_lower for e in UNSUPPORTED_ENTITIES) or \
                                  any(m in part_lower for m in UNSUPPORTED_METRICS) or \
                                  any(g in part_lower for g in UNSUPPORTED_GEOGRAPHIES) or \
                                  any(t in part_lower for t in UNSUPPORTED_TOPICS) or \
                                  any(re.findall(r"\b(19\d\d|20\d\d)\b", part_lower))
                sub_questions.append(SubQuestion(
                    text=part,
                    topic="general",
                    is_supported=not sub_unsupported
                ))

        # 6. Refusal Pre-check
        is_refusal_required = False
        refusal_reasons = []

        if detected_unsupported_entities:
            is_refusal_required = True
            refusal_reasons.append(f"unsupported entities: {detected_unsupported_entities}")
        if detected_unsupported_metrics:
            is_refusal_required = True
            refusal_reasons.append(f"unsupported metrics: {detected_unsupported_metrics}")
        if detected_unsupported_geos:
            is_refusal_required = True
            refusal_reasons.append(f"unsupported geographies: {detected_unsupported_geos}")
        if detected_bad_topics and not is_multi_part:
            is_refusal_required = True
            refusal_reasons.append(f"unsupported topics: {detected_bad_topics}")
        if unsupported_temporal and not any(k in query_lower for k in ["3 to 5", "3-5", "next"]) and not is_multi_part:
            is_refusal_required = True
            refusal_reasons.append(f"unsupported historical or specific year: {years_mentioned}")

        # Check for vague/ambiguous queries unrelated to robotic surgery or transcripts
        core_medical_terms = [
            "robotic", "surgery", "robot", "hospital", "surgeon", "adoption", "barrier",
            "cost", "training", "reimbursement", "roi", "drg", "capital", "procurement",
            "clinics", "procedure", "stay", "complication", "timeline", "expert", "differ",
            "disagree", "contrast", "utilization", "utilisation", "price"
        ]
        if not any(term in query_lower for term in core_medical_terms) and not detected_markets:
            is_refusal_required = True
            refusal_reasons.append("query unrelated to expert transcript topics")

        # Multi-part resolution: if at least one sub-question is supported, allow answering with partial caveat
        if is_multi_part:
            supported_subs = [sq for sq in sub_questions if sq.is_supported]
            if supported_subs:
                is_refusal_required = False

        # 7. Intent Type Classification
        if is_refusal_required:
            intent_type = "REFUSAL_EXPECTED"
            primary_intent = "unsupported_query"
        elif is_disagreement:
            intent_type = "DISAGREEMENT"
            primary_intent = "cost_disagreement" if is_cost_query else "disagreement_analysis"
        elif is_common:
            intent_type = "COMMON_THEMES"
            primary_intent = "common_barriers" if "barrier" in query_lower else "common_themes"
        elif is_comparison:
            intent_type = "COMPARISON"
            primary_intent = "cross_market_barriers" if "barrier" in query_lower else "comparison"
        elif "selling_price" in topics:
            intent_type = "FACTUAL"
            primary_intent = "selling_price"
        elif "hospital_utilization" in topics:
            intent_type = "FACTUAL"
            primary_intent = "hospital_utilization"
        elif "reimbursement" in topics:
            intent_type = "FACTUAL"
            primary_intent = "reimbursement"
        elif "training_requirements" in topics:
            intent_type = "FACTUAL"
            primary_intent = "training_requirements"
        elif "why_adopt_benefits" in topics:
            intent_type = "EXPLANATION"
            primary_intent = "why_adopt_benefits"
        elif "procurement_timeline" in topics:
            intent_type = "FACTUAL"
            primary_intent = "procurement_timeline"
        elif "barriers" in topics:
            intent_type = "FACTUAL"
            primary_intent = "adoption_barriers"
        else:
            intent_type = "GENERAL"
            primary_intent = "general_query"

        # Subject extraction
        subject = "robotic surgery adoption"
        if "selling_price" in topics:
            subject = "robotic surgery system selling price"
        elif "hospital_utilization" in topics:
            subject = "hospital system utilization"
        elif "cost_disagreement" in topics:
            subject = "disagreement on cost and financial prioritization"
        elif "reimbursement" in topics:
            subject = "robotic surgery reimbursement"
        elif "training_requirements" in topics:
            subject = "surgeon and staff training"
        elif "procurement_timeline" in topics:
            subject = "hospital decision timelines"

        return StructuredQuery(
            raw_query=query,
            subject=subject,
            topics=topics,
            intent_type=intent_type,
            primary_intent=primary_intent,
            entities=[e for e in ["sécurité sociale", "drg", "nhs", "chu"] if e in query_lower],
            unsupported_entities=detected_unsupported_entities,
            metrics=[m for m in ["timeline", "cases", "percentage", "cost"] if m in query_lower],
            unsupported_metrics=detected_unsupported_metrics,
            markets=detected_markets,
            unsupported_geographies=detected_unsupported_geos,
            time_period="3-5 years" if any(k in query_lower for k in ["3 to 5", "3-5", "next"]) else None,
            unsupported_temporal=unsupported_temporal,
            comparison_required=is_comparison,
            is_multi_part=is_multi_part,
            sub_questions=sub_questions,
            is_refusal_required=is_refusal_required,
            refusal_reason="; ".join(refusal_reasons) if refusal_reasons else None,
            target_concepts=list(set(target_concepts)),
            negative_concepts=list(set(negative_concepts)),
            operation=operation,
            requested_attribute=requested_attribute,
            target_roots=list(set(target_roots)),
            requires_price=requires_price,
            requires_count=requires_count,
            requires_percentage=requires_percentage,
            requires_timeline=requires_timeline,
            requires_why=requires_why,
            requires_importance=requires_importance
        )


def detect_query_intent(query: str) -> StructuredQuery:
    """Entrypoint function preserving backward compatibility."""
    return QueryAnalyzer.analyze(query)

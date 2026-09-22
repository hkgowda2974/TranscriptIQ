import pytest
from backend.app.schemas import TranscriptChunk
from backend.app.services.validator import validate_and_bind_evidence, validate_evidence_list

DUMMY_CHUNK = TranscriptChunk(
    chunk_id="exp3_turn_01",
    source_file="expert_3.txt",
    expert_id="expert_3",
    expert_name="Dr. Emily Carter",
    expert_role="Consultant Urologist",
    market="United Kingdom",
    question_context="What are the main barriers?",
    speaker="Dr. Carter",
    start_timestamp="01:05",
    end_timestamp="02:02",
    verbatim_text="Dr. Carter: Funding is important, but I would say training capacity is just as important. You can buy a system, but if you cannot train enough surgeons and theatre staff, adoption stalls.",
    raw_lines=["01:05", "Funding is important..."]
)


def test_validate_quote_exact_match():
    quote = "Funding is important, but I would say training capacity is just as important."
    ev = validate_and_bind_evidence(quote, "Dr. Carter", "01:05", [DUMMY_CHUNK])

    assert ev.verification_status == "VERIFIED_EXACT_MATCH"
    assert ev.timestamp == "01:05"
    assert ev.source == "expert_3.txt"


def test_validate_quote_hallucination_detection():
    hallucinated_quote = "Robotic surgery is completely banned in public hospitals in the UK."
    ev = validate_and_bind_evidence(hallucinated_quote, "Dr. Carter", "01:05", [DUMMY_CHUNK])

    assert ev.verification_status == "UNVERIFIED_HALLUCINATION"
    assert ev.source == "unverified"


def test_filter_and_validate_evidence():
    raw_evidence = [
        {
            "quote": "Funding is important, but I would say training capacity is just as important.",
            "expert": "Dr. Carter",
            "timestamp": "01:05"
        },
        {
            "quote": "Robots perform 100% of all operations autonomously.",
            "expert": "Dr. Carter",
            "timestamp": "01:05"
        }
    ]

    validated_list, is_grounded = validate_evidence_list(raw_evidence, [DUMMY_CHUNK])
    assert len(validated_list) == 1
    assert is_grounded is False  # Contains hallucinated quote
    assert validated_list[0].verification_status == "VERIFIED_EXACT_MATCH"

import pytest
from backend.app.services.parser import parse_interview_guide, parse_transcript
from backend.app.services.chunker import create_turn_chunks

SAMPLE_GUIDE = """Interview Guide – European Robotic Surgery Market

Project objective:
Understand hospital adoption, barriers, economics, and purchasing behaviour.

Questions:
1. How would you describe current adoption?
2. What are the main barriers?
"""

SAMPLE_TRANSCRIPT = """Expert 3 – Dr. Emily Carter
Role: Consultant Urologist
Market: United Kingdom

00:00
Interviewer: How would you describe adoption in the UK?

00:14
Dr. Carter: Adoption is increasing, and in some larger NHS trusts robotic surgery is becoming standard.

01:00
Interviewer: What are the main barriers?

01:05
Dr. Carter: Funding is important, but training capacity is just as important.
"""


def test_parse_interview_guide():
    obj, questions = parse_interview_guide(SAMPLE_GUIDE)
    assert "Understand hospital adoption" in obj
    assert len(questions) == 2
    assert questions[0].question_id == 1
    assert questions[0].question_text == "How would you describe current adoption?"


def test_parse_transcript():
    parsed = parse_transcript(SAMPLE_TRANSCRIPT, "expert_3.txt")
    meta = parsed["metadata"]
    turns = parsed["turns"]

    assert meta.expert_id == "expert_3"
    assert meta.name == "Dr. Emily Carter"
    assert meta.market == "United Kingdom"
    assert len(turns) == 4
    assert turns[0].speaker == "Interviewer"
    assert turns[1].speaker == "Dr. Carter"
    assert turns[1].timestamp == "00:14"


def test_create_turn_chunks():
    parsed = parse_transcript(SAMPLE_TRANSCRIPT, "expert_3.txt")
    chunks = create_turn_chunks(parsed)

    assert len(chunks) == 2
    assert chunks[0].start_timestamp == "00:14"
    assert "Adoption is increasing" in chunks[0].verbatim_text
    assert chunks[1].start_timestamp == "01:05"
    assert "Funding is important" in chunks[1].verbatim_text

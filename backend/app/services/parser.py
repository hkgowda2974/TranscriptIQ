import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from backend.app.schemas import ExpertMetadata, InterviewQuestion, TranscriptTurn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_timestamp(timestamp_str: str) -> str:
    """
    Normalizes raw timestamp strings to a canonical MM:SS format.
    Example: '0:14' -> '00:14', '1:05' -> '01:05', '00:00' -> '00:00'
    """
    ts = timestamp_str.strip()
    match = re.match(r"^(\d{1,2}):(\d{2})$", ts)
    if match:
        mins, secs = match.groups()
        return f"{int(mins):02d}:{secs}"
    return ts


def parse_interview_guide(guide_content_or_path: Any) -> Tuple[str, List[InterviewQuestion]]:
    """
    Parses an interview guide string or file path to extract the project objective
    and a structured list of canonical questions.
    """
    if isinstance(guide_content_or_path, Path):
        text_content = guide_content_or_path.read_text(encoding="utf-8")
    elif isinstance(guide_content_or_path, str):
        text_content = guide_content_or_path
        if "\n" not in guide_content_or_path and len(guide_content_or_path) < 4096:
            try:
                guide_path = Path(guide_content_or_path)
                if guide_path.exists() and guide_path.is_file():
                    text_content = guide_path.read_text(encoding="utf-8")
            except (OSError, ValueError):
                pass
    else:
        text_content = str(guide_content_or_path)

    objective = ""
    questions: List[InterviewQuestion] = []

    # Extract project objective
    obj_match = re.search(
        r"Project objective:\s*\n*(.*?)(?=\n\s*\n|\nQuestions:|$)",
        text_content,
        re.DOTALL | re.IGNORECASE
    )
    if obj_match:
        objective = obj_match.group(1).strip()

    # Extract numbered questions (e.g., "1. How would you describe...")
    q_matches = re.findall(r"^(\d+)\.\s*(.+)$", text_content, re.MULTILINE)
    for q_id, q_text in q_matches:
        questions.append(
            InterviewQuestion(
                question_id=int(q_id),
                question_text=q_text.strip()
            )
        )

    logger.info(f"Successfully parsed interview guide: {len(questions)} questions found.")
    return objective, questions


def parse_transcript(transcript_content_or_path: Any, filename_hint: str = "") -> Dict[str, Any]:
    """
    Parses a raw transcript string or file path into expert metadata and an ordered sequence
    of timestamped speaker turns.
    """
    source_filename = filename_hint
    if isinstance(transcript_content_or_path, Path):
        text_content = transcript_content_or_path.read_text(encoding="utf-8")
        if not source_filename:
            source_filename = transcript_content_or_path.name
    elif isinstance(transcript_content_or_path, str):
        text_content = transcript_content_or_path
        if "\n" not in transcript_content_or_path and len(transcript_content_or_path) < 4096:
            try:
                file_path = Path(transcript_content_or_path)
                if file_path.exists() and file_path.is_file():
                    text_content = file_path.read_text(encoding="utf-8")
                    if not source_filename:
                        source_filename = file_path.name
            except (OSError, ValueError):
                pass
    else:
        text_content = str(transcript_content_or_path)

    if not source_filename:
        source_filename = "transcript.txt"

    lines = [line.rstrip() for line in text_content.strip().split("\n")]

    # Infer default expert_id from filename (e.g. expert_1.txt -> expert_1)
    filename_clean = Path(source_filename).stem.lower().replace(" ", "_")
    expert_id = filename_clean if filename_clean.startswith("expert_") else "expert_unknown"
    name = "Subject Expert"
    role = "Subject Expert"
    market = "Europe"

    body_start_index = 0

    # Parse Header Metadata
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue
        
        # Check for "Expert X – Name" or "Expert X - Name"
        if re.match(r"^Expert\s+\d+", line_clean, re.IGNORECASE):
            m_exp = re.search(r"Expert\s+(\d+)", line_clean, re.IGNORECASE)
            if m_exp:
                expert_id = f"expert_{m_exp.group(1)}"

            name_parts = re.split(r"–|-", line_clean, maxsplit=1)
            if len(name_parts) > 1:
                name = name_parts[1].strip()
        elif line_clean.lower().startswith("role:"):
            role = line_clean.split(":", 1)[1].strip()
        elif line_clean.lower().startswith("market:"):
            market = line_clean.split(":", 1)[1].strip()
        elif re.match(r"^\d{1,2}:\d{2}", line_clean):
            body_start_index = i
            break

    metadata = ExpertMetadata(
        expert_id=expert_id,
        name=name,
        role=role,
        market=market,
        source_file=source_filename
    )

    # Parse Body Speaker Turns
    turns: List[TranscriptTurn] = []
    current_timestamp = "00:00"

    i = body_start_index
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Check for timestamp anchor e.g., "01:05" or "1:05"
        if re.match(r"^\d{1,2}:\d{2}$", line):
            current_timestamp = normalize_timestamp(line)
            i += 1
            continue

        # Check for speaker label e.g., "Interviewer:", "Dr. Carter:", "Anna Keller:"
        speaker_match = re.match(r"^([A-Za-z0-9\.\s–-]+):\s*(.*)", line)
        if speaker_match:
            speaker_name = speaker_match.group(1).strip()
            content_first_line = speaker_match.group(2).strip()

            content_lines = [content_first_line] if content_first_line else []
            i += 1
            
            # Consume multi-line speaker statement until next timestamp or next speaker turn
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    continue
                if re.match(r"^\d{1,2}:\d{2}$", next_line) or re.match(r"^([A-Za-z0-9\.\s–-]+):", next_line):
                    break
                content_lines.append(next_line)
                i += 1

            full_content = " ".join(content_lines).strip()
            turns.append(
                TranscriptTurn(
                    timestamp=current_timestamp,
                    speaker=speaker_name,
                    content=full_content
                )
            )
        else:
            i += 1

    logger.info(f"Parsed {metadata.expert_id} ({metadata.name}, {metadata.market}): {len(turns)} turns found.")
    return {
        "metadata": metadata,
        "turns": turns
    }

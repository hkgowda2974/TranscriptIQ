import logging
from typing import List, Dict, Any
from backend.app.schemas import TranscriptChunk, ExpertMetadata, TranscriptTurn

logger = logging.getLogger(__name__)


def create_turn_chunks(parsed_transcript: Dict[str, Any]) -> List[TranscriptChunk]:
    """
    Transforms parsed transcript metadata and turns into atomic Q&A dialogue chunks.
    Preserves speaker identity, timestamps, surrounding question context, and verbatim text.
    """
    metadata: ExpertMetadata = parsed_transcript["metadata"]
    turns: List[TranscriptTurn] = parsed_transcript["turns"]

    chunks: List[TranscriptChunk] = []
    i = 0
    chunk_index = 1

    while i < len(turns):
        turn = turns[i]

        # Detect Interviewer question turn
        if "interviewer" in turn.speaker.lower():
            question_text = turn.content
            q_timestamp = turn.timestamp

            i += 1
            expert_content_parts = []
            expert_speaker = metadata.name
            start_timestamp = q_timestamp

            # Capture following expert answer turn(s)
            if i < len(turns) and "interviewer" not in turns[i].speaker.lower():
                expert_turn = turns[i]
                expert_speaker = expert_turn.speaker
                start_timestamp = expert_turn.timestamp
                expert_content_parts.append(f"{expert_speaker}: {expert_turn.content}")
                i += 1

                # Capture any contiguous continuation turns by the same expert
                while i < len(turns) and "interviewer" not in turns[i].speaker.lower():
                    expert_content_parts.append(f"{turns[i].speaker}: {turns[i].content}")
                    i += 1

            # Determine end timestamp boundary from next turn or current turn
            if i < len(turns):
                end_timestamp = turns[i].timestamp
            else:
                end_timestamp = start_timestamp

            verbatim_text = "\n".join(expert_content_parts) if expert_content_parts else f"Interviewer: {question_text}"

            chunk = TranscriptChunk(
                chunk_id=f"{metadata.expert_id}_turn_{chunk_index:02d}",
                source_file=metadata.source_file,
                expert_id=metadata.expert_id,
                expert_name=metadata.name,
                expert_role=metadata.role,
                market=metadata.market,
                question_context=question_text,
                speaker=expert_speaker,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                verbatim_text=verbatim_text,
                raw_lines=[f"[{start_timestamp} - {end_timestamp}]", verbatim_text]
            )
            chunks.append(chunk)
            chunk_index += 1
        else:
            # Standalone expert statement without explicit interviewer question prefix
            start_timestamp = turn.timestamp
            end_timestamp = turns[i + 1].timestamp if (i + 1 < len(turns)) else start_timestamp
            
            chunk = TranscriptChunk(
                chunk_id=f"{metadata.expert_id}_turn_{chunk_index:02d}",
                source_file=metadata.source_file,
                expert_id=metadata.expert_id,
                expert_name=metadata.name,
                expert_role=metadata.role,
                market=metadata.market,
                question_context="General expert statement",
                speaker=turn.speaker,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                verbatim_text=f"{turn.speaker}: {turn.content}",
                raw_lines=[f"[{start_timestamp} - {end_timestamp}]", f"{turn.speaker}: {turn.content}"]
            )
            chunks.append(chunk)
            chunk_index += 1
            i += 1

    logger.info(f"Created {len(chunks)} chunks for expert {metadata.expert_id}.")
    return chunks

from typing import List, Optional
from pydantic import BaseModel, Field


class TranscriptTurn(BaseModel):
    timestamp: str = Field(..., description="Timestamp of turn, e.g., '01:05'")
    speaker: str = Field(..., description="Speaker name, e.g., 'Dr. Carter' or 'Interviewer'")
    content: str = Field(..., description="Spoken text content")


class ExpertMetadata(BaseModel):
    expert_id: str = Field(..., description="Unique ID for expert, e.g., 'expert_1'")
    name: str = Field(..., description="Expert name, e.g., 'Dr. Emily Carter'")
    role: str = Field(..., description="Role/title of expert")
    market: str = Field(..., description="Country or market region")
    source_file: str = Field(..., description="Filename of source transcript")


class TranscriptChunk(BaseModel):
    chunk_id: str
    source_file: str
    expert_id: str
    expert_name: str
    expert_role: str
    market: str
    question_context: str
    speaker: str
    start_timestamp: str
    end_timestamp: str
    verbatim_text: str
    raw_lines: List[str]


class InterviewQuestion(BaseModel):
    question_id: int
    question_text: str


class RAGEvidenceItem(BaseModel):
    expert: str = Field(..., description="Expert name or identifier, e.g., 'Dr. Jean-Luc Dubois (France)'")
    timestamp: str = Field(..., description="Validated start timestamp from source metadata")
    quote: str = Field(..., description="Verbatim quote extracted from transcript")
    source: str = Field(..., description="Source transcript filename, e.g., 'expert_1.txt'")
    verification_status: str = Field("VERIFIED_EXACT_MATCH", description="VERIFIED_EXACT_MATCH, VERIFIED_FUZZY_MATCH, or UNVERIFIED_HALLUCINATION")


class AnswerClaimItem(BaseModel):
    expert_name: str = Field(..., description="Name of the expert the claim is about, e.g., 'Dr. Jean-Luc Dubois' or 'France'")
    market: Optional[str] = Field(None, description="Country or market of the expert, e.g., 'France'")
    claim_text: str = Field(..., description="Summary of the specific factual claim made regarding this expert")
    supporting_quote: Optional[str] = Field(None, description="Verbatim quote backing this claim if available")


class RAGAnswerResponse(BaseModel):
    answer: str = Field(..., description="Generated summary answer text")
    confidence: str = Field("HIGH", description="Confidence level: HIGH, MEDIUM, or LOW")
    claims: List[AnswerClaimItem] = Field(default_factory=list, description="Structured claims made per expert in the answer")
    referenced_experts: List[str] = Field(default_factory=list, description="List of experts referenced in the answer text")
    evidence: List[RAGEvidenceItem] = Field(default_factory=list, description="List of validated evidence items")
    is_grounded: bool = Field(True, description="Flag indicating if all evidence quotes were verified against source chunks")


class ExpertGuidedAnswer(BaseModel):
    expert_id: str
    expert_name: str
    market: str
    summary_answer: str
    key_findings: List[str]
    evidence: List[RAGEvidenceItem]


class GuidedQuestionAnalysis(BaseModel):
    question_id: int
    question_text: str
    expert_answers: List[ExpertGuidedAnswer]


class ThemeExpertEvidence(BaseModel):
    expert_name: str
    market: str
    position_summary: str
    evidence_quotes: List[RAGEvidenceItem]


class ThemeSynthesis(BaseModel):
    theme_title: str
    description: str
    supporting_experts: List[str]
    per_expert_evidence: List[ThemeExpertEvidence]


class ExpertSynthesisItem(BaseModel):
    expert_id: str
    expert_name: str
    market: str
    position_summary: str
    verbatim_quote: str
    timestamp: str
    source: str = "transcript.txt"


class DisagreementSynthesis(BaseModel):
    topic: str
    relationship_type: str = Field("DIRECT_DISAGREEMENT", description="DIRECT_DISAGREEMENT, DIFFERENT_EMPHASIS, or PARTIAL_AGREEMENT")
    description: str
    expert_positions: List[ExpertSynthesisItem]


class SynthesisResult(BaseModel):
    common_themes: List[ThemeSynthesis]
    disagreements: List[DisagreementSynthesis]


class QuestionAnswerResult(BaseModel):
    question_id: int
    question_text: str
    expert_id: str
    expert_name: str
    market: str
    summary_answer: str
    key_findings: List[str] = Field(default_factory=list)
    evidence: List[RAGEvidenceItem]
    is_grounded: bool = True


class CustomQARequest(BaseModel):
    query: str
    target_expert_ids: Optional[List[str]] = None


class CustomQAResponse(BaseModel):
    query: str
    answer_summary: str
    evidence: List[RAGEvidenceItem]
    is_grounded: bool

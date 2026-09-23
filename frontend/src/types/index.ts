export interface ExpertMetadata {
  expert_id: string;
  name: string;
  role: string;
  market: string;
  source_file: string;
}

export interface InterviewQuestion {
  question_id: number;
  question_text: string;
}

export interface RAGEvidenceItem {
  expert: string;
  timestamp: string;
  quote: string;
  source: string;
  verification_status: string;
}

export interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  evidence?: RAGEvidenceItem[];
  confidence?: string;
  isGrounded?: boolean;
  isStreaming?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  timestamp: string | Date | number;
  messages: ChatMessageItem[];
}

export interface ExpertGuidedAnswer {
  expert_id: string;
  expert_name: string;
  market: string;
  summary_answer: string;
  key_findings: string[];
  evidence: RAGEvidenceItem[];
}

export interface GuidedQuestionAnalysis {
  question_id: number;
  question_text: string;
  expert_answers: ExpertGuidedAnswer[];
}

export interface ThemeExpertEvidence {
  expert_name: string;
  market: string;
  position_summary: string;
  evidence_quotes: RAGEvidenceItem[];
}

export interface ThemeSynthesis {
  theme_title: string;
  description: string;
  supporting_experts: string[];
  per_expert_evidence: ThemeExpertEvidence[];
}

export interface ExpertSynthesisItem {
  expert_id: string;
  expert_name: string;
  market: string;
  position_summary: string;
  verbatim_quote: string;
  timestamp: string;
  source: string;
}

export interface DisagreementSynthesis {
  topic: string;
  relationship_type: string;
  description: string;
  expert_positions: ExpertSynthesisItem[];
}

export interface SynthesisResult {
  common_themes: ThemeSynthesis[];
  disagreements: DisagreementSynthesis[];
}

export type ActiveView = 'chat' | 'library' | 'hub' | 'guide' | 'synthesis' | 'explorer';

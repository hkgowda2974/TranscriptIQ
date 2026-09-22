import { SynthesisResult, RAGEvidenceItem } from '../types';

const API_BASE = '/api';

export async function fetchTranscripts() {
  const res = await fetch(`${API_BASE}/transcripts`);
  if (!res.ok) throw new Error('Failed to fetch transcripts data');
  return res.json();
}

export async function fetchMatrix() {
  const res = await fetch(`${API_BASE}/matrix`);
  if (!res.ok) throw new Error('Failed to fetch matrix answers');
  return res.json();
}

export async function fetchSynthesis(): Promise<SynthesisResult> {
  const res = await fetch(`${API_BASE}/synthesis`);
  if (!res.ok) throw new Error('Failed to fetch synthesis results');
  return res.json();
}

export async function sendCustomQA(query: string, target_expert_ids?: string[]) {
  const res = await fetch(`${API_BASE}/qa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, target_expert_ids }),
  });
  if (!res.ok) throw new Error('Failed to execute custom QA');
  return res.json();
}

export async function uploadTranscriptFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/transcripts/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to upload transcript file' }));
    throw new Error(errorData.detail || 'Failed to upload transcript file');
  }
  return res.json();
}

export async function streamChatAnswer(
  query: string,
  target_expert_ids: string[] | undefined,
  onToken: (token: string) => void,
  onEvidence: (data: { evidence: RAGEvidenceItem[]; confidence: string; is_grounded: boolean }) => void,
  signal?: AbortSignal
) {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, target_expert_ids }),
    signal,
  });

  if (!res.ok) throw new Error('Failed to stream response');
  if (!res.body) return;

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const payloadStr = line.replace('data: ', '').trim();
        if (payloadStr === '[DONE]') break;

        try {
          const payload = JSON.parse(payloadStr);
          if (payload.type === 'token') {
            onToken(payload.content);
          } else if (payload.type === 'evidence') {
            onEvidence(payload);
          }
        } catch (err) {
          console.error('Failed to parse SSE payload:', err);
        }
      }
    }
  }
}

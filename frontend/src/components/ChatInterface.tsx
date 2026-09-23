import React, { useState, useRef, useEffect } from 'react';
import { Send, Square, Plus, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { ChatMessageItem } from '../types';
import { ChatMessage } from './ChatMessage';
import { ShinyText } from './ShinyText';
import { streamChatAnswer, uploadTranscriptFile } from '../services/api';

interface ChatInterfaceProps {
  currentMessages: ChatMessageItem[];
  onSaveMessages: (messages: ChatMessageItem[]) => void;
  onOpenExplorer: (filename: string, timestamp: string) => void;
  onTranscriptUploaded?: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  currentMessages,
  onSaveMessages,
  onOpenExplorer,
  onTranscriptUploaded,
}) => {
  const [messages, setMessages] = useState<ChatMessageItem[]>(currentMessages || []);
  const [inputQuery, setInputQuery] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  // Sync when active session changes
  useEffect(() => {
    setMessages(currentMessages || []);
  }, [currentMessages]);

  // Upload feedback toast state
  const [uploadToast, setUploadToast] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  // Auto-dismiss upload toast
  useEffect(() => {
    if (uploadToast) {
      const timer = setTimeout(() => setUploadToast(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [uploadToast]);

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || isGenerating) return;

    const userMsgId = Date.now().toString();
    const assistantMsgId = (Date.now() + 1).toString();

    // Append User Message
    const userMsg: ChatMessageItem = {
      id: userMsgId,
      role: 'user',
      content: textToSend.trim(),
    };

    // Append Assistant Placeholder
    const assistantMsg: ChatMessageItem = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      evidence: [],
      isStreaming: true,
    };

    const initialMsgs = [...messages, userMsg, assistantMsg];
    setMessages(initialMsgs);
    onSaveMessages(initialMsgs);
    setInputQuery('');
    setIsGenerating(true);

    const controller = new AbortController();
    setAbortController(controller);

    try {
      await streamChatAnswer(
        textToSend.trim(),
        undefined,
        (token) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, content: msg.content + token }
                : msg
            )
          );
        },
        (payload) => {
          setMessages((prev) => {
            const updated = prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    evidence: payload.evidence,
                    confidence: payload.confidence,
                    isGrounded: payload.is_grounded,
                    isStreaming: false,
                  }
                : msg
            );
            onSaveMessages(updated);
            return updated;
          });
        },
        controller.signal
      );
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages((prev) => {
          const updated = prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: "Unable to connect to the backend server. Please verify the Render service is running and retry.",
                  isStreaming: false,
                }
              : msg
          );
          onSaveMessages(updated);
          return updated;
        });
      }
    } finally {
      setIsGenerating(false);
      setAbortController(null);
    }
  };

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
      setIsGenerating(false);
      setMessages((prev) =>
        prev.map((msg) => (msg.isStreaming ? { ...msg, isStreaming: false } : msg))
      );
    }
  };

  // Handle Transcript File Upload via "+" button
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.txt')) {
      setUploadToast({ type: 'error', text: 'Please upload a .txt transcript file.' });
      return;
    }

    setIsUploading(true);
    try {
      const res = await uploadTranscriptFile(file);
      setUploadToast({
        type: 'success',
        text: `Uploaded & indexed: ${res.expert.name} (${res.expert.market})`,
      });
      if (onTranscriptUploaded) {
        onTranscriptUploaded();
      }
    } catch (err: any) {
      setUploadToast({
        type: 'error',
        text: err.message || 'Failed to upload transcript file.',
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const samplePrompts = [
    "What are the main adoption barriers in Germany vs the UK?",
    "How does surgeon training affect hospital utilization?",
    "Where do the experts disagree about cost?",
    "How long does a typical purchase decision take across hospitals?",
  ];

  const isEmptyState = messages.length === 0;

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden relative">
      {/* Toast Notification */}
      {uploadToast && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 transition-all duration-300">
          <div
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-full shadow-lg text-xs font-medium border backdrop-blur-md ${
              uploadToast.type === 'success'
                ? 'bg-emerald-50/95 border-emerald-200 text-emerald-800 dark:bg-emerald-950/90 dark:border-emerald-800 dark:text-emerald-200'
                : 'bg-rose-50/95 border-rose-200 text-rose-800 dark:bg-rose-950/90 dark:border-rose-800 dark:text-rose-200'
            }`}
          >
            {uploadToast.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400" />
            )}
            <span>{uploadToast.text}</span>
          </div>
        </div>
      )}

      {/* Hidden File Input for Transcript Uploads */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt"
        className="hidden"
        onChange={handleFileChange}
      />

      {isEmptyState ? (
        /* Empty State: Centered Shiny Headline + Subtext + Centered Composer */
        <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 max-w-2xl mx-auto w-full">
          {/* Animated Shiny Headline and Subtitle */}
          <div className="text-center mb-8 select-none">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-slate-800 dark:text-slate-100 leading-tight">
              How can I{' '}
              <ShinyText className="font-bold">
                help
              </ShinyText>{' '}
              you today?
            </h1>
            <p className="mt-3 text-sm sm:text-base text-slate-500 dark:text-slate-400 max-w-lg mx-auto font-normal leading-relaxed">
              Get grounded answers with exact quotes and timestamps from your expert transcripts.
            </p>
          </div>

          {/* Centered Composer in Empty State */}
          <div className="w-full relative">
            <div className="flex items-center bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border border-slate-200/90 dark:border-slate-800/80 rounded-full shadow-lg shadow-slate-200/50 dark:shadow-none p-1.5 transition-all focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-500">
              {/* + Button for Transcript Upload */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading || isGenerating}
                className="w-10 h-10 rounded-full flex items-center justify-center text-slate-500 hover:text-blue-600 hover:bg-blue-50 dark:text-slate-400 dark:hover:bg-slate-800 transition flex-shrink-0"
                title="Upload additional transcript file (.txt)"
              >
                <Plus className={`w-5 h-5 ${isUploading ? 'animate-spin' : ''}`} />
              </button>

              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask about barriers, reimbursement, training, timelines..."
                className="flex-1 px-3 py-2 bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none"
              />

              <button
                type="button"
                onClick={() => handleSend()}
                disabled={!inputQuery.trim() || isGenerating}
                className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-200 dark:disabled:bg-slate-800 text-white flex items-center justify-center transition shadow-sm flex-shrink-0 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>

            {/* Suggested Prompts */}
            <div className="mt-6 flex flex-wrap justify-center gap-2.5">
              {samplePrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(prompt)}
                  className="inline-flex items-center space-x-2 text-xs bg-white/80 dark:bg-slate-900/70 hover:bg-white dark:hover:bg-slate-850 border border-white/80 dark:border-slate-800/80 text-slate-700 dark:text-slate-300 rounded-full px-4 py-2 transition-all shadow-xs hover:shadow-md hover:scale-[1.02] backdrop-blur-md"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
                  <span>{prompt}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Active Conversation: Full-Frame Scrolling Thread */
        <div className="flex-1 flex flex-col h-full overflow-hidden">
          {/* Scrolling Messages */}
          <div className="flex-1 overflow-y-auto px-4 md:px-12 py-8 space-y-4">
            <div className="max-w-4xl mx-auto w-full">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} onOpenExplorer={onOpenExplorer} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Bottom Pinned Composer */}
          <div className="p-4 bg-white/30 dark:bg-slate-950/30 backdrop-blur-md border-t border-white/50 dark:border-slate-800/50">
            <div className="max-w-3xl mx-auto relative flex items-center bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border border-slate-200/90 dark:border-slate-800/80 rounded-full shadow-lg shadow-slate-200/40 dark:shadow-none p-1.5 focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-500">
              {/* + Button for Transcript Upload */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading || isGenerating}
                className="w-10 h-10 rounded-full flex items-center justify-center text-slate-500 hover:text-blue-600 hover:bg-blue-50 dark:text-slate-400 dark:hover:bg-slate-800 transition flex-shrink-0"
                title="Upload additional transcript file (.txt)"
              >
                <Plus className={`w-5 h-5 ${isUploading ? 'animate-spin' : ''}`} />
              </button>

              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask a question grounded in transcripts..."
                disabled={isGenerating}
                className="flex-1 px-3 py-2 bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none"
              />

              <div className="flex-shrink-0 pr-1">
                {isGenerating ? (
                  <button
                    onClick={handleStop}
                    className="flex items-center space-x-1 px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-full text-xs font-semibold transition shadow-sm"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>Stop</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleSend()}
                    disabled={!inputQuery.trim()}
                    className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-200 dark:disabled:bg-slate-800 text-white flex items-center justify-center transition shadow-sm disabled:cursor-not-allowed"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
            <div className="text-[11px] text-center text-slate-400 dark:text-slate-500 mt-2 font-medium">
              Grounding active — Every factual claim validated with exact timestamped quotes.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

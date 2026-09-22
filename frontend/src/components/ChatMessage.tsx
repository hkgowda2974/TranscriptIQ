import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, ShieldCheck, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { ChatMessageItem } from '../types';
import { EvidenceCard } from './EvidenceCard';

interface ChatMessageProps {
  message: ChatMessageItem;
  onOpenExplorer?: (filename: string, timestamp: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onOpenExplorer }) => {
  const [showEvidence, setShowEvidence] = useState(true);
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end mb-5">
        <div className="flex items-start max-w-2xl space-x-2.5">
          <div className="bg-blue-600 text-white rounded-3xl rounded-br-sm px-5 py-3.5 text-sm shadow-md shadow-blue-600/15 leading-relaxed">
            {message.content}
          </div>
          <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 flex items-center justify-center flex-shrink-0 text-xs font-semibold shadow-sm border border-blue-200 dark:border-blue-900">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  const isThinking = message.isStreaming && !message.content;

  return (
    <div className="flex justify-start mb-6">
      <div className="flex items-start max-w-3xl space-x-3 w-full">
        {/* Assistant Avatar */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center flex-shrink-0 text-xs shadow-md shadow-blue-600/20">
          <Bot className="w-4 h-4" />
        </div>

        {/* Assistant Glass Bubble */}
        <div className="flex-1 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-white/60 dark:border-slate-800/60 rounded-3xl rounded-bl-sm p-5 shadow-sm">
          {/* Thinking State */}
          {isThinking && (
            <div className="flex items-center space-x-2 py-1 text-slate-500 dark:text-slate-400 text-xs font-medium">
              <Sparkles className="w-4 h-4 text-blue-500 animate-spin" />
              <span>Analyzing grounded transcripts across markets...</span>
            </div>
          )}

          {/* Narrative Content */}
          {message.content && (
            <div className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-normal prose dark:prose-invert max-w-none prose-p:my-2 prose-ul:my-2 prose-li:my-0.5">
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {message.isStreaming && <span className="animate-typing-cursor inline-block w-1.5 h-4 bg-blue-600 ml-1"></span>}
            </div>
          )}

          {/* Evidence Cards Accordion */}
          {message.evidence && message.evidence.length > 0 && (
            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80">
              <div
                onClick={() => setShowEvidence(!showEvidence)}
                className="flex items-center justify-between text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer select-none mb-2 transition"
              >
                <div className="flex items-center space-x-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    Verified Grounded Evidence ({message.evidence.length} {message.evidence.length === 1 ? 'Quote' : 'Quotes'})
                  </span>
                </div>
                <button className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition">
                  {showEvidence ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              </div>

              {showEvidence && (
                <div className="space-y-2 mt-2">
                  {message.evidence.map((ev, idx) => (
                    <EvidenceCard key={idx} evidence={ev} onOpenExplorer={onOpenExplorer} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { Clock, CheckCircle2, FileText, ArrowUpRight } from 'lucide-react';
import { RAGEvidenceItem } from '../types';

interface EvidenceCardProps {
  evidence: RAGEvidenceItem;
  onOpenExplorer?: (filename: string, timestamp: string) => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence, onOpenExplorer }) => {
  const isFrance = evidence.expert.toLowerCase().includes('france') || evidence.source.includes('1');
  const isGermany = evidence.expert.toLowerCase().includes('germany') || evidence.source.includes('2');

  return (
    <div
      onClick={() => onOpenExplorer && onOpenExplorer(evidence.source, evidence.timestamp)}
      className="group relative bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-900/40 rounded-2xl p-4 my-2.5 text-xs transition duration-200 hover:shadow-md hover:border-amber-300 dark:hover:border-amber-700 cursor-pointer backdrop-blur-sm"
    >
      {/* Header Metadata */}
      <div className="flex items-center justify-between gap-2 mb-2 flex-wrap">
        <div className="flex items-center space-x-1.5 flex-wrap gap-y-1">
          {/* Expert pill badge */}
          <span
            className={`px-2.5 py-0.5 rounded-full font-semibold text-[11px] shadow-sm ${
              isFrance
                ? 'bg-rose-100/90 text-rose-700 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-200/60 dark:border-rose-900'
                : isGermany
                ? 'bg-amber-100/90 text-amber-700 dark:bg-amber-950/80 dark:text-amber-300 border border-amber-200/60 dark:border-amber-900'
                : 'bg-sky-100/90 text-sky-700 dark:bg-sky-950/80 dark:text-sky-300 border border-sky-200/60 dark:border-sky-900'
            }`}
          >
            {evidence.expert}
          </span>

          {/* Timestamp Pill */}
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-blue-50/80 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-mono font-medium text-[11px] border border-blue-200/60 dark:border-blue-800/60">
            <Clock className="w-3 h-3 text-blue-500" />
            <span>{evidence.timestamp}</span>
          </span>

          {/* Verification Badge */}
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50/80 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-semibold text-[10px] border border-emerald-200/70 dark:border-emerald-800/60">
            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            <span>{evidence.verification_status}</span>
          </span>
        </div>

        {/* View source prompt */}
        <div className="opacity-0 group-hover:opacity-100 transition flex items-center space-x-0.5 text-[11px] text-blue-600 dark:text-blue-400 font-medium">
          <span>Jump to turn</span>
          <ArrowUpRight className="w-3 h-3" />
        </div>
      </div>

      {/* Quote Block */}
      <div className="font-serif italic text-slate-800 dark:text-slate-200 text-xs sm:text-[13px] leading-relaxed pl-1 my-1.5 border-l-2 border-amber-400/80 dark:border-amber-500/60 pl-3 py-0.5">
        "{evidence.quote}"
      </div>

      {/* Source Filename */}
      <div className="flex items-center space-x-1 text-[10px] text-slate-400 dark:text-slate-500 mt-1 font-mono">
        <FileText className="w-3 h-3" />
        <span>{evidence.source}</span>
      </div>
    </div>
  );
};

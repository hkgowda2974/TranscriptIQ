import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  AlertTriangle,
  Users,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Filter,
  ExternalLink,
} from 'lucide-react';
import { SynthesisResult } from '../types';
import { EvidenceCard } from './EvidenceCard';
import { fetchSynthesis } from '../services/api';

interface ThemesDisagreementsViewProps {
  onOpenExplorer: (filename: string, timestamp: string) => void;
}

export const ThemesDisagreementsView: React.FC<ThemesDisagreementsViewProps> = ({
  onOpenExplorer,
}) => {
  const [synthesis, setSynthesis] = useState<SynthesisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterMode, setFilterMode] = useState<'all' | 'themes' | 'disagreements'>('all');
  const [expandedThemes, setExpandedThemes] = useState<Record<number, boolean>>({ 0: true });

  useEffect(() => {
    fetchSynthesis()
      .then((data) => setSynthesis(data))
      .catch((err) => console.error('Failed to load synthesis:', err))
      .finally(() => setLoading(false));
  }, []);

  const toggleTheme = (idx: number) => {
    setExpandedThemes((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
        <div className="p-4 rounded-3xl bg-white/70 dark:bg-slate-850/70 backdrop-blur-xl border border-white/60 dark:border-slate-800 shadow-sm max-w-sm">
          <Sparkles className="w-8 h-8 animate-spin mx-auto mb-3 text-purple-600 dark:text-purple-400" />
          <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
            Synthesizing Cross-Market Intelligence...
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Analyzing consensus patterns and policy divergence across France, Germany, and the UK.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 md:p-8 overflow-y-auto w-full max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800/80">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-50/90 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 text-xs font-semibold mb-2 border border-purple-200/60 dark:border-purple-800/40 shadow-sm backdrop-blur-sm">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Cross-Market Strategic Synthesis</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Themes & Disagreements
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            Identifies shared European consensus supported by multi-expert evidence alongside contrasting strategic and economic approaches.
          </p>
        </div>

        {/* View Mode Filter Pills */}
        <div className="flex items-center gap-1.5 p-1 rounded-full bg-white/80 dark:bg-slate-850/80 backdrop-blur-md border border-slate-200/80 dark:border-slate-800 shadow-sm flex-shrink-0">
          <button
            onClick={() => setFilterMode('all')}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
              filterMode === 'all'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            All Views
          </button>
          <button
            onClick={() => setFilterMode('themes')}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
              filterMode === 'themes'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Consensus Only
          </button>
          <button
            onClick={() => setFilterMode('disagreements')}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
              filterMode === 'disagreements'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Disagreements
          </button>
        </div>
      </div>

      {/* Main Content Layout */}
      <div
        className={`grid gap-8 ${
          filterMode === 'all' ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'
        }`}
      >
        {/* LEFT COLUMN: COMMON CONSENSUS THEMES */}
        {(filterMode === 'all' || filterMode === 'themes') && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-emerald-200/60 dark:border-emerald-900/40">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300">
                  <Users className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100">
                    Common Consensus Themes
                  </h2>
                  <span className="text-[11px] text-slate-400">
                    Substantiated by $\ge 2$ independent expert transcripts
                  </span>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200/60">
                {synthesis?.common_themes.length || 0} Themes
              </span>
            </div>

            <div className="space-y-4">
              {synthesis?.common_themes.map((theme, idx) => {
                const isExpanded = expandedThemes[idx] ?? true;

                return (
                  <div
                    key={idx}
                    className="rounded-3xl bg-white/80 dark:bg-slate-850/80 backdrop-blur-xl border border-white/70 dark:border-slate-800 p-5 sm:p-6 shadow-sm hover:shadow-md transition-all border-l-4 border-l-emerald-500"
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 dark:text-emerald-300">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                            Multi-Market Consensus
                          </span>
                        </div>
                        <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">
                          {theme.theme_title}
                        </h3>
                      </div>

                      <button
                        onClick={() => toggleTheme(idx)}
                        className="p-1.5 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        title={isExpanded ? 'Collapse' : 'Expand'}
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                    </div>

                    <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed mb-4 font-normal">
                      {theme.description}
                    </p>

                    {/* Supporting Expert Pills */}
                    <div className="mb-4">
                      <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-1.5">
                        Supporting Experts:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {theme.supporting_experts.map((exp, i) => (
                          <span
                            key={i}
                            className="px-3 py-1 rounded-full bg-emerald-50/90 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-200 text-xs font-medium border border-emerald-200/60 dark:border-emerald-800/40 shadow-sm"
                          >
                            {exp}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Expandable Per-Expert Evidence Accordion */}
                    {isExpanded && (
                      <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 space-y-3">
                        <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                          Verified Supporting Evidence:
                        </span>
                        {theme.per_expert_evidence.map((pe, i) => (
                          <div
                            key={i}
                            className="p-3.5 rounded-2xl bg-slate-50/70 dark:bg-slate-900/60 border border-slate-200/60 dark:border-slate-800/60 space-y-2"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-xs text-slate-800 dark:text-slate-200">
                                {pe.expert_name} ({pe.market})
                              </span>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400 italic">
                              {pe.position_summary}
                            </p>
                            <div className="space-y-1.5 pt-1">
                              {pe.evidence_quotes.map((ev, k) => (
                                <EvidenceCard
                                  key={k}
                                  evidence={ev}
                                  onOpenExplorer={onOpenExplorer}
                                />
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* RIGHT COLUMN: DISAGREEMENTS & DIFFERENCES */}
        {(filterMode === 'all' || filterMode === 'disagreements') && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-amber-200/60 dark:border-amber-900/40">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-xl bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100">
                    Disagreements & Market Divergence
                  </h2>
                  <span className="text-[11px] text-slate-400">
                    Contrasting procurement models, economic tests, and health policy
                  </span>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-200/60">
                {synthesis?.disagreements.length || 0} Divergences
              </span>
            </div>

            <div className="space-y-4">
              {synthesis?.disagreements.map((dis, idx) => (
                <div
                  key={idx}
                  className="rounded-3xl bg-white/80 dark:bg-slate-850/80 backdrop-blur-xl border border-white/70 dark:border-slate-800 p-5 sm:p-6 shadow-sm hover:shadow-md transition-all border-l-4 border-l-amber-500"
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">
                      {dis.topic}
                    </h3>
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-100/90 dark:bg-amber-950/70 text-amber-800 dark:text-amber-300 text-[10px] font-bold border border-amber-200/80 dark:border-amber-800 flex-shrink-0">
                      {dis.relationship_type}
                    </span>
                  </div>

                  <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed mb-4 font-normal">
                    {dis.description}
                  </p>

                  <div className="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                    <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                      Direct Market Stances:
                    </span>
                    {dis.expert_positions.map((pos, i) => (
                      <div
                        key={i}
                        className="p-4 bg-slate-50/80 dark:bg-slate-900/60 rounded-2xl border border-slate-200/70 dark:border-slate-800 space-y-2"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-bold text-xs text-slate-800 dark:text-slate-200">
                            {pos.expert_name} ({pos.market})
                          </span>
                          <button
                            onClick={() => onOpenExplorer(pos.source, pos.timestamp)}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 border border-slate-200 dark:border-slate-700 hover:border-blue-400 transition-colors"
                            title="Jump to quote in transcript"
                          >
                            <span>⏱️ {pos.timestamp}</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </button>
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-400">
                          <strong className="text-slate-700 dark:text-slate-300">Stance:</strong> {pos.position_summary}
                        </p>
                        <div className="font-serif italic text-xs text-slate-800 dark:text-slate-200 bg-amber-50/70 dark:bg-amber-950/20 p-2.5 rounded-xl border-l-2 border-amber-400 leading-relaxed">
                          &ldquo;{pos.verbatim_quote}&rdquo;
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ThemesDisagreementsView;

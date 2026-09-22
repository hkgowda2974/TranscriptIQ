import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  Play,
  Sparkles,
  ChevronRight,
  TrendingUp,
  ShieldAlert,
  Coins,
  GraduationCap,
  Calendar,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import { InterviewQuestion, ExpertMetadata, ExpertGuidedAnswer } from '../types';
import { EvidenceCard } from './EvidenceCard';
import { fetchMatrix } from '../services/api';

interface InterviewGuideViewProps {
  questions: InterviewQuestion[];
  experts: ExpertMetadata[];
  onOpenExplorer: (filename: string, timestamp: string) => void;
}

const QUESTION_TOPIC_ICONS: Record<number, React.ReactNode> = {
  1: <TrendingUp className="w-3.5 h-3.5 text-blue-500" />,
  2: <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />,
  3: <Coins className="w-3.5 h-3.5 text-amber-500" />,
  4: <GraduationCap className="w-3.5 h-3.5 text-purple-500" />,
  5: <Calendar className="w-3.5 h-3.5 text-teal-500" />,
  6: <Clock className="w-3.5 h-3.5 text-indigo-500" />,
};

const QUESTION_TOPIC_LABELS: Record<number, string> = {
  1: 'Current Adoption',
  2: 'Adoption Barriers',
  3: 'Budgets & ROI',
  4: 'Surgeon Training',
  5: '3–5 Year Outlook',
  6: 'Decision Timeline',
};

export const InterviewGuideView: React.FC<InterviewGuideViewProps> = ({
  questions,
  experts,
  onOpenExplorer,
}) => {
  const [matrixData, setMatrixData] = useState<Record<number, ExpertGuidedAnswer[]> | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedQuestionId, setSelectedQuestionId] = useState<number>(questions[0]?.question_id || 1);

  const handleAnalyzeMatrix = async () => {
    setLoading(true);
    try {
      const data = await fetchMatrix();
      const grouped: Record<number, ExpertGuidedAnswer[]> = {};
      data.forEach((item: any) => {
        if (!grouped[item.question_id]) grouped[item.question_id] = [];
        grouped[item.question_id].push({
          expert_id: item.expert_id,
          expert_name: item.expert_name,
          market: item.market,
          summary_answer: item.summary_answer,
          key_findings: item.key_findings || [],
          evidence: item.evidence || [],
        });
      });
      setMatrixData(grouped);
    } catch (err) {
      console.error('Matrix execution failed:', err);
    } finally {
      setLoading(false);
    }
  };

  // Automatically fetch matrix on first mount if not loaded
  useEffect(() => {
    if (!matrixData && !loading) {
      handleAnalyzeMatrix();
    }
  }, []);

  const selectedQuestion = questions.find((q) => q.question_id === selectedQuestionId) || questions[0];

  return (
    <div className="flex-1 p-6 md:p-8 overflow-y-auto w-full max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800/80">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50/90 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-xs font-semibold mb-2 border border-indigo-200/60 dark:border-indigo-800/40 shadow-sm backdrop-blur-sm">
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Canonical Interview-Guide Matrix</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Interview-Guide Cross-Market Matrix
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            Compare responses across France, Germany, and the UK for each canonical guide question with verified timestamped evidence.
          </p>
        </div>

        <button
          onClick={handleAnalyzeMatrix}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-semibold shadow-md shadow-blue-500/10 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 flex-shrink-0"
        >
          {loading ? (
            <>
              <Sparkles className="w-4 h-4 animate-spin text-white" />
              <span>Analyzing Guide...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Refresh Matrix</span>
            </>
          )}
        </button>
      </div>

      {/* Question Selector Tabs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {questions.map((q) => {
          const isSelected = selectedQuestionId === q.question_id;
          const topicLabel = QUESTION_TOPIC_LABELS[q.question_id] || `Topic ${q.question_id}`;
          const topicIcon = QUESTION_TOPIC_ICONS[q.question_id] || <FileSpreadsheet className="w-3.5 h-3.5" />;

          return (
            <button
              key={q.question_id}
              onClick={() => setSelectedQuestionId(q.question_id)}
              className={`p-3 rounded-2xl text-left transition-all backdrop-blur-md border flex flex-col justify-between ${
                isSelected
                  ? 'bg-white/95 dark:bg-slate-850/95 border-blue-500/80 shadow-md ring-2 ring-blue-500/20 text-slate-900 dark:text-slate-100'
                  : 'bg-white/60 dark:bg-slate-900/60 border-slate-200/70 dark:border-slate-800/70 text-slate-600 dark:text-slate-400 hover:bg-white/80 dark:hover:bg-slate-850/80 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-2 w-full">
                <span className="flex items-center gap-1.5 text-xs font-semibold text-blue-600 dark:text-blue-400">
                  {topicIcon}
                  <span>Q{q.question_id}</span>
                </span>
                <span className="text-[10px] font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  {topicLabel}
                </span>
              </div>
              <p className="text-[11px] leading-snug line-clamp-2 font-normal text-slate-700 dark:text-slate-300">
                {q.question_text}
              </p>
            </button>
          );
        })}
      </div>

      {/* Active Question Hero Card */}
      {selectedQuestion && (
        <div className="p-4 sm:p-5 rounded-3xl bg-white/80 dark:bg-slate-850/80 backdrop-blur-xl border border-white/70 dark:border-slate-800 shadow-sm flex items-start gap-3">
          <div className="p-2 rounded-2xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300">
                Question {selectedQuestion.question_id}
              </span>
              <span className="text-xs font-semibold text-slate-400 dark:text-slate-500">
                {QUESTION_TOPIC_LABELS[selectedQuestion.question_id]}
              </span>
            </div>
            <h2 className="text-base sm:text-lg font-semibold text-slate-900 dark:text-slate-100">
              {selectedQuestion.question_text}
            </h2>
          </div>
        </div>
      )}

      {/* Results Grid: 3 Market Columns */}
      {loading ? (
        <div className="p-16 text-center rounded-3xl bg-white/60 dark:bg-slate-900/60 backdrop-blur-md border border-white/50 dark:border-slate-800">
          <Sparkles className="w-8 h-8 animate-spin mx-auto mb-3 text-blue-500" />
          <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            Synthesizing Expert Responses & Extracting Verbatim Evidence...
          </h3>
          <p className="text-xs text-slate-400 mt-1">Cross-referencing transcripts for France, Germany, and the UK.</p>
        </div>
      ) : matrixData && selectedQuestion ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {(matrixData[selectedQuestionId] || []).map((ans) => {
            const isFrance = ans.market.toLowerCase().includes('france');
            const isGermany = ans.market.toLowerCase().includes('germany');

            const marketBadgeClass = isFrance
              ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 border-rose-200/80 dark:border-rose-900/50'
              : isGermany
              ? 'bg-amber-50 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300 border-amber-200/80 dark:border-amber-900/50'
              : 'bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300 border-sky-200/80 dark:border-sky-900/50';

            const cardBorderClass = isFrance
              ? 'hover:border-rose-300/80 dark:hover:border-rose-700/60'
              : isGermany
              ? 'hover:border-amber-300/80 dark:hover:border-amber-700/60'
              : 'hover:border-sky-300/80 dark:hover:border-sky-700/60';

            return (
              <div
                key={ans.expert_id}
                className={`flex flex-col justify-between rounded-3xl bg-white/80 dark:bg-slate-850/80 backdrop-blur-xl border border-white/70 dark:border-slate-800 p-5 sm:p-6 shadow-sm transition-all hover:shadow-md ${cardBorderClass}`}
              >
                <div>
                  {/* Column Top Header */}
                  <div className="flex items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
                    <div>
                      <h3 className="font-bold text-sm sm:text-base text-slate-900 dark:text-slate-100">
                        {ans.expert_name}
                      </h3>
                      <span className="text-[11px] text-slate-400">
                        Expert ID: {ans.expert_id}
                      </span>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold border shadow-sm ${marketBadgeClass}`}
                    >
                      {ans.market}
                    </span>
                  </div>

                  {/* Summary Answer */}
                  <div className="mb-4">
                    <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-1.5">
                      Synthesized Position
                    </span>
                    <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
                      {ans.summary_answer}
                    </p>
                  </div>

                  {/* Key Findings Bullet List */}
                  {ans.key_findings && ans.key_findings.length > 0 && (
                    <div className="mb-5">
                      <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-2">
                        Key Strategic Findings
                      </span>
                      <ul className="space-y-1.5">
                        {ans.key_findings.map((kf, i) => (
                          <li
                            key={i}
                            className="text-xs text-slate-600 dark:text-slate-300 flex items-start gap-2 bg-slate-50/70 dark:bg-slate-900/50 p-2 rounded-xl border border-slate-100 dark:border-slate-800"
                          >
                            <ChevronRight className="w-3.5 h-3.5 text-blue-500 flex-shrink-0 mt-0.5" />
                            <span className="leading-snug">{kf}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Evidence Quotes Section */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
                  <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block mb-2">
                    Verified Citations ({ans.evidence.length})
                  </span>
                  {ans.evidence && ans.evidence.length > 0 ? (
                    <div className="space-y-2">
                      {ans.evidence.map((ev, i) => (
                        <EvidenceCard
                          key={`${ev.expert}-${ev.timestamp}-${i}`}
                          evidence={ev}
                          onOpenExplorer={onOpenExplorer}
                        />
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 rounded-2xl bg-slate-50/60 dark:bg-slate-900/40 text-xs text-slate-400 italic text-center border border-dashed border-slate-200 dark:border-slate-800">
                      No verified quotation for this topic.
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="p-16 text-center rounded-3xl bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl border border-white/60 dark:border-slate-800 shadow-sm">
          <FileSpreadsheet className="w-12 h-12 text-indigo-400 mx-auto mb-3 opacity-60" />
          <h3 className="font-semibold text-slate-800 dark:text-slate-200 text-base mb-1">
            Canonical Matrix Ready
          </h3>
          <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto mb-4">
            Click the button above to evaluate all 6 interview-guide questions across France, Germany, and the UK.
          </p>
          <button
            onClick={handleAnalyzeMatrix}
            className="px-5 py-2.5 rounded-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition-all hover:scale-105"
          >
            Run Full Matrix Analysis
          </button>
        </div>
      )}
    </div>
  );
};

export default InterviewGuideView;

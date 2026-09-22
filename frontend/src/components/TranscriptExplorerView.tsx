import React, { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Clock,
  User,
  Search,
  CheckCircle2,
  Bookmark,
  Share2,
  X,
  Sparkles,
} from 'lucide-react';
import { ExpertMetadata } from '../types';
import { fetchTranscripts } from '../services/api';

interface TranscriptExplorerViewProps {
  experts: ExpertMetadata[];
  initialDoc?: string;
  initialTimestamp?: string;
}

interface ParsedTurn {
  index: number;
  timestamp: string;
  speaker: string;
  text: string;
}

export const TranscriptExplorerView: React.FC<TranscriptExplorerViewProps> = ({
  experts,
  initialDoc = 'expert_1.txt',
  initialTimestamp,
}) => {
  const [selectedDoc, setSelectedDoc] = useState<string>(initialDoc);
  const [activeTimestamp, setActiveTimestamp] = useState<string | undefined>(initialTimestamp);
  const [rawTranscripts, setRawTranscripts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const activeTurnRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchTranscripts()
      .then((data) => {
        setRawTranscripts(data.raw_transcripts || {});
      })
      .catch((err) => console.error('Failed to load transcripts:', err))
      .finally(() => setLoading(false));
  }, []);

  // Update selected doc or timestamp if incoming props change
  useEffect(() => {
    if (initialDoc) setSelectedDoc(initialDoc);
  }, [initialDoc]);

  useEffect(() => {
    if (initialTimestamp) setActiveTimestamp(initialTimestamp);
  }, [initialTimestamp]);

  // Smooth scroll to active timestamp turn when it changes or when content is loaded
  useEffect(() => {
    if (activeTimestamp && activeTurnRef.current) {
      setTimeout(() => {
        activeTurnRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 250);
    }
  }, [activeTimestamp, selectedDoc, rawTranscripts]);

  const currentContent = rawTranscripts[selectedDoc] || '';
  const currentExpert = experts.find((e) => e.source_file === selectedDoc);

  // Parse raw text into structured turns if it's an expert transcript
  const parseTurns = (content: string): ParsedTurn[] => {
    if (!content) return [];
    const lines = content.split('\n');
    const turns: ParsedTurn[] = [];

    let currentTimestamp = '';
    let currentSpeaker = '';
    let currentTextLines: string[] = [];
    let turnIndex = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Check for timestamp pattern (e.g., 00:00, 01:15, 03:06)
      const tsMatch = line.match(/^(\d{1,2}:\d{2})$/);
      if (tsMatch) {
        if (currentSpeaker && currentTextLines.length > 0) {
          turns.push({
            index: turnIndex++,
            timestamp: currentTimestamp,
            speaker: currentSpeaker,
            text: currentTextLines.join(' ').trim(),
          });
          currentTextLines = [];
        }
        currentTimestamp = tsMatch[1];
        continue;
      }

      // Check for speaker pattern (e.g., "Interviewer: ...", "Dr. Dubois: ...", "Anna Keller: ...")
      const speakerMatch = line.match(/^([A-Za-z0-9\.\s–—]+):\s*(.*)$/);
      if (speakerMatch && currentTimestamp) {
        if (currentSpeaker && currentTextLines.length > 0) {
          turns.push({
            index: turnIndex++,
            timestamp: currentTimestamp,
            speaker: currentSpeaker,
            text: currentTextLines.join(' ').trim(),
          });
          currentTextLines = [];
        }
        currentSpeaker = speakerMatch[1].trim();
        if (speakerMatch[2]) {
          currentTextLines.push(speakerMatch[2]);
        }
        continue;
      }

      if (line && currentSpeaker) {
        currentTextLines.push(line);
      }
    }

    if (currentSpeaker && currentTextLines.length > 0) {
      turns.push({
        index: turnIndex++,
        timestamp: currentTimestamp,
        speaker: currentSpeaker,
        text: currentTextLines.join(' ').trim(),
      });
    }

    return turns;
  };

  const parsedTurns = parseTurns(currentContent);

  // Filter turns by search term
  const filteredTurns = parsedTurns.filter((turn) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      turn.text.toLowerCase().includes(term) ||
      turn.speaker.toLowerCase().includes(term) ||
      turn.timestamp.includes(term)
    );
  });

  const highlightMatches = (text: string, term: string) => {
    if (!term.trim()) return text;
    const parts = text.split(new RegExp(`(${term})`, 'gi'));
    return (
      <>
        {parts.map((part, i) =>
          part.toLowerCase() === term.toLowerCase() ? (
            <mark
              key={i}
              className="bg-amber-200 dark:bg-amber-800 text-slate-900 dark:text-slate-100 rounded px-1 py-0.5"
            >
              {part}
            </mark>
          ) : (
            part
          )
        )}
      </>
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 sm:p-8 max-w-7xl mx-auto w-full space-y-4">
      {/* Top Navigation & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800/80 flex-shrink-0">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50/90 dark:bg-teal-950/40 text-teal-700 dark:text-teal-300 text-xs font-semibold mb-2 border border-teal-200/60 dark:border-teal-800/40 shadow-sm backdrop-blur-sm">
            <FileText className="w-3.5 h-3.5" />
            <span>Transcript & Source Explorer</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Source Dialogue Explorer
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            Inspect verbatim dialogue turns with verified timestamp alignment, speaker roles, and keyword filters.
          </p>
        </div>

        {/* Search Input Bar */}
        <div className="flex items-center gap-2 max-w-md w-full md:w-80">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search transcript text..."
              className="w-full pl-9 pr-8 py-2 rounded-full text-xs bg-white/90 dark:bg-slate-850/90 backdrop-blur-md border border-slate-200/80 dark:border-slate-800 text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Transcript Document Selector Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 flex-shrink-0">
        {experts.map((exp) => {
          const isSelected = selectedDoc === exp.source_file;
          const isFrance = exp.market.toLowerCase().includes('france');
          const isGermany = exp.market.toLowerCase().includes('germany');

          return (
            <button
              key={exp.expert_id}
              onClick={() => {
                setSelectedDoc(exp.source_file);
                setActiveTimestamp(undefined);
              }}
              className={`px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap transition-all border shadow-sm ${
                isSelected
                  ? 'bg-blue-600 text-white border-blue-600 shadow-md scale-105'
                  : 'bg-white/80 dark:bg-slate-850/80 text-slate-700 dark:text-slate-300 border-slate-200/70 dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800'
              }`}
            >
              <span>{exp.name}</span>
              <span className={`ml-2 text-[10px] px-2 py-0.5 rounded-full ${
                isSelected
                  ? 'bg-white/20 text-white'
                  : isFrance
                  ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300'
                  : isGermany
                  ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300'
                  : 'bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300'
              }`}>
                {exp.market}
              </span>
            </button>
          );
        })}

        <button
          onClick={() => {
            setSelectedDoc('interview_guide.txt');
            setActiveTimestamp(undefined);
          }}
          className={`px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap transition-all border shadow-sm ${
            selectedDoc === 'interview_guide.txt'
              ? 'bg-indigo-600 text-white border-indigo-600 shadow-md scale-105'
              : 'bg-white/80 dark:bg-slate-850/80 text-slate-700 dark:text-slate-300 border-slate-200/70 dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800'
          }`}
        >
          Interview Guide
        </button>
      </div>

      {/* Metadata Banner Card */}
      {currentExpert && (
        <div className="p-4 sm:p-5 rounded-3xl bg-white/80 dark:bg-slate-850/80 backdrop-blur-xl border border-white/70 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-sm shadow-sm flex-shrink-0">
              <User className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">
                  {currentExpert.name}
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-teal-50 dark:bg-teal-950/50 text-teal-700 dark:text-teal-300 border border-teal-200/60 dark:border-teal-800/40">
                  {currentExpert.market}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {currentExpert.role}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="font-mono bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-full text-[11px]">
              {selectedDoc}
            </span>
            <span>&bull;</span>
            <span>{parsedTurns.length} dialogue turns</span>
          </div>
        </div>
      )}

      {/* Main Dialogue Scrollable Body */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 rounded-3xl">
        {loading ? (
          <div className="p-16 text-center rounded-3xl bg-white/60 dark:bg-slate-900/60 backdrop-blur-md border border-white/50 dark:border-slate-800">
            <Sparkles className="w-8 h-8 animate-spin mx-auto mb-3 text-teal-500" />
            <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              Loading Transcript Turns...
            </h3>
          </div>
        ) : parsedTurns.length > 0 ? (
          filteredTurns.length > 0 ? (
            filteredTurns.map((turn) => {
              const isTargetTimestamp =
                activeTimestamp && turn.timestamp.trim() === activeTimestamp.trim();
              const isInterviewer = turn.speaker.toLowerCase().includes('interviewer');

              return (
                <div
                  key={turn.index}
                  ref={isTargetTimestamp ? activeTurnRef : null}
                  className={`rounded-3xl p-4 sm:p-5 transition-all backdrop-blur-md border ${
                    isTargetTimestamp
                      ? 'bg-amber-50/90 dark:bg-amber-950/40 border-amber-400 dark:border-amber-600 ring-4 ring-amber-400/20 shadow-lg'
                      : isInterviewer
                      ? 'bg-white/60 dark:bg-slate-900/50 border-slate-200/60 dark:border-slate-800/60'
                      : 'bg-white/85 dark:bg-slate-850/80 border-white/80 dark:border-slate-800 shadow-sm'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-3 py-0.5 rounded-full text-xs font-semibold ${
                          isInterviewer
                            ? 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                            : 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/40'
                        }`}
                      >
                        {turn.speaker}
                      </span>
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {turn.timestamp}
                      </span>
                    </div>

                    {isTargetTimestamp && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-200 border border-amber-300/80 dark:border-amber-700 shadow-sm animate-pulse">
                        <CheckCircle2 className="w-3 h-3 text-amber-600" />
                        Target Citation Turn
                      </span>
                    )}
                  </div>

                  <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-normal">
                    {highlightMatches(turn.text, searchTerm)}
                  </p>
                </div>
              );
            })
          ) : (
            <div className="p-12 text-center rounded-3xl bg-white/70 dark:bg-slate-850/70 border border-slate-200 dark:border-slate-800 text-xs text-slate-400">
              No dialogue turns match "{searchTerm}". Try a different keyword.
            </div>
          )
        ) : (
          /* Render raw text fallback (for interview_guide.txt or custom uploads) */
          <div className="bg-white/80 dark:bg-slate-900/80 border border-white/60 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-sm">
            <pre className="font-mono text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap overflow-x-auto">
              {currentContent}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default TranscriptExplorerView;

import React, { useState, useEffect } from 'react';
import { ActiveView, ExpertMetadata, InterviewQuestion, ChatSession, ChatMessageItem } from './types';
import { Sidebar } from './components/Sidebar';
import { ChatInterface } from './components/ChatInterface';
import { InterviewGuideView } from './components/InterviewGuideView';
import { ThemesDisagreementsView } from './components/ThemesDisagreementsView';
import { TranscriptExplorerView } from './components/TranscriptExplorerView';
import { fetchTranscripts } from './services/api';
import { BookOpen, FileSpreadsheet, Sparkles, FileText, ArrowRight, Building2 } from 'lucide-react';

const STORAGE_KEY = 'transcriptiq_chat_sessions_v1';

function getInitialSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch (e) {
    console.error('Error loading chat sessions:', e);
  }
  const defaultId = 'session_' + Date.now();
  return [
    {
      id: defaultId,
      title: 'New Conversation',
      timestamp: new Date().toISOString(),
      messages: [],
    },
  ];
}

export function App() {
  const [activeView, setActiveView] = useState<ActiveView>('chat');
  const [darkMode, setDarkMode] = useState<boolean>(false);
  const [experts, setExperts] = useState<ExpertMetadata[]>([]);
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [explorerTarget, setExplorerTarget] = useState<{ doc: string; timestamp?: string }>({
    doc: 'expert_1.txt',
  });

  const [sessions, setSessions] = useState<ChatSession[]>(getInitialSessions);
  const [activeSessionId, setActiveSessionId] = useState<string>(() => sessions[0]?.id || 'default');

  // Save sessions to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (e) {
      console.error('Error saving sessions:', e);
    }
  }, [sessions]);

  const loadData = () => {
    fetchTranscripts()
      .then((data) => {
        setExperts(data.experts || []);
        setQuestions(data.questions || []);
      })
      .catch((err) => console.error('Error loading transcripts:', err));
  };

  useEffect(() => {
    loadData();
  }, []);

  // Update dark mode html class
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const handleOpenExplorer = (filename: string, timestamp?: string) => {
    setExplorerTarget({ doc: filename, timestamp });
    setActiveView('explorer');
  };

  const handleNewChat = () => {
    // If the current active session is already clean/empty, just remain on it
    const current = sessions.find((s) => s.id === activeSessionId);
    if (current && current.messages.length === 0) {
      setActiveView('chat');
      return;
    }
    const newId = 'session_' + Date.now();
    const newSession: ChatSession = {
      id: newId,
      title: 'New Conversation',
      timestamp: new Date().toISOString(),
      messages: [],
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newId);
    setActiveView('chat');
  };

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
    setActiveView('chat');
  };

  const handleDeleteSession = (id: string) => {
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== id);
      if (filtered.length === 0) {
        const freshId = 'session_' + Date.now();
        const fresh: ChatSession = {
          id: freshId,
          title: 'New Conversation',
          timestamp: new Date().toISOString(),
          messages: [],
        };
        setActiveSessionId(freshId);
        return [fresh];
      }
      if (activeSessionId === id) {
        setActiveSessionId(filtered[0].id);
      }
      return filtered;
    });
  };

  const handleSaveMessages = (newMessages: ChatMessageItem[]) => {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id !== activeSessionId) return s;
        let title = s.title;
        if (title === 'New Conversation' || !title) {
          const firstUserMsg = newMessages.find((m) => m.role === 'user');
          if (firstUserMsg) {
            title = firstUserMsg.content.slice(0, 36) + (firstUserMsg.content.length > 36 ? '...' : '');
          }
        }
        return {
          ...s,
          title,
          messages: newMessages,
          timestamp: new Date().toISOString(),
        };
      })
    );
  };

  const currentSession = sessions.find((s) => s.id === activeSessionId) || sessions[0];

  return (
    <div className={`flex h-screen w-screen overflow-hidden ${darkMode ? 'dark' : ''}`}>
      <div className="flex h-full w-full overflow-hidden text-slate-900 dark:text-slate-100 transition-colors duration-300">
        {/* Sidebar Component with neutral light background */}
        <Sidebar
          activeView={activeView}
          setActiveView={setActiveView}
          onNewChat={handleNewChat}
          experts={experts}
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          onOpenExpertInExplorer={(doc) => handleOpenExplorer(doc)}
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
        />

        {/* Main Content View Container with visible Soft Pastel Gradient Background */}
        <main className="flex-1 flex flex-col h-screen overflow-hidden relative bg-gradient-to-br from-[#dbeafe] via-[#ede9fe] to-[#ccfbf1] dark:from-[#0B1120] dark:via-[#161233] dark:to-[#0A1A1E]">
          {/* View 1: Grounded Chat */}
          {activeView === 'chat' && (
            <ChatInterface
              key={activeSessionId}
              currentMessages={currentSession?.messages || []}
              onSaveMessages={handleSaveMessages}
              onOpenExplorer={handleOpenExplorer}
              onTranscriptUploaded={loadData}
            />
          )}

          {/* View 2: Library */}
          {activeView === 'library' && (
            <div className="flex-1 p-6 md:p-10 overflow-y-auto max-w-5xl mx-auto w-full">
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200/80 dark:border-slate-800/80">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center space-x-2">
                    <BookOpen className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                    <span>Transcript Library</span>
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Indexed expert call transcripts across France, Germany, and the United Kingdom.
                  </p>
                </div>
                <div className="text-xs font-semibold px-3 py-1 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                  {experts.length} Transcripts Indexed
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {experts.map((exp) => (
                  <div
                    key={exp.expert_id}
                    onClick={() => handleOpenExplorer(exp.source_file)}
                    className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-white/60 dark:border-slate-800/60 rounded-3xl p-5 shadow-sm hover:shadow-md hover:border-blue-300 dark:hover:border-blue-800 transition cursor-pointer flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-bold shadow-sm ${
                            exp.market.toLowerCase().includes('france')
                              ? 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300 border border-rose-200'
                              : exp.market.toLowerCase().includes('germany')
                              ? 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border border-amber-200'
                              : 'bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300 border border-sky-200'
                          }`}
                        >
                          {exp.market}
                        </span>
                        <span className="font-mono text-[11px] text-slate-400">
                          {exp.source_file}
                        </span>
                      </div>

                      <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 mb-1">
                        {exp.name}
                      </h3>
                      <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mb-4">
                        {exp.role}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-semibold text-blue-600 dark:text-blue-400">
                      <span>Explore Transcript</span>
                      <ArrowRight className="w-4 h-4" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* View 3: Deep Dive Analysis Hub */}
          {activeView === 'hub' && (
            <div className="flex-1 p-6 md:p-10 overflow-y-auto max-w-5xl mx-auto w-full">
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center space-x-2">
                  <Sparkles className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                  <span>Deep Dive Analysis Hub</span>
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Structured comparison, consensus synthesis, and raw evidence inspection across European healthcare systems.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Hub Card 1: Matrix */}
                <div
                  onClick={() => setActiveView('guide')}
                  className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-white/60 dark:border-slate-800/60 rounded-3xl p-6 shadow-sm hover:shadow-md hover:border-teal-300 dark:hover:border-teal-800 transition cursor-pointer flex flex-col justify-between"
                >
                  <div>
                    <div className="w-12 h-12 rounded-2xl bg-teal-100 dark:bg-teal-950 flex items-center justify-center text-teal-600 dark:text-teal-400 mb-4 shadow-sm">
                      <FileSpreadsheet className="w-6 h-6" />
                    </div>
                    <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 mb-2">
                      Interview Guide Matrix
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      Map each canonical research question across all 3 expert transcripts with side-by-side answers and verified quotes.
                    </p>
                  </div>
                  <div className="mt-6 flex items-center justify-between text-xs font-semibold text-teal-600 dark:text-teal-400">
                    <span>Open Matrix</span>
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </div>

                {/* Hub Card 2: Themes & Disagreements */}
                <div
                  onClick={() => setActiveView('synthesis')}
                  className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-white/60 dark:border-slate-800/60 rounded-3xl p-6 shadow-sm hover:shadow-md hover:border-amber-300 dark:hover:border-amber-800 transition cursor-pointer flex flex-col justify-between"
                >
                  <div>
                    <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-950 flex items-center justify-center text-amber-600 dark:text-amber-400 mb-4 shadow-sm">
                      <Sparkles className="w-6 h-6" />
                    </div>
                    <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 mb-2">
                      Themes & Disagreements
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      Identify verified common themes across markets and analyze nuanced disagreements in economic vs clinical strategy.
                    </p>
                  </div>
                  <div className="mt-6 flex items-center justify-between text-xs font-semibold text-amber-600 dark:text-amber-400">
                    <span>Open Synthesis</span>
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </div>

                {/* Hub Card 3: Transcript Explorer */}
                <div
                  onClick={() => setActiveView('explorer')}
                  className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-white/60 dark:border-slate-800/60 rounded-3xl p-6 shadow-sm hover:shadow-md hover:border-blue-300 dark:hover:border-blue-800 transition cursor-pointer flex flex-col justify-between"
                >
                  <div>
                    <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400 mb-4 shadow-sm">
                      <FileText className="w-6 h-6" />
                    </div>
                    <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 mb-2">
                      Transcript Explorer
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      Read full, unedited turn-by-turn transcripts with speaker differentiation, left-aligned timestamps, and deep linking.
                    </p>
                  </div>
                  <div className="mt-6 flex items-center justify-between text-xs font-semibold text-blue-600 dark:text-blue-400">
                    <span>Open Explorer</span>
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* View 4: Interview Guide Matrix */}
          {activeView === 'guide' && (
            <InterviewGuideView
              questions={questions}
              experts={experts}
              onOpenExplorer={handleOpenExplorer}
            />
          )}

          {/* View 5: Themes & Disagreements */}
          {activeView === 'synthesis' && (
            <ThemesDisagreementsView onOpenExplorer={handleOpenExplorer} />
          )}

          {/* View 6: Transcript Explorer */}
          {activeView === 'explorer' && (
            <TranscriptExplorerView
              experts={experts}
              initialDoc={explorerTarget.doc}
              initialTimestamp={explorerTarget.timestamp}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;

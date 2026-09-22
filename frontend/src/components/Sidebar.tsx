import React, { useState } from 'react';
import {
  Plus,
  Search,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Moon,
  Sun,
  PanelLeftClose,
  PanelLeft,
  MessageSquare,
  ArrowUpRight,
  CheckCircle2,
  FileSpreadsheet,
  FileText,
} from 'lucide-react';
import { ActiveView, ExpertMetadata } from '../types';

interface SidebarProps {
  activeView: ActiveView;
  setActiveView: (view: ActiveView) => void;
  onNewChat: () => void;
  experts: ExpertMetadata[];
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  onOpenExpertInExplorer: (filename: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  setActiveView,
  onNewChat,
  experts,
  darkMode,
  setDarkMode,
  onOpenExpertInExplorer,
}) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [deepDiveOpen, setDeepDiveOpen] = useState<boolean>(true);
  const [chatHistoryOpen, setChatHistoryOpen] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const chatHistory = [
    { id: '1', title: 'Adoption barriers across markets' },
    { id: '2', title: 'Reimbursement rules in France' },
    { id: '3', title: 'Surgeon training & utilization ROI' },
  ];

  const filteredHistory = chatHistory.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <aside
      className={`h-screen flex flex-col justify-between border-r border-slate-200/80 dark:border-slate-800/80 bg-[#F8F9FC] dark:bg-[#0B0F19] transition-all duration-300 flex-shrink-0 select-none z-30 ${
        isCollapsed ? 'w-16' : 'w-72'
      }`}
    >
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header / Brand + Collapse Button */}
        <div
          className={`border-b border-slate-200/60 dark:border-slate-800/60 transition-all ${
            isCollapsed
              ? 'py-3 px-2 flex flex-col items-center gap-2'
              : 'p-4 flex items-center justify-between'
          }`}
        >
          <div className="flex items-center space-x-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white text-xs shadow-md shadow-blue-600/25 flex-shrink-0">
              IQ
            </div>
            {!isCollapsed && (
              <div className="truncate">
                <h1 className="font-bold text-sm tracking-tight text-slate-800 dark:text-slate-100">
                  TranscriptIQ
                </h1>
                <span className="text-[10px] text-slate-400 dark:text-slate-400 font-medium block">
                  AI-Powered Evidence & Expert Insight
                </span>
              </div>
            )}
          </div>

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-800 transition"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <PanelLeft className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
          </button>
        </div>

        {/* Scrollable Navigation Area */}
        <div
          className={`flex-1 overflow-y-auto space-y-3 ${
            isCollapsed ? 'p-2 flex flex-col items-center' : 'p-3'
          }`}
        >
          {/* 1. Top-Level Pill Button: Search */}
          {!isCollapsed ? (
            <div className="w-full rounded-2xl bg-white dark:bg-slate-850/90 border border-slate-200/80 dark:border-slate-800/80 px-3.5 py-2.5 shadow-sm flex items-center gap-2.5 transition focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-400">
              <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search..."
                className="w-full bg-transparent text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none"
              />
            </div>
          ) : (
            <button
              onClick={() => setIsCollapsed(false)}
              className="w-10 h-10 rounded-2xl bg-white dark:bg-slate-850 border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-center justify-center text-slate-500 hover:text-blue-600 hover:border-blue-300 transition"
              title="Search"
            >
              <Search className="w-4 h-4" />
            </button>
          )}

          {/* 2. Top-Level Pill Button: "New Chat" (Solid-Fill Accent Prominent Button) */}
          <button
            onClick={onNewChat}
            className={`rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-md shadow-blue-500/25 transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center ${
              isCollapsed ? 'w-10 h-10 p-0' : 'w-full py-3 px-4 gap-2.5'
            }`}
            title="Start fresh chat"
          >
            <Plus className="w-4 h-4 flex-shrink-0" />
            {!isCollapsed && <span>New Chat</span>}
          </button>

          {/* 3. Top-Level Pill Button: Grounded Chat */}
          <button
            onClick={() => setActiveView('chat')}
            className={`rounded-2xl border transition-all shadow-xs flex items-center ${
              isCollapsed ? 'w-10 h-10 p-0 justify-center' : 'w-full py-3 px-4 justify-between'
            } ${
              activeView === 'chat'
                ? 'bg-blue-50/90 dark:bg-blue-950/60 border-blue-400/80 dark:border-blue-600/80 text-blue-700 dark:text-blue-300 font-semibold ring-2 ring-blue-500/10'
                : 'bg-white dark:bg-slate-850/80 border-slate-200/80 dark:border-slate-800/80 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
            }`}
            title="Grounded Chat"
          >
            <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'}`}>
              <MessageSquare className="w-4 h-4 text-blue-500 flex-shrink-0" />
              {!isCollapsed && <span className="text-xs">Grounded Chat</span>}
            </div>
            {!isCollapsed && activeView === 'chat' && (
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            )}
          </button>

          {/* 4. Top-Level Pill Button: Library */}
          <button
            onClick={() => setActiveView('library')}
            className={`rounded-2xl border transition-all shadow-xs flex items-center ${
              isCollapsed ? 'w-10 h-10 p-0 justify-center' : 'w-full py-3 px-4 justify-between'
            } ${
              activeView === 'library'
                ? 'bg-indigo-50/90 dark:bg-indigo-950/60 border-indigo-400/80 dark:border-indigo-600/80 text-indigo-700 dark:text-indigo-300 font-semibold ring-2 ring-indigo-500/10'
                : 'bg-white dark:bg-slate-850/80 border-slate-200/80 dark:border-slate-800/80 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
            }`}
            title="Transcript Library"
          >
            <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'}`}>
              <BookOpen className="w-4 h-4 text-indigo-500 flex-shrink-0" />
              {!isCollapsed && <span className="text-xs">Library</span>}
            </div>
            {!isCollapsed && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 font-semibold">
                {experts.length}
              </span>
            )}
          </button>

          {/* 5. Top-Level Pill Button: Deep Dive Analysis (Parent Pill + Nested Indented Rows) */}
          <div className="w-full space-y-1.5">
            <button
              onClick={() => {
                if (isCollapsed) {
                  setIsCollapsed(false);
                  setDeepDiveOpen(true);
                } else {
                  setDeepDiveOpen(!deepDiveOpen);
                }
              }}
              className={`rounded-2xl border transition-all shadow-xs flex items-center ${
                isCollapsed ? 'w-10 h-10 p-0 justify-center mx-auto' : 'w-full py-3 px-4 justify-between'
              } ${
                activeView === 'guide' || activeView === 'synthesis' || activeView === 'explorer' || activeView === 'hub'
                  ? 'bg-purple-50/90 dark:bg-purple-950/60 border-purple-400/80 dark:border-purple-600/80 text-purple-700 dark:text-purple-300 font-semibold ring-2 ring-purple-500/10'
                  : 'bg-white dark:bg-slate-850/80 border-slate-200/80 dark:border-slate-800/80 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
              }`}
              title="Deep Dive Analysis"
            >
              <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'}`}>
                <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0" />
                {!isCollapsed && <span className="text-xs">Deep Dive Analysis</span>}
              </div>
              {!isCollapsed && (
                <div className="text-slate-400">
                  {deepDiveOpen ? (
                    <ChevronDown className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5" />
                  )}
                </div>
              )}
            </button>

            {/* Nested Sub-Items (Plain Indented Rows with Small Arrow Icon) */}
            {!isCollapsed && deepDiveOpen && (
              <div className="ml-4 pl-3 border-l-2 border-slate-200/80 dark:border-slate-800 space-y-1 pt-1">
                {/* Child 1: Interview Matrix */}
                <button
                  onClick={() => setActiveView('guide')}
                  className={`w-full flex items-center justify-between py-1.5 px-2 rounded-lg text-xs transition group ${
                    activeView === 'guide'
                      ? 'text-purple-700 dark:text-purple-300 font-semibold bg-purple-50/60 dark:bg-purple-950/40'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/50 dark:hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <FileSpreadsheet className="w-3.5 h-3.5 text-teal-500" />
                    <span>Interview Matrix</span>
                  </div>
                  <ArrowUpRight className="w-3 h-3 text-slate-400 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                </button>

                {/* Child 2: Themes & Disagreements */}
                <button
                  onClick={() => setActiveView('synthesis')}
                  className={`w-full flex items-center justify-between py-1.5 px-2 rounded-lg text-xs transition group ${
                    activeView === 'synthesis'
                      ? 'text-purple-700 dark:text-purple-300 font-semibold bg-purple-50/60 dark:bg-purple-950/40'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/50 dark:hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                    <span>Themes & Disagreements</span>
                  </div>
                  <ArrowUpRight className="w-3 h-3 text-slate-400 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                </button>

                {/* Child 3: Transcript Explorer */}
                <button
                  onClick={() => setActiveView('explorer')}
                  className={`w-full flex items-center justify-between py-1.5 px-2 rounded-lg text-xs transition group ${
                    activeView === 'explorer'
                      ? 'text-purple-700 dark:text-purple-300 font-semibold bg-purple-50/60 dark:bg-purple-950/40'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/50 dark:hover:bg-slate-800/40'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-blue-500" />
                    <span>Transcript Explorer</span>
                  </div>
                  <ArrowUpRight className="w-3 h-3 text-slate-400 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                </button>
              </div>
            )}
          </div>

          {/* 6. Chat History / Recent Conversations Section */}
          {!isCollapsed && (
            <div className="pt-4 border-t border-slate-200/80 dark:border-slate-800/80 mt-4 w-full">
              <button
                onClick={() => setChatHistoryOpen(!chatHistoryOpen)}
                className="w-full flex items-center justify-between text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-2 py-1.5 hover:text-slate-600 dark:hover:text-slate-300 transition"
              >
                <span>Recent Conversations</span>
                {chatHistoryOpen ? (
                  <ChevronDown className="w-3 h-3" />
                ) : (
                  <ChevronRight className="w-3 h-3" />
                )}
              </button>

              {chatHistoryOpen && (
                <div className="space-y-1 mt-1">
                  {filteredHistory.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setActiveView('chat')}
                      className="w-full flex items-center justify-between py-2 px-2.5 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/50 dark:hover:bg-slate-800/50 rounded-xl group transition-all"
                    >
                      <span className="truncate pr-2">{item.title}</span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 opacity-50 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all flex-shrink-0" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer: Light/Dark Mode + Grounding Status */}
      <div className="p-3 border-t border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between">
        {!isCollapsed && (
          <div className="flex items-center space-x-1.5 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Strict Grounding</span>
          </div>
        )}

        <button
          onClick={() => setDarkMode(!darkMode)}
          className={`p-2 rounded-full text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-200/60 dark:hover:bg-slate-800 transition ${
            isCollapsed ? 'mx-auto' : ''
          }`}
          title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {darkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;

import React from 'react';
import { ShieldCheck, Zap, Layers, Sparkles, ArrowUpRight } from 'lucide-react';

interface WelcomeScreenProps {
  onSelectPrompt: (prompt: string) => void;
}

const EXAMPLE_PROMPTS = [
  {
    title: 'Real-Time Streaming Architecture',
    prompt: 'Explain how Server-Sent Events (SSE) stream tokens from FastAPI to React.',
    tag: 'Architecture',
  },
  {
    title: 'PostgreSQL & Database Design',
    prompt: 'Show the PostgreSQL schema design for multi-tenant chat conversations and messages.',
    tag: 'Database',
  },
  {
    title: 'Security & IDOR Prevention',
    prompt: 'How does NexaAI protect against IDOR and protect API keys on the server?',
    tag: 'Security',
  },
  {
    title: 'Markdown & Code Formatting',
    prompt: 'Show me an example with TypeScript code blocks, a markdown table, and bullet points.',
    tag: 'UI Demo',
  },
];

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onSelectPrompt }) => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-4xl mx-auto w-full my-auto text-center select-none">
      {/* Brand Icon */}
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-teal-600 to-teal-400 text-white flex items-center justify-center shadow-lg shadow-teal-500/25 mb-6 ring-4 ring-teal-500/10">
        <Sparkles className="w-8 h-8" />
      </div>

      {/* Main Heading */}
      <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-2">
        NexaAI
      </h1>
      <p className="text-base md:text-lg text-slate-600 dark:text-slate-400 max-w-lg mb-8 leading-relaxed">
        Production-minded, secure AI assistant engineered for real-time streaming and modern LLM orchestration.
      </p>

      {/* Architecture Highlights Pill Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full mb-10 text-left">
        <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm flex items-start gap-3">
          <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-semibold text-slate-900 dark:text-slate-200">
              Zero Key Exposure
            </h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
              Backend-only credential isolation & IDOR ownership validation.
            </p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm flex items-start gap-3">
          <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-semibold text-slate-900 dark:text-slate-200">
              Live Token Streaming
            </h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
              Low-latency SSE chunking with client-side cancellation.
            </p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 shadow-sm flex items-start gap-3">
          <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-semibold text-slate-900 dark:text-slate-200">
              Modular Architecture
            </h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
              Provider adapters for Gemini, OpenAI, & Anthropic.
            </p>
          </div>
        </div>
      </div>

      {/* Suggested Prompt Cards */}
      <div className="w-full">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-left mb-3">
          Try an example prompt (Phase 1 Mock Simulation)
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
          {EXAMPLE_PROMPTS.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectPrompt(item.prompt)}
              className="group p-4 rounded-xl bg-white dark:bg-slate-900/80 hover:bg-slate-50 dark:hover:bg-slate-850 border border-slate-200 dark:border-slate-800 hover:border-teal-500/50 dark:hover:border-teal-500/50 transition-all text-left shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between w-full mb-1">
                  <span className="text-[11px] font-semibold text-teal-600 dark:text-teal-400">
                    {item.tag}
                  </span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-500 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </div>
                <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100 mb-1">
                  {item.title}
                </h3>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {item.prompt}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

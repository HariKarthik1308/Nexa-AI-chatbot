import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Square } from 'lucide-react';

interface ComposerProps {
  onSendMessage: (text: string) => void;
  onStopGeneration: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export const Composer: React.FC<ComposerProps> = ({
  onSendMessage,
  onStopGeneration,
  isStreaming,
  disabled = false,
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isStreaming || disabled) return;
    onSendMessage(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full bg-gradient-to-t from-slate-50 via-slate-50 to-transparent dark:from-slate-950 dark:via-slate-950 dark:to-transparent pt-4 pb-4 px-4 md:px-6">
      <div className="max-w-4xl mx-auto">
        <form
          onSubmit={handleSubmit}
          className="relative rounded-2xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-lg shadow-slate-200/50 dark:shadow-none focus-within:border-teal-500 dark:focus-within:border-teal-500 focus-within:ring-2 focus-within:ring-teal-500/20 transition-all"
        >
          <div className="flex items-end gap-2 p-3">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              placeholder="Ask NexaAI anything... (Shift+Enter for newline)"
              className="w-full resize-none bg-transparent text-sm md:text-base text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none max-h-48 leading-relaxed py-1 px-2"
              aria-label="Chat input message"
            />

            <div className="flex items-center gap-1.5 flex-shrink-0">
              {isStreaming ? (
                <button
                  type="button"
                  onClick={onStopGeneration}
                  className="p-2 rounded-xl bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-200 transition-colors shadow-sm"
                  title="Stop generation"
                  aria-label="Stop generation"
                >
                  <Square className="w-4 h-4 fill-current" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim() || disabled}
                  className="p-2 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:bg-slate-200 dark:disabled:bg-slate-800 text-white disabled:text-slate-400 dark:disabled:text-slate-600 transition-colors shadow-sm disabled:cursor-not-allowed"
                  title="Send message"
                  aria-label="Send message"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </form>

        <p className="mt-2 text-center text-[11px] text-slate-400 dark:text-slate-500">
          NexaAI Prototype (Phase 1 Mock Mode) • Simulated inference • Real LLM and backend connected in Phases 2–4.
        </p>
      </div>
    </div>
  );
};

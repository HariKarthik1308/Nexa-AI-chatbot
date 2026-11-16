import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Bot,
  User,
  Copy,
  Check,
  RotateCw,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  AlertCircle,
  Square,
} from 'lucide-react';
import { Message } from '../../types/chat';
import { CodeBlock } from './CodeBlock';

interface MessageBubbleProps {
  message: Message;
  isLatestAssistant?: boolean;
  isStreaming?: boolean;
  onRegenerate?: (messageId: string) => void;
  onFeedback?: (messageId: string, rating: 'up' | 'down') => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isLatestAssistant,
  isStreaming,
  onRegenerate,
  onFeedback,
}) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div
      className={`group w-full py-5 px-4 md:px-6 transition-colors ${
        isUser
          ? 'bg-transparent'
          : 'bg-slate-100/60 dark:bg-slate-900/40 border-y border-slate-200/50 dark:border-slate-800/40'
      }`}
    >
      <div className="max-w-4xl mx-auto flex gap-4 md:gap-5">
        {/* Avatar */}
        <div className="flex-shrink-0 pt-0.5">
          {isUser ? (
            <div className="w-8 h-8 rounded-lg bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-slate-700 dark:text-slate-300 font-medium text-xs shadow-sm ring-1 ring-slate-300 dark:ring-slate-700">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center shadow-sm shadow-teal-500/20 ring-1 ring-teal-500/50">
              <Bot className="w-4 h-4" />
            </div>
          )}
        </div>

        {/* Content Container */}
        <div className="flex-1 min-w-0 space-y-2">
          {/* Header Info */}
          <div className="flex items-center gap-2 text-xs">
            <span className="font-semibold text-slate-900 dark:text-slate-100">
              {isUser ? 'You' : 'NexaAI'}
            </span>

            {!isUser && message.modelName && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-medium bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                <Sparkles className="w-2.5 h-2.5" />
                {message.modelName}
              </span>
            )}

            <span className="text-slate-400 text-[11px]">
              {formatTime(message.createdAt)}
            </span>

            {/* Status Indicators */}
            {message.status === 'streaming' && (
              <span className="flex items-center gap-1 text-[11px] text-teal-600 dark:text-teal-400 font-medium animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                Generating...
              </span>
            )}

            {message.status === 'partial' && (
              <span className="flex items-center gap-1 text-[11px] text-amber-600 dark:text-amber-400 font-medium">
                <Square className="w-2.5 h-2.5 fill-current" />
                Stopped by user
              </span>
            )}

            {message.status === 'error' && (
              <span className="flex items-center gap-1 text-[11px] text-rose-600 dark:text-rose-400 font-medium">
                <AlertCircle className="w-2.5 h-2.5" />
                Generation failed
              </span>
            )}
          </div>

          {/* Message Body */}
          <div className="prose prose-slate dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 text-sm md:text-base leading-relaxed break-words">
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      const codeString = String(children).replace(/\n$/, '');
                      const isInline = !match && !codeString.includes('\n');

                      if (isInline) {
                        return (
                          <code
                            className="bg-slate-200/80 dark:bg-slate-800 px-1.5 py-0.5 rounded text-xs font-mono text-teal-700 dark:text-teal-300"
                            {...props}
                          >
                            {children}
                          </code>
                        );
                      }

                      return (
                        <CodeBlock
                          language={match ? match[1] : ''}
                          code={codeString}
                        />
                      );
                    },
                    table({ children }) {
                      return (
                        <div className="my-4 overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm">
                          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-xs md:text-sm">
                            {children}
                          </table>
                        </div>
                      );
                    },
                    th({ children }) {
                      return (
                        <th className="px-3 py-2 bg-slate-100 dark:bg-slate-800 text-left font-semibold text-slate-900 dark:text-slate-100">
                          {children}
                        </th>
                      );
                    },
                    td({ children }) {
                      return (
                        <td className="px-3 py-2 border-t border-slate-200 dark:border-slate-800/60">
                          {children}
                        </td>
                      );
                    },
                    blockquote({ children }) {
                      return (
                        <blockquote className="border-l-4 border-teal-500 pl-4 my-3 text-slate-600 dark:text-slate-400 italic">
                          {children}
                        </blockquote>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>

                {message.status === 'streaming' && (
                  <span className="inline-block w-2 h-4 ml-1 bg-teal-500 animate-pulse align-middle" />
                )}
              </>
            )}
          </div>

          {/* Action Toolbar on Assistant Messages */}
          {!isUser && message.content && (
            <div className="flex items-center gap-1 pt-1 opacity-80 group-hover:opacity-100 transition-opacity text-slate-500 dark:text-slate-400">
              <button
                type="button"
                onClick={handleCopy}
                className="p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
                title="Copy message"
                aria-label="Copy message"
              >
                {copied ? (
                  <Check className="w-3.5 h-3.5 text-teal-500" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>

              {onRegenerate && (
                <button
                  type="button"
                  onClick={() => onRegenerate(message.id)}
                  disabled={isStreaming}
                  className="p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  title="Regenerate response"
                  aria-label="Regenerate response"
                >
                  <RotateCw
                    className={`w-3.5 h-3.5 ${
                      isStreaming && isLatestAssistant ? 'animate-spin' : ''
                    }`}
                  />
                </button>
              )}

              {onFeedback && (
                <>
                  <button
                    type="button"
                    onClick={() => onFeedback(message.id, 'up')}
                    className={`p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors ${
                      message.feedback === 'up'
                        ? 'text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/50'
                        : 'hover:text-slate-900 dark:hover:text-slate-100'
                    }`}
                    title="Good response"
                    aria-label="Thumbs up"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                  </button>

                  <button
                    type="button"
                    onClick={() => onFeedback(message.id, 'down')}
                    className={`p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors ${
                      message.feedback === 'down'
                        ? 'text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/50'
                        : 'hover:text-slate-900 dark:hover:text-slate-100'
                    }`}
                    title="Poor response"
                    aria-label="Thumbs down"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

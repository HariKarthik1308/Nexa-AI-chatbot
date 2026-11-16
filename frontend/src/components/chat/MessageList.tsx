import React, { useEffect, useRef } from 'react';
import { Message } from '../../types/chat';
import { MessageBubble } from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  onRegenerate: (messageId: string) => void;
  onFeedback: (messageId: string, rating: 'up' | 'down') => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isStreaming,
  onRegenerate,
  onFeedback,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll when messages update or stream
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const lastAssistantIndex = [...messages]
    .map((m, idx) => ({ role: m.role, idx }))
    .reverse()
    .find((m) => m.role === 'assistant')?.idx;

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.map((message, idx) => (
        <MessageBubble
          key={message.id}
          message={message}
          isLatestAssistant={idx === lastAssistantIndex}
          isStreaming={isStreaming && message.status === 'streaming'}
          onRegenerate={onRegenerate}
          onFeedback={onFeedback}
        />
      ))}
      <div ref={bottomRef} className="h-4" />
    </div>
  );
};

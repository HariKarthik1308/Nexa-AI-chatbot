import React from 'react';
import { Message } from '../../types/chat';
import { WelcomeScreen } from './WelcomeScreen';
import { MessageList } from './MessageList';
import { Composer } from './Composer';

interface ChatAreaProps {
  messages: Message[];
  isStreaming: boolean;
  onSendMessage: (text: string) => void;
  onStopGeneration: () => void;
  onRegenerate: (messageId: string) => void;
  onFeedback: (messageId: string, rating: 'up' | 'down') => void;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  isStreaming,
  onSendMessage,
  onStopGeneration,
  onRegenerate,
  onFeedback,
}) => {
  return (
    <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-50 dark:bg-slate-950">
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col overflow-y-auto">
          <WelcomeScreen onSelectPrompt={onSendMessage} />
        </div>
      ) : (
        <MessageList
          messages={messages}
          isStreaming={isStreaming}
          onRegenerate={onRegenerate}
          onFeedback={onFeedback}
        />
      )}

      <Composer
        onSendMessage={onSendMessage}
        onStopGeneration={onStopGeneration}
        isStreaming={isStreaming}
      />
    </main>
  );
};

export type MessageRole = 'user' | 'assistant' | 'system';

export type MessageStatus = 'complete' | 'streaming' | 'partial' | 'error';

export interface Message {
  id: string;
  conversationId: string;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  modelProvider?: string;
  modelName?: string;
  createdAt: string;
  feedback?: 'up' | 'down' | null;
  error?: string;
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  lastMessagePreview?: string;
}

export interface ModelOption {
  id: string;
  name: string;
  provider: 'Gemini' | 'OpenAI' | 'Anthropic' | 'Mock';
  description: string;
  isDefault?: boolean;
}

export interface StreamEvent {
  type: 'message_start' | 'content_delta' | 'message_complete' | 'usage' | 'error';
  delta?: string;
  messageId?: string;
  usage?: {
    inputTokens: number;
    outputTokens: number;
  };
  error?: string;
}

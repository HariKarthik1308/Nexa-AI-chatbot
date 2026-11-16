import { Conversation, Message, ModelOption } from '../types/chat';

export const AVAILABLE_MODELS: ModelOption[] = [
  {
    id: 'mock-gemini-1.5-flash',
    name: 'Gemini 1.5 Flash (Simulated)',
    provider: 'Gemini',
    description: 'Fast, lightweight mock inference for Phase 1 UI validation',
    isDefault: true,
  },
  {
    id: 'mock-gpt-4o-mini',
    name: 'GPT-4o Mini (Simulated)',
    provider: 'OpenAI',
    description: 'Balanced response preview for Phase 1 UI validation',
  },
  {
    id: 'mock-claude-3-haiku',
    name: 'Claude 3 Haiku (Simulated)',
    provider: 'Anthropic',
    description: 'Concise response preview for Phase 1 UI validation',
  },
];

export const INITIAL_CONVERSATIONS: Conversation[] = [
  {
    id: 'conv-1',
    title: 'Project Architecture & Tech Stack',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    lastMessagePreview: 'Welcome to NexaAI. Here is an overview of our architecture...',
  },
  {
    id: 'conv-2',
    title: 'Security & Auth Blueprint',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    lastMessagePreview: 'Argon2id password hashing and HttpOnly session cookies...',
  },
];

export const INITIAL_MESSAGES: Record<string, Message[]> = {
  'conv-1': [
    {
      id: 'msg-1-1',
      conversationId: 'conv-1',
      role: 'user',
      content: 'Can you summarize the architecture of NexaAI?',
      status: 'complete',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    },
    {
      id: 'msg-1-2',
      conversationId: 'conv-1',
      role: 'assistant',
      content: `### NexaAI System Architecture

NexaAI is built with a security-first, production-oriented architecture:

- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite.
- **Backend API**: Python FastAPI with Server-Sent Events (SSE) for token streaming.
- **Data Layer**: PostgreSQL with SQLAlchemy ORM and Alembic migrations.
- **Cache & Rate Limits**: Redis for IP and per-user request throttling.
- **Model Orchestration**: Modular provider adapters (Gemini, OpenAI, Anthropic).

\`\`\`python
# Example FastAPI Streaming Endpoint Blueprint
@router.post("/chats/{chat_id}/messages/stream")
async def stream_chat_message(
    chat_id: str,
    payload: MessageCreateRequest,
    current_user: User = Depends(get_current_user)
):
    # Verify ownership before invoking LLM
    await conversation_service.verify_ownership(chat_id, current_user.id)
    return EventSourceResponse(chat_service.stream_response(chat_id, payload))
\`\`\`

> **Note:** Currently running in **Phase 1 Mock Mode**. Real backend and provider adapters are wired in Phases 2-4.`,
      status: 'complete',
      modelProvider: 'Gemini',
      modelName: 'Gemini 1.5 Flash (Simulated)',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2 + 5000).toISOString(),
      feedback: 'up',
    },
  ],
  'conv-2': [
    {
      id: 'msg-2-1',
      conversationId: 'conv-2',
      role: 'user',
      content: 'What are the core security principles we are enforcing?',
      status: 'complete',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    },
    {
      id: 'msg-2-2',
      conversationId: 'conv-2',
      role: 'assistant',
      content: `### Mandatory Security Controls

1. **Zero Key Exposure**: Provider API keys stay strictly on the server in \`.env\`.
2. **Object-Level Authorization**: Prevents IDOR by validating user ownership on every conversation.
3. **Argon2id Password Hashing**: Protection against brute-force and credential stuffing.
4. **Input & Prompt Sanitization**: Content treated as untrusted; Markdown sanitized against XSS.`,
      status: 'complete',
      modelProvider: 'Gemini',
      modelName: 'Gemini 1.5 Flash (Simulated)',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 + 4000).toISOString(),
    },
  ],
};

const SAMPLE_RESPONSES = [
  `### Understanding Real-Time Token Streaming

Streaming responses in modern conversational AI rely on protocols like **Server-Sent Events (SSE)** or HTTP chunked transfer:

1. **Client Dispatches Request**: User submits prompt via \`POST /stream\`.
2. **Backend Validates & Authorizes**: Checks session, quota, and rate limits.
3. **LLM Provider Yields Chunks**: Model outputs deltas as tokens are generated.
4. **SSE Forwards Chunks**: The browser receives individual tokens and renders them immediately.

\`\`\`typescript
// Frontend SSE consumer pattern
const response = await fetch('/api/v1/chats/stream', { ... });
const reader = response.body?.getReader();
// Decodes chunks progressively
\`\`\`

*(Phase 1 Mock Mode: Simulated streaming response successfully demonstrated).*`,

  `Here is a clean breakdown of how to structure database models for multi-tenant chat conversations:

| Table | Primary Key | Key Foreign Keys | Purpose |
| :--- | :--- | :--- | :--- |
| **users** | \`id\` (UUID) | None | Authenticated user profiles & hashed credentials |
| **conversations** | \`id\` (UUID) | \`user_id\` -> users.id | Chat threads owned by users |
| **messages** | \`id\` (UUID) | \`conversation_id\` -> conversations.id | Ordered dialog history with role & token counts |
| **usage_records** | \`id\` (UUID) | \`user_id\` -> users.id | Token tracking and billing audit log |

Every database query in FastAPI will verify \`conversation.user_id == current_user.id\` to eliminate Insecure Direct Object Reference (IDOR) vulnerabilities.`,

  `### Code Sample: React + TypeScript Hook for Chat Streaming

Here is an architectural pattern for managing abortable streaming chat state:

\`\`\`tsx
import { useState, useRef } from 'react';

export function useChatStream() {
  const [isGenerating, setIsGenerating] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsGenerating(false);
    }
  };

  return { isGenerating, stopGeneration };
}
\`\`\`

This provides snappy, user-controlled interruption when the answer has provided enough context.`,
];

/**
 * Simulates real-time token streaming with cancellation support.
 */
export async function* streamMockResponse(
  prompt: string,
  model: ModelOption,
  signal?: AbortSignal
): AsyncGenerator<string, void, unknown> {
  // Pick an informative response based on query or rotation
  let template = SAMPLE_RESPONSES[Math.floor(Math.random() * SAMPLE_RESPONSES.length)];
  
  if (prompt.toLowerCase().includes('hello') || prompt.toLowerCase().includes('hi')) {
    template = `Hello! I am **NexaAI**, simulating **${model.name}**. 

Currently, the interface is running in **Phase 1: UI Foundation & Mock Mode**. 
You can test:
- Responsive desktop and mobile drawer navigation
- Token-by-token simulated streaming
- Stopping generation in-flight
- Markdown rendering, code highlighting, and copy controls
- Dark and light theme switching

How can I help you explore the system?`;
  }

  // Break text into words/tokens for streaming
  const tokens = template.split(/(\s+)/);

  for (const token of tokens) {
    if (signal?.aborted) {
      return;
    }
    // Realistic variable typing delay (15-35ms)
    await new Promise((resolve) => setTimeout(resolve, Math.floor(Math.random() * 20) + 15));
    if (signal?.aborted) {
      return;
    }
    yield token;
  }
}

import { Conversation, Message, ModelOption } from '../types/chat';

export const AVAILABLE_MODELS: ModelOption[] = [
  {
    id: 'gemini-1.5-flash',
    name: 'Gemini 1.5 Flash (Fast)',
    provider: 'Gemini',
    description: 'High-speed multimodal inference via FastAPI backend',
    isDefault: true,
  },
  {
    id: 'gemini-2.0-flash',
    name: 'Gemini 2.0 Flash (Next-Gen)',
    provider: 'Gemini',
    description: 'Google GenAI real-time reasoning model',
  },
  {
    id: 'gpt-4o-mini',
    name: 'GPT-4o Mini',
    provider: 'OpenAI',
    description: 'Cost-efficient intelligence via backend adapter',
  },
  {
    id: 'mock-gemini-1.5-flash',
    name: 'Gemini (Offline Mock)',
    provider: 'Mock',
    description: 'Simulated tokens for offline testing',
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
    return StreamingResponse(
        chat_service.stream_message(chat_id, current_user.id, payload.content),
        media_type="text/event-stream"
    )
\`\`\`

> **Phase 4:** Live Server-Sent Events (SSE) token streaming connected between FastAPI and React!`,
      status: 'complete',
      modelProvider: 'Gemini',
      modelName: 'Gemini 1.5 Flash',
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
      modelName: 'Gemini 1.5 Flash',
      createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 + 4000).toISOString(),
    },
  ],
};

const SAMPLE_RESPONSES = [
  `### Understanding Real-Time Token Streaming

Streaming responses in modern conversational AI rely on protocols like **Server-Sent Events (SSE)** or HTTP chunked transfer:

1. **Client Dispatches Request**: User submits prompt via \`POST /api/v1/chats/{id}/messages/stream\`.
2. **Backend Validates & Authorizes**: Checks session, quota, and rate limits.
3. **LLM Provider Yields Chunks**: Model outputs deltas as tokens are generated.
4. **SSE Forwards Chunks**: The browser receives individual tokens and renders them immediately.

\`\`\`typescript
// Frontend SSE consumer pattern
const response = await fetch('/api/v1/chats/' + id + '/messages/stream', { ... });
const reader = response.body?.getReader();
// Decodes chunks progressively
\`\`\`

*(Simulated streaming response successfully demonstrated).*`,
];

/**
 * Simulates real-time token streaming with cancellation support.
 */
export async function* streamMockResponse(
  prompt: string,
  model: ModelOption,
  signal?: AbortSignal
): AsyncGenerator<string, void, unknown> {
  let template = SAMPLE_RESPONSES[Math.floor(Math.random() * SAMPLE_RESPONSES.length)];
  
  if (prompt.toLowerCase().includes('hello') || prompt.toLowerCase().includes('hi')) {
    template = `Hello! I am **NexaAI**, simulating **${model.name}**. 

The application supports:
- Real-time Server-Sent Events (SSE) streaming from FastAPI
- Client-side in-flight generation cancellation (Stop Generation)
- Conversation history persistence and search
- Markdown rendering, code highlighting, and copy controls
- Dark and light theme switching

How can I help you today?`;
  }

  const tokens = template.split(/(\s+)/);

  for (const token of tokens) {
    if (signal?.aborted) return;
    await new Promise((resolve) => setTimeout(resolve, Math.floor(Math.random() * 20) + 15));
    if (signal?.aborted) return;
    yield token;
  }
}

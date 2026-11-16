# NexaAI — Architecture Overview

## 1. System Vision

NexaAI is a full-stack, production-minded AI assistant designed with a secure backend architecture, real-time token streaming, multi-model support, and structured conversation persistence.

```
┌──────────────────────────────────────────────┐
│                React Frontend                │
│ Chat UI • Auth UI • History • Streaming UI   │
└───────────────────────┬──────────────────────┘
                        │ HTTPS / SSE
                        ▼
┌──────────────────────────────────────────────┐
│                FastAPI Backend               │
│ Auth • Validation • Rate Limits • Chat API   │
│ Conversation Service • Provider Orchestrator │
│ Safety Checks • Usage Tracking • Audit Logs  │
└───────────────┬──────────────────┬───────────┘
                │                  │
                ▼                  ▼
┌────────────────────────┐  ┌──────────────────┐
│      PostgreSQL        │  │   LLM Provider   │
│ Users • Chats • Messages│  │ Gemini / OpenAI  │
│ Usage • Feedback        │  │ / Anthropic      │
└────────────────────────┘  └──────────────────┘
                │
                ▼
        ┌──────────────┐
        │    Redis     │
        │ Rate limits  │
        │ Short-lived  │
        │ coordination │
        └──────────────┘
```

## 2. Core Modules

### Frontend (React 18 + TypeScript + Vite + Tailwind CSS)
- **`src/components/chat/`**: Message list, markdown rendering with safe syntax highlighting, code snippet copy, auto-resizing composer with stop generation.
- **`src/components/layout/`**: Collapsible sidebar with conversation search, model switcher, theme toggle (dark/light).
- **`src/hooks/`**: Abortable stream management (`useChat`), theme state (`useTheme`).
- **`src/services/`**: Mock streaming generator (Phase 1) transitioning to Server-Sent Events (SSE) consumer in Phase 4.

### Backend (Python + FastAPI — Planned Phase 2+)
- **`app/api/`**: Authentication, conversation management, message streaming endpoints.
- **`app/services/`**: Conversation authorization, rate limiting, and provider orchestration.
- **`app/llm/`**: Modular LLM adapters for Google Gemini, OpenAI, and Anthropic.
- **`app/models/`**: SQLAlchemy models for `users`, `conversations`, `messages`, and `usage_records`.
- **`app/core/`**: Environment configuration, Argon2id password hashing, and logging with secret redaction.

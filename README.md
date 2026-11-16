# NexaAI — Secure Real-Time AI Assistant

A full-stack, responsive AI assistant with an original, polished chat experience, powered by real hosted Large Language Models (LLMs), with secure backend architecture, token-by-token streaming responses, persistent conversation history, and measurable answer quality.

---

## Current Status: Phase 1 (UI Foundation & Mock Mode)

Phase 1 delivers the responsive frontend shell, state management, and mock streaming service:
- [x] Responsive desktop and mobile drawer layout with original branding.
- [x] Auto-expanding composer with Enter to send and Shift+Enter for newline.
- [x] Real-time simulated token streaming with in-flight **Stop Generation** cancellation.
- [x] Full Markdown rendering with syntax-highlighted code blocks, tables, and copy controls.
- [x] Conversation management: New chat, search filtering, inline rename, and deletion.
- [x] Light / Dark mode toggle with preference persistence.
- [x] Clearly labeled Phase 1 Mock Mode indicators across the UI.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons |
| **Backend (Phase 2+)** | Python, FastAPI, Pydantic |
| **Database (Phase 2+)** | PostgreSQL, SQLAlchemy, Alembic |
| **LLM Provider (Phase 3+)** | Google Gemini API (with OpenAI / Anthropic modular adapters) |
| **Streaming (Phase 4+)** | Server-Sent Events (SSE) / HTTP Streaming |
| **Testing** | Vitest, React Testing Library, Pytest |

---

## Quick Start (Frontend UI)

### 1. Install dependencies
```bash
cd frontend
npm install
```

### 2. Run local development server
```bash
npm run dev
```

### 3. Run unit tests
```bash
npm test
```

### 4. Typecheck
```bash
npm run lint
```

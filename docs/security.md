# NexaAI — Security Architecture & Guidelines

## 1. Core Threat Model

NexaAI is designed to mitigate key LLM and API application vulnerabilities:
- **API Key Leakage**: Exposure through client-side bundles, git commits, or verbose logging.
- **Insecure Direct Object Reference (IDOR)**: Malicious users reading or altering another user's chat sessions.
- **Cross-Site Scripting (XSS)**: Untrusted model or user markdown executing malicious scripts.
- **Prompt Injection**: User prompts attempting to override backend business rules or extract system instructions.
- **Denial of Service / Cost Depletion**: Unbounded API requests exhausting quotas and budgets.

## 2. Defensive Controls Implemented

### Credential Safety
- API keys reside solely in server environment variables loaded through Pydantic `BaseSettings`.
- `.gitignore` explicitly excludes `.env` and credential files.
- `.env.example` documents placeholders only.

### Ownership Checks
Every conversation endpoint verifies:
```python
if conversation.user_id != current_user.id:
    raise HTTPException(status_code=404, detail="Conversation not found")
```
*(404 returned instead of 403 to prevent conversation enumeration attacks).*

### Safe Content Rendering
- Frontend markdown rendering sanitizes raw HTML and prevents inline script execution.
- Syntax highlighting handles code snippets securely within isolated containers.

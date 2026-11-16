import logging
import re
from typing import List

# Patterns matching sensitive credentials
SECRET_PATTERNS: List[re.Pattern] = [
    re.compile(r"(AIzaSy[A-Za-z0-9_-]{33})", re.IGNORECASE),  # Google API key
    re.compile(r"(sk-[A-Za-z0-9]{20,})", re.IGNORECASE),      # OpenAI API key
    re.compile(r"Bearer\s+([A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_=]*)", re.IGNORECASE),  # JWT Token
    re.compile(r"password['\"]?\s*[:=]\s*['\"]?([^'\"\s,]+)", re.IGNORECASE),  # Passwords
]


class SecretRedactionFilter(logging.Filter):
    """Logging filter that automatically redacts API keys, credentials, and tokens."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact(str(arg)) for arg in record.args)
        return True

    @staticmethod
    def redact(text: str) -> str:
        for pattern in SECRET_PATTERNS:
            text = pattern.sub(r"[REDACTED_SECRET]", text)
        return text


def setup_secure_logging(log_level: str = "INFO"):
    """Configure secure root and application loggers with secret redaction."""
    logger = logging.getLogger("nexa_ai")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Add secret redaction filter to all handlers
    redaction_filter = SecretRedactionFilter()
    logger.addFilter(redaction_filter)

    for handler in logging.root.handlers:
        handler.addFilter(redaction_filter)

    return logger

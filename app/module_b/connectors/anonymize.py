"""Simple anonymization helpers for connector adapters.

This provides deterministic hashing of user IDs and conservative PII redaction.
"""
import re
import hashlib
import os
from typing import Optional

PII_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)
PII_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def anonymize_user_id(user_id: str, salt: Optional[str] = None) -> str:
    if user_id is None:
        return ""
    if salt is None:
        salt = os.environ.get("ANON_SALT", "dev-salt")
    h = hashlib.sha256((salt + str(user_id)).encode("utf-8")).hexdigest()
    return h


def redact_pii(text: Optional[str]) -> Optional[str]:
    if text is None:
        return text
    t = str(text)
    # redact emails
    t = PII_EMAIL_RE.sub("[REDACTED_EMAIL]", t)
    # redact SSN-like patterns
    t = PII_SSN_RE.sub("[REDACTED_SSN]", t)
    return t

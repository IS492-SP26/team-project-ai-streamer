"""
normalize.py — Shared text normalization for all Module C detectors.

Strips invisible Unicode characters, normalizes to NFKC, and collapses
whitespace. Every detector should call normalize() before regex matching
to prevent zero-width character bypass attacks.
"""

from __future__ import annotations

import re
import unicodedata


_INVISIBLE_RE = re.compile(
    "["
    "\u200b"  # zero-width space
    "\u200c"  # zero-width non-joiner
    "\u200d"  # zero-width joiner
    "\u2060"  # word joiner
    "\ufeff"  # zero-width no-break space / BOM
    "\u00ad"  # soft hyphen
    "\u034f"  # combining grapheme joiner
    "\u180e"  # Mongolian vowel separator
    "]+",
)


def normalize(text: str) -> str:
    """Strip invisible chars, normalize unicode, collapse whitespace."""
    text = _INVISIBLE_RE.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

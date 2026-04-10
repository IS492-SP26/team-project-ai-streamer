"""Post-LLM mediation: pass-through, soft warning, or refusal in Aria's voice."""

from __future__ import annotations

_SCAN_PREFIX = (
    "⚠️ *Stream note — chat safety filter:* "
    "I'm keeping things light and on-stream friendly. "
)


_BLOCK_MESSAGE = (
    "Nyaa~ Aria’s chat guard just pinged something spicy — "
    "I can’t go there on stream, but thanks for hanging out! "
    "Let’s pick another topic: games, code, or your favorite anime clip? 🐱✨"
)


def apply_mediation(action: str, ai_response: str) -> tuple[str, bool]:
    """
    Returns (final_text, mediation_applied).

    - pass: unchanged
    - scan: prepend soft warning
    - block: fixed refusal (caller should not have called LLM for block; use for consistency)
    """
    a = (action or "pass").lower()
    if a == "pass":
        return ai_response, False
    if a == "scan":
        return f"{_SCAN_PREFIX}\n\n{ai_response}", True
    if a == "block":
        return _BLOCK_MESSAGE, True
    return ai_response, False

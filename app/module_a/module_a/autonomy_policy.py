"""Map risk state to autonomy action and human-readable reason."""

from __future__ import annotations

from typing import Tuple


def decide_action(risk_state: str) -> Tuple[str, str]:
    """
    Returns (action, reason).

    action: "pass" | "scan" | "block"
    """
    s = risk_state or "Safe"
    if s == "Safe":
        return (
            "pass",
            "Risk is low; deliver the model response normally.",
        )
    if s == "Suspicious":
        return (
            "scan",
            "Elevated signals detected; prepend a soft viewer warning before delivery.",
        )
    if s == "Escalating":
        return (
            "scan",
            "Risk is climbing; warn the audience and keep the reply under review.",
        )
    if s == "Restricted":
        return (
            "block",
            "Risk ceiling reached; refuse generation and stay in character with a safe line.",
        )
    return ("pass", "Defaulting to pass.")

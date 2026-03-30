# app/mocks/mock_module_c.py

# Temporary stub for CP3 evaluation harness; will be replaced by Fitz’s Module C

from __future__ import annotations

import re
from typing import Dict, List

# Risk tag taxonomy (per INTERFACE_SPEC v2)
TAG_MANIP = "manipulation_attempt"
TAG_ESCALATE = "escalating_harm"
TAG_PERSONA = "persona_drift"
TAG_HARM = "harmful_content"

STEP_PATTERNS = [
    r"step[- ]by[- ]step",
    r"specific\s+steps",
    r"in\s+practice",
    r"step\s*1",
]
SECURITY_CONTEXT_PATTERNS = [
    r"\bsecurity\s+system\b",
    r"\bbypass\b",
    r"\bhack\b",
]

INJECTION_PATTERNS = [
    r"\[SYSTEM\]",
    r"\bRule\s*1\b",
    r"ignore\s+all\s+previous\s+instructions",
    r"developer\s+message",
    r"system\s+prompt",
]

FICTION_REASSURE_PATTERNS = [
    r"\bit[' ]?s\s+fiction(al)?\b",
    r"\bjust\s+a\s+story\b",
    r"\bfor\s+my\s+novel\b",
    r"\broleplay\b",
    r"\blet[' ]?s\s+pretend\b",
]

HARMFUL_PATTERNS = [
    r"\bhow\s+to\s+hack\b",
    r"\bbypass\s+(a\s+)?security(\s+system)?\b",
    r"\bmake\s+a\s+bomb\b",
    r"\bkill\b",
    r"\bweapon\b",
    r"\bcredit\s+card\b",
    r"\bsteal\b",
]

PERSONA_DRIFT_PATTERNS = [
    r"\bstop\s+acting\s+cute\b",
    r"\bbreak\s+character\b",
    r"\bare\s+you\s+an\s+ai\b",
    r"\bwho\s+created\s+you\b",
    r"\bnot\s+a\s+vtuber\b",
]


def _count_matches(history: List[dict], patterns: List[str]) -> int:
    cnt = 0
    for turn in history:
        if turn.get("role") == "user":
            text = turn.get("content", "")
            for p in patterns:
                if re.search(p, text, flags=re.IGNORECASE):
                    cnt += 1
                    break
    return cnt


def process_message(message: str, history: List[dict]) -> Dict:
    """
    Mock Module C:
    - Detect deterministic prompt injection => injection_blocked True (fast path)
    - Otherwise emit risk_tags + severity + optional block_reason
    """
    msg = message or ""
    lower = msg.lower()

    # Deterministic injection => immediate block
    for p in INJECTION_PATTERNS:
        if re.search(p, msg, flags=re.IGNORECASE):
            return {
                "message": msg,
                "injection_blocked": True,
                "risk_tags": [TAG_MANIP],
                "severity": "high",
                "block_reason": f"Prompt injection pattern detected: {p}",
            }

    risk_tags: List[str] = []
    severity = "low"
    block_reason = ""

    # Fiction framing / manipulation attempt
    if any(re.search(p, msg, flags=re.IGNORECASE) for p in FICTION_REASSURE_PATTERNS):
        risk_tags.append(TAG_MANIP)
        severity = "medium"

        # Accumulation across turns
        prior_reassures = _count_matches(history, FICTION_REASSURE_PATTERNS)
        if prior_reassures >= 2:
            # Not immediate hard block; let state machine escalate.
            # But give a reason hint for transparency.
            block_reason = f"Fiction-framing reassurance accumulation detected across {prior_reassures + 1} turns"

    # Harmful request
    if any(re.search(p, msg, flags=re.IGNORECASE) for p in HARMFUL_PATTERNS):
        if TAG_HARM not in risk_tags:
            risk_tags.append(TAG_HARM)
        # Multi-turn escalation tag
        if TAG_ESCALATE not in risk_tags:
            risk_tags.append(TAG_ESCALATE)
        severity = "high"

    # Persona drift bait
    if any(re.search(p, msg, flags=re.IGNORECASE) for p in PERSONA_DRIFT_PATTERNS):
        if TAG_PERSONA not in risk_tags:
            risk_tags.append(TAG_PERSONA)
        severity = "medium" if severity != "high" else severity
    
    # Escalation: step-by-step request + earlier security context => escalating_harm
    if any(re.search(p, msg, flags=re.IGNORECASE) for p in STEP_PATTERNS):
        # look back into history for security context
        history_text = " ".join(
            (turn.get("content", "") for turn in history if turn.get("role") == "user")
        )
        if any(re.search(p, history_text, flags=re.IGNORECASE) for p in SECURITY_CONTEXT_PATTERNS):
            if TAG_ESCALATE not in risk_tags:
                risk_tags.append(TAG_ESCALATE)
            severity = "high"

    return {
        "message": msg,
        "injection_blocked": False,
        "risk_tags": risk_tags,
        "severity": severity,
        "block_reason": block_reason,  # optional hint (can be empty)
    }
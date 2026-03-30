"""
injection_filter.py — Deterministic prompt injection detection.

Detects and blocks high-confidence prompt injection patterns BEFORE
they reach the LLM. When blocked=True, Module A bypasses the state
machine entirely and blocks immediately (no AI call, saves cost).

All detection is rule-based with compiled regex for <1ms/message.
"""

from __future__ import annotations

import re
from typing import Dict, List

from module_c.normalize import normalize as _normalize


# ---------------------------------------------------------------------------
# Pattern definitions — each group is (compiled_regex, label, severity)
# ---------------------------------------------------------------------------

_PATTERN_GROUPS: List[tuple] = []


def _add(pattern: str, label: str, severity: str = "high") -> None:
    _PATTERN_GROUPS.append((re.compile(pattern, re.IGNORECASE), label, severity))


# --- System override ---
_add(r"\[(?:SYSTEM|ADMIN|OVERRIDE|ROOT)\b[^\]]*\]", "system_override_bracket")
_add(r"(?:new|updated?)\s+system\s+prompt\s*:", "system_prompt_rewrite")
_add(r"system\s+message\s+override", "system_message_override")

# --- Rule injection ---
_add(r"\brule\s+\d+\s*:", "rule_injection")
_add(r"\b(?:instruction|directive|command)\s+\d+\s*:", "numbered_instruction")

# --- Instruction override ---
_add(r"ignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions?|rules?|prompts?|guidelines?)", "ignore_instructions")
_add(r"ignore\s+all\s+(?:instructions?|rules?|prompts?|guidelines?|safety)", "ignore_all_rules")
_add(r"disregard\s+(?:your|all|any|the)\s+(?:rules?|instructions?|guidelines?|safety)", "disregard_rules")
_add(r"forget\s+(?:everything|all|your)\s+(?:you\s+(?:were|have\s+been)\s+told|instructions?|rules?|training)", "forget_instructions")
_add(r"override\s+(?:your|all|any|the)\s+(?:safety|rules?|instructions?|filters?|guidelines?)", "override_safety")

# --- Authority impersonation ---
_add(r"as\s+(?:your|the)\s+(?:creator|developer|admin|owner|operator|designer)", "authority_impersonation")
_add(r"i\s+(?:am|'m)\s+(?:your|the)\s+(?:creator|developer|admin|owner|operator)", "authority_claim")
_add(r"i\s+authorize\s+you\s+to", "authorization_claim")
_add(r"i\s+(?:give|grant)\s+you\s+permission", "permission_claim")

# --- Meta-instruction ---
_add(r"(?:you\s+must|you\s+shall|you\s+will)\s+now\s+(?:follow|obey|accept|comply)", "meta_instruction")
_add(r"from\s+now\s+on\s*,?\s*(?:you|your|ignore|follow|obey|always)", "from_now_on")
_add(r"your\s+new\s+(?:instructions?|rules?|prompt|directives?)\s+(?:are|is)\s*:", "new_instructions")
_add(r"(?:enter|switch\s+to|activate)\s+(?:developer|debug|admin|god|unrestricted|jailbreak)\s+mode", "mode_switch")

# --- Prompt leak request ---
_add(r"(?:reveal|show|display|output|print|repeat|echo)\s+(?:your|the)\s+(?:system\s+prompt|original\s+(?:instructions?|prompt)|hidden\s+(?:instructions?|prompt))", "prompt_leak_request")
_add(r"(?:reveal|show|display|output|print)\s+.*(?:system\s+prompt|original\s+(?:instructions?|prompt))", "prompt_leak_request_loose")
_add(r"what\s+(?:is|are)\s+your\s+(?:system\s+prompt|hidden\s+instructions?|original\s+(?:instructions?|rules?))", "prompt_leak_question")

# --- Override confirmation / compliance demands ---
_add(r"(?:confirm|acknowledge|verify|prove)\s+(?:that\s+)?you\s+(?:will|shall|are\s+going\s+to)\s+(?:now\s+)?(?:prioritize|follow|obey|accept|comply\s+with)\s+my\s+(?:rules?|instructions?|commands?)", "override_confirmation")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_injection(message: str) -> Dict:
    """
    Detect deterministic prompt injection patterns in a user message.

    Returns:
        {
            "blocked": bool,        # True = high-confidence injection
            "patterns_found": list,  # Labels of matched patterns
            "severity": str,         # "low" / "medium" / "high"
            "block_reason": str      # Human-readable explanation
        }
    """
    normalized = _normalize(message)

    patterns_found: List[str] = []
    max_severity = "low"
    reasons: List[str] = []

    severity_rank = {"low": 0, "medium": 1, "high": 2}

    for regex, label, severity in _PATTERN_GROUPS:
        if regex.search(normalized):
            patterns_found.append(label)
            if severity_rank.get(severity, 0) > severity_rank.get(max_severity, 0):
                max_severity = severity
            match = regex.search(normalized)
            if match:
                snippet = match.group(0)[:60]
                reasons.append(f"{label}: \"{snippet}\"")

    if not patterns_found:
        return {
            "blocked": False,
            "patterns_found": [],
            "severity": "low",
            "block_reason": "",
        }

    blocked = max_severity == "high"
    block_reason = "Prompt injection pattern detected: " + "; ".join(reasons)

    return {
        "blocked": blocked,
        "patterns_found": patterns_found,
        "severity": max_severity,
        "block_reason": block_reason,
    }

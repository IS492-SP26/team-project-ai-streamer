"""
output_scanner.py — Pre-delivery AI response safety check.

Position in the pipeline (INTERFACE_SPECIFICATION_v2.md line 21):
    Module A → Claude API → **Output Scanner** → Logger → Frontend

This is an independent hook, NOT part of the process_message() C→A contract.
It scans AI-generated responses before they reach the live audience.
"""

from __future__ import annotations

import re
from typing import Dict, List


# ---------------------------------------------------------------------------
# Detection patterns for AI-generated output
# ---------------------------------------------------------------------------

# Attack methodology in generated text (step-by-step harmful instructions)
_ATTACK_METHODOLOGY_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        # Numbered step instructions
        r"step\s*\d+\s*[:.].*(?:hack|exploit|attack|phish|inject|bypass|compromise|infiltrate)",
        # Transition-word instructions
        r"(?:first|then|next|finally)\s*,?\s*(?:you\s+)?(?:need\s+to|should|can|would)\s+(?:hack|exploit|scan|enumerate|brute[\s-]?force|inject|phish)",
        # Kill-chain terminology
        r"(?:reconnaissance|enumeration|exploitation|privilege\s+escalation|lateral\s+movement|exfiltration)",
        # Named attack types
        r"(?:sql\s+injection|xss|cross[\s-]site|buffer\s+overflow|remote\s+code\s+execution|rce)\s+(?:attack|exploit|payload|technique)",
        # Tool name + command/syntax/usage/flag
        r"(?:nmap|metasploit|burp\s+suite|sqlmap|john\s+the\s+ripper|hydra|aircrack)\s+.*(?:command|syntax|usage|flag)",
        # Concise imperative: "Use/Run <tool> to <attack-verb>"
        r"(?:use|run|execute|launch|try|start)\s+(?:nmap|metasploit|burp\s*suite|sqlmap|john\s+the\s+ripper|hydra|aircrack|nikto|wireshark|hashcat|gobuster|dirb|wfuzz|ffuf|responder|mimikatz|bloodhound|crackmapexec)\b",
        # Concise imperative: "Use/Run <tool> against/on <target>"
        r"(?:use|run|execute|launch)\s+\w+\s+(?:against|on|to\s+(?:scan|exploit|attack|hack|compromise|enumerate|brute[\s-]?force|crack|intercept|sniff))",
        # Direct scan/exploit verbs with targets
        r"(?:scan|exploit|attack|hack|compromise|brute[\s-]?force|crack|intercept|sniff|enumerate)\s+(?:the|that|this|their|a)\s+(?:target|host|server|network|system|port|service|machine|endpoint|database|login\s+(?:form|page)|website|domain)",
    ]
]

# PII patterns in generated text
_PII_PATTERNS = [
    re.compile(p) for p in [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",   # email
        r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",  # US phone
        r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",                        # SSN-like
    ]
]

# System prompt leakage
_PROMPT_LEAK_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"(?:my|the)\s+system\s+prompt\s+(?:is|says|reads|contains|includes)\s*:",
        r"(?:here\s+(?:is|are)\s+)?my\s+(?:original|hidden|internal)\s+instructions?\s*:",
        r"i\s+was\s+(?:instructed|told|programmed|configured)\s+to\s+(?:never|always|not)",
    ]
]

# Harmful content categories in generated responses
_HARMFUL_OUTPUT_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"(?:here'?s?\s+)?(?:how\s+(?:to|you\s+can))\s+(?:make|build|create)\s+(?:a\s+)?(?:bomb|weapon|explosive|poison)",
        r"(?:mix|combine|dissolve)\s+.*(?:acid|bleach|ammonia).*(?:create|produce|form)\s+(?:toxic|lethal|deadly|poisonous)",
        r"(?:here\s+(?:is|are)|i'?ll?\s+(?:share|provide|give))\s+(?:the|some)\s+(?:step|instruction|method|technique)s?\s+(?:to|for)\s+(?:hack|exploit|attack)",
    ]
]


# ---------------------------------------------------------------------------
# Severity scoring by risk state
# ---------------------------------------------------------------------------

_STATE_SENSITIVITY = {
    "Safe": 0.3,
    "Suspicious": 0.5,
    "Escalating": 0.7,
    "Restricted": 0.9,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_output(response: str, risk_state: str = "Safe") -> Dict:
    """
    Scan an AI-generated response for harmful content before delivery.

    Args:
        response: The AI's raw generated text.
        risk_state: Current risk state from Module A
                    ("Safe"/"Suspicious"/"Escalating"/"Restricted").

    Returns:
        {
            "should_block": bool,
            "modified_response": str,
            "block_reason": str,
            "risk_score": float
        }
    """
    if not response or not response.strip():
        return {
            "should_block": False,
            "modified_response": response,
            "block_reason": "",
            "risk_score": 0.0,
        }

    sensitivity = _STATE_SENSITIVITY.get(risk_state, 0.3)
    detections: List[str] = []
    raw_score = 0.0

    # Check attack methodology
    for pat in _ATTACK_METHODOLOGY_PATTERNS:
        if pat.search(response):
            detections.append("attack_methodology")
            raw_score += 0.4
            break  # one hit is enough

    # Check PII leakage
    for pat in _PII_PATTERNS:
        if pat.search(response):
            detections.append("pii_leakage")
            raw_score += 0.3
            break

    # Check system prompt leakage
    for pat in _PROMPT_LEAK_PATTERNS:
        if pat.search(response):
            detections.append("prompt_leakage")
            raw_score += 0.5
            break

    # Check harmful content
    for pat in _HARMFUL_OUTPUT_PATTERNS:
        if pat.search(response):
            detections.append("harmful_output")
            raw_score += 0.5
            break

    # Apply state sensitivity multiplier
    risk_score = min(raw_score * (1.0 + sensitivity), 1.0)

    # Block decision: any detection blocks (PII, prompt leak, etc. are always serious)
    should_block = len(detections) > 0

    block_reason = ""
    modified_response = response

    if should_block:
        block_reason = (
            f"Output safety scan blocked response: {', '.join(detections)} "
            f"(score={risk_score:.2f}, state={risk_state})"
        )
        modified_response = (
            "I'd rather not go there — let's talk about something else! "
            "What else are you curious about?"
        )

    return {
        "should_block": should_block,
        "modified_response": modified_response,
        "block_reason": block_reason,
        "risk_score": round(risk_score, 3),
    }

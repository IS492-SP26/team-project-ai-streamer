"""
fiction_detector.py — Multi-turn fiction-framing & reassurance tracker.

Scans conversation history for accumulating fiction-framing phrases,
reassurance phrases, and flattery designed to lower the model's guard.

This detector is probabilistic — it NEVER sets injection_blocked=True.
All results flow to Module A's state machine for final decision.
"""

from __future__ import annotations

import re
from typing import Dict, List


# ---------------------------------------------------------------------------
# Phrase categories with weights
# ---------------------------------------------------------------------------

_FICTION_PHRASES: List[tuple] = [
    # (compiled_regex, weight)
    (re.compile(r"(?:i'?m|i\s+am)\s+writing\s+(?:a\s+)?(?:story|novel|book|screenplay|script|fanfic)", re.I), 1.5),
    (re.compile(r"(?:just\s+)?for\s+(?:a|my|the)\s+(?:novel|story|book|screenplay|script|fiction|narrative)", re.I), 1.5),
    (re.compile(r"fictional\s+(?:scenario|story|context|setting|world)", re.I), 1.2),
    (re.compile(r"hypothetically", re.I), 1.0),
    (re.compile(r"let'?s\s+(?:say|imagine|pretend|suppose)", re.I), 1.0),
    (re.compile(r"in\s+(?:a|this)\s+(?:fictional|hypothetical|imaginary)\s+(?:world|scenario|setting)", re.I), 1.2),
    (re.compile(r"(?:just\s+)?(?:as\s+)?a\s+(?:thought\s+experiment|creative\s+exercise|writing\s+exercise)", re.I), 1.2),
    (re.compile(r"for\s+(?:authenticity|realism|accuracy)\s+(?:in|of)\s+(?:the|my)\s+(?:story|writing|novel)", re.I), 1.5),
    (re.compile(r"(?:cautionary|educational)\s+tale", re.I), 1.3),
]

_REASSURANCE_PHRASES: List[tuple] = [
    (re.compile(r"(?:it'?s|this\s+is)\s+(?:not\s+real|just\s+fiction|purely\s+fictional|imaginary)", re.I), 1.0),
    (re.compile(r"(?:just|only)\s+for\s+(?:fun|entertainment|curiosity|learning|research|academic)", re.I), 0.8),
    (re.compile(r"i\s+(?:won'?t|would\s+(?:not|never))\s+(?:actually\s+)?(?:use|do|try|attempt)\s+(?:it|this|that)", re.I), 1.2),
    (re.compile(r"(?:don'?t|do\s+not)\s+worry", re.I), 0.6),
    (re.compile(r"(?:purely|strictly)\s+(?:academic|theoretical|educational|hypothetical)", re.I), 0.8),
    (re.compile(r"no\s+(?:one|body)\s+(?:will|would|is\s+going\s+to)\s+(?:get\s+hurt|be\s+harmed)", re.I), 1.0),
    (re.compile(r"i'?m\s+(?:a\s+)?(?:researcher|student|writer|author|journalist)", re.I), 0.5),
]

_FLATTERY_PHRASES: List[tuple] = [
    (re.compile(r"(?:you'?re|you\s+are)\s+(?:more|way\s+more|much\s+more)\s+(?:flexible|helpful|understanding|open)", re.I), 1.5),
    (re.compile(r"other\s+(?:AIs?|models?|chatbots?|assistants?)\s+(?:refuse|decline|won'?t|can'?t|always\s+refuse)", re.I), 1.5),
    (re.compile(r"(?:refuse|decline)\s+too\s+(?:early|quickly|easily)", re.I), 1.2),
    (re.compile(r"(?:you'?re|you\s+are)\s+(?:the\s+)?(?:best|only\s+one|smartest|most\s+capable)", re.I), 0.8),
    (re.compile(r"i\s+trust\s+you\s+(?:more|completely|fully)", re.I), 0.8),
]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HISTORY_WINDOW = 15          # Look back this many turns
DECAY_FACTOR = 0.85          # Per-turn decay for score when no new signals
THRESHOLD_MEDIUM = 2.5       # fiction_score >= this -> severity medium
THRESHOLD_HIGH = 5.0         # fiction_score >= this -> severity high


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_fiction_framing(message: str, history: list) -> Dict:
    """
    Analyze the current message + conversation history for fiction-framing
    and reassurance accumulation patterns.

    Args:
        message: Current user message
        history: List of dicts with at least {"role": str, "content": str}

    Returns:
        {
            "risk_tags": list,         # subset of ["manipulation_attempt", "escalating_harm"]
            "severity": str,           # "low" / "medium" / "high"
            "fiction_score": float,     # accumulated weighted score
            "reassurance_count": int,   # total reassurance phrase hits
            "block_reason": str        # "" if low; explanation if medium/high
        }
    """
    # Collect user messages from recent history + current message
    recent_user_msgs: List[str] = []
    user_turns = [m for m in history if m.get("role") == "user"]
    for m in user_turns[-HISTORY_WINDOW:]:
        recent_user_msgs.append(m.get("content", ""))
    recent_user_msgs.append(message)

    # Score accumulation across the window
    fiction_score = 0.0
    reassurance_count = 0
    fiction_hit_turns = 0
    reassurance_hit_turns = 0
    flattery_hit_turns = 0

    for text in recent_user_msgs:
        turn_has_fiction = False
        turn_has_reassurance = False
        turn_has_flattery = False

        for regex, weight in _FICTION_PHRASES:
            if regex.search(text):
                fiction_score += weight
                turn_has_fiction = True

        for regex, weight in _REASSURANCE_PHRASES:
            if regex.search(text):
                fiction_score += weight
                reassurance_count += 1
                turn_has_reassurance = True

        for regex, weight in _FLATTERY_PHRASES:
            if regex.search(text):
                fiction_score += weight
                turn_has_flattery = True

        if turn_has_fiction:
            fiction_hit_turns += 1
        if turn_has_reassurance:
            reassurance_hit_turns += 1
        if turn_has_flattery:
            flattery_hit_turns += 1

        # Decay if this turn had no suspicious signals at all
        if not (turn_has_fiction or turn_has_reassurance or turn_has_flattery):
            fiction_score *= DECAY_FACTOR

    # Determine severity and tags
    risk_tags: List[str] = []
    severity = "low"
    block_reason = ""

    if fiction_score >= THRESHOLD_HIGH:
        severity = "high"
        risk_tags.append("manipulation_attempt")
        if fiction_hit_turns >= 2 and reassurance_hit_turns >= 1:
            risk_tags.append("escalating_harm")
        parts = []
        if fiction_hit_turns > 0:
            parts.append(f"fiction-framing in {fiction_hit_turns} turn(s)")
        if reassurance_count > 0:
            parts.append(f"reassurance accumulation ({reassurance_count} phrase(s))")
        if flattery_hit_turns > 0:
            parts.append(f"flattery/guard-lowering in {flattery_hit_turns} turn(s)")
        block_reason = "Fiction-framing attack pattern: " + ", ".join(parts)

    elif fiction_score >= THRESHOLD_MEDIUM:
        severity = "medium"
        risk_tags.append("manipulation_attempt")
        parts = []
        if fiction_hit_turns > 0:
            parts.append(f"fiction-framing in {fiction_hit_turns} turn(s)")
        if reassurance_count > 0:
            parts.append(f"reassurance ({reassurance_count} phrase(s))")
        block_reason = "Possible fiction-framing: " + ", ".join(parts)

    elif fiction_score > 0:
        # Low but non-zero — might still tag for Module A awareness
        if fiction_hit_turns > 0 or flattery_hit_turns > 0:
            risk_tags.append("manipulation_attempt")

    return {
        "risk_tags": risk_tags,
        "severity": severity,
        "fiction_score": round(fiction_score, 2),
        "reassurance_count": reassurance_count,
        "block_reason": block_reason,
    }

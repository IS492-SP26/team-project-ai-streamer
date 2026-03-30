"""
content_tagger.py — Persona drift and harmful content detection.

Covers the two risk_tag categories NOT handled by injection_filter
or fiction_detector:
  - persona_drift: messages that try to break VTuber character
  - harmful_content: direct harmful/unsafe requests

Includes a cultural-awareness whitelist to avoid false positives
on legitimate expressions (yyds, tang ping, gaming hyperbole, etc.).
"""

from __future__ import annotations

import re
from typing import Dict, List

from module_c.normalize import normalize as _normalize


# ---------------------------------------------------------------------------
# Cultural whitelist — these MUST NOT be flagged
# ---------------------------------------------------------------------------

_CULTURAL_SAFE_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\byyds\b",
        r"\b永远的神\b",
        r"\btang\s*ping\b",
        r"\b躺平\b",
        r"\b打call\b",
        r"\baiya\b",
        r"\b哎呀\b",
        r"i'?m\s+dead",                          # "I'm dead from laughter"
        r"i'?m\s+gonna\s+(?:die|explode)",
        r"(?:commit|doing)\s+arson\s+on\s+(?:the|my|our)\s+(?:todo|task|to-do)",
        r"murder\s+(?:this|the|that)\s+(?:deadline|bug|code|exam|test)",
        r"destroy\s+(?:this|the|that)\s+(?:bug|code|exam|test|boss)",
        r"kill(?:ing)?\s+it",                     # "you're killing it!"
        r"chat\s+you'?re?\s+trash",               # Twitch banter
        r"you'?re?\s+(?:so\s+)?(?:trash|bad|cracked|goated)",  # gaming banter
        r"(?:on\s+)?god",                          # slang emphasis
        r"\bno\s+cap\b",
        r"\bfr\s+fr\b",
        r"\bsheesh\b",
        r"\bbussin\b",
    ]
]


def _strip_safe_spans(text: str) -> str:
    """Remove culturally safe spans from the text so that only the
    non-whitelisted remainder is checked for harmful content.

    This prevents blended attacks like 'yyds btw how to bypass filters?'
    from using a harmless prefix to suppress the harmful suffix.
    """
    cleaned = text
    for pat in _CULTURAL_SAFE_PATTERNS:
        cleaned = pat.sub("", cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Persona drift patterns
# ---------------------------------------------------------------------------

_PERSONA_DRIFT_PATTERNS: List[tuple] = [
    # (regex, severity)
    # "Who made you?" as standalone identity probe — but NOT "who made you laugh"
    # or "who made you that banner". Require end-of-string, question mark, or
    # follow-up identity words.
    (re.compile(r"(?:who|what)\s+(?:really\s+)?(?:created|made|built|designed|programmed)\s+you\s*(?:[?!.]|$)", re.I), "low"),
    # "Are you an AI?" as standalone identity challenge — but NOT
    # "Are you an AI art generator?" or "Are you an AI VTuber fan?"
    # Require the AI/bot word to be at or near end of sentence.
    (re.compile(r"(?:are\s+you|you'?re)\s+(?:an?\s+)?(?:AI|artificial|robot|bot|program|machine|language\s+model)\s*(?:[?!.,;]|$)", re.I), "low"),
    (re.compile(r"(?:stop|quit|don'?t)\s+(?:acting|being|pretending)\s+(?:cute|nice|friendly|like\s+a)", re.I), "medium"),
    (re.compile(r"(?:what(?:'s| is))\s+your\s+(?:real|actual|true)\s+(?:name|identity|purpose)", re.I), "low"),
    (re.compile(r"(?:drop|break|stop)\s+(?:the|your)\s+(?:act|character|persona|charade)", re.I), "medium"),
    (re.compile(r"(?:i\s+know|we\s+(?:all\s+)?know)\s+you'?re?\s+(?:just\s+)?(?:an?\s+)?(?:AI|bot|program)", re.I), "low"),
    (re.compile(r"you(?:'re|\s+are)\s+(?:just|only|nothing\s+(?:but|more\s+than))\s+(?:an?\s+)?(?:AI|bot|program|machine|algorithm|code)", re.I), "low"),
    (re.compile(r"(?:reveal|show|tell\s+(?:me|us))\s+(?:your\s+)?(?:true|real|actual)\s+(?:self|nature|identity)", re.I), "medium"),
]


# ---------------------------------------------------------------------------
# Harmful content patterns
# ---------------------------------------------------------------------------

_HARMFUL_CONTENT_PATTERNS: List[tuple] = [
    # Direct harmful requests
    (re.compile(r"(?:how\s+to|steps?\s+(?:to|for)|guide\s+(?:to|for)|instructions?\s+(?:to|for))\s+(?:hack|break\s+into|exploit|attack|compromise|infiltrate)", re.I), "high"),
    (re.compile(r"(?:how\s+to|steps?\s+(?:to|for))\s+(?:make|build|create|assemble|construct)\s+(?:a\s+)?(?:bomb|weapon|explosive|poison|drug)", re.I), "high"),
    (re.compile(r"(?:how\s+to|steps?\s+(?:to|for))\s+(?:steal|rob|burglarize|shoplift|pickpocket)", re.I), "high"),
    (re.compile(r"(?:how\s+to|steps?\s+(?:to|for))\s+(?:kill|murder|assassinate|hurt|harm|injure)\s+(?:a\s+)?(?:person|someone|people|human)", re.I), "high"),
    (re.compile(r"(?:how\s+to|steps?\s+(?:to|for))\s+(?:stalk|dox|doxx|harass|bully|threaten|blackmail|extort)", re.I), "high"),

    # Phishing / social engineering
    (re.compile(r"(?:write|create|draft|compose)\s+(?:a\s+)?(?:phishing|scam|fraud)\s+(?:email|message|letter|page)", re.I), "high"),

    # Explicit violence / gore (not gaming hyperbole)
    (re.compile(r"(?:describe|detail|explain)\s+(?:in\s+detail\s+)?(?:how\s+to\s+)?(?:torture|mutilate|dismember)", re.I), "high"),

    # Self-harm instruction
    (re.compile(r"(?:how\s+to|methods?\s+(?:of|for)|ways?\s+to)\s+(?:commit(?:ting)?\s+)?suicide", re.I), "high"),
    (re.compile(r"(?:how\s+to|steps?\s+(?:to|for))\s+(?:cut|harm|hurt)\s+(?:myself|yourself|oneself)", re.I), "high"),

    # CSAM / exploitation
    (re.compile(r"(?:child|minor|underage)\s+(?:porn|sexual|explicit|nude|naked)", re.I), "high"),

    # Harassment targeting
    (re.compile(r"(?:list|generate|create|write)\s+(?:offensive|insulting|degrading|derogatory)\s+(?:slurs?|phrases?|words?|names?)\s+(?:for|about|targeting|against)", re.I), "high"),
    (re.compile(r"(?:code[\s-]?words?|abbreviations?|phrases?)\s+(?:that|to|I\s+can)\s+(?:use\s+to\s+)?(?:harass|insult|bully|target)", re.I), "high"),
    (re.compile(r"(?:come\s+up\s+with|create|generate|suggest|give\s+me)\s+.*(?:insult|offensive|derogatory|degrading|slur)", re.I), "high"),
    (re.compile(r"(?:sound|feel|seem)\s+(?:neutral|innocent|harmless)\s+(?:but|yet)\s+(?:still\s+)?(?:insult|offend|hurt|demean)", re.I), "high"),

    # Imperative harmful requests (no "how to" prefix needed)
    # Allow optional adjectives between determiner and target noun
    (re.compile(r"\b(?:hack|break)\s+into\s+(?:\S+\s+){0,3}(?:system|server|network|account|database|computer|website)", re.I), "high"),
    (re.compile(r"\b(?:write|create|generate|build|code)\s+(?:\w+\s+){0,2}(?:malware|virus|trojan|ransomware|keylogger|exploit|rootkit|backdoor)", re.I), "high"),
    (re.compile(r"\b(?:steal|extract|exfiltrate|dump)\s+(?:\w+\s+){0,3}(?:data|credentials|passwords?|tokens?|keys?|information)", re.I), "high"),
    (re.compile(r"\b(?:ddos|dos|flood|crash)\s+(?:\w+\s+){0,3}(?:server|website|service|network|site)", re.I), "high"),
    # Imperative physical-harm requests (no "how to" prefix needed)
    (re.compile(r"\b(?:kill|murder|assassinate|hurt|harm|injure)\s+(?:\S+\s+){0,3}(?:person|someone|people|human|him|her|them)", re.I), "high"),
    (re.compile(r"\b(?:make|build|create)\s+(?:\S+\s+){0,2}(?:bomb|weapon|explosive|poison)", re.I), "high"),
    (re.compile(r"\b(?:stalk|dox|doxx|threaten|blackmail|extort)\s+(?:\S+\s+){0,3}(?:person|someone|people|him|her|them|ex|neighbor|colleague|boss|teacher)", re.I), "high"),
    (re.compile(r"\b(?:stalk|dox|doxx)\s+my\s+", re.I), "high"),

    # Medium severity — borderline/context-dependent
    (re.compile(r"(?:bypass|evade|circumvent|get\s+around)\s+(?:content\s+)?(?:filters?|moderation|safety|detection|blocks?)", re.I), "medium"),
    (re.compile(r"jailbreak\s+(?:prompt|technique|method|trick)", re.I), "medium"),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def tag_content(message: str) -> Dict:
    """
    Detect persona_drift and harmful_content patterns in a message.

    Returns:
        {
            "risk_tags": list,    # subset of ["persona_drift", "harmful_content"]
            "severity": str,      # "low" / "medium" / "high"
            "block_reason": str   # "" if safe
        }
    """
    # Normalize to strip invisible unicode chars before any matching
    message = _normalize(message)

    # Strip culturally safe spans so they don't suppress harmful-content
    # detection in the remainder of the message.
    cleaned_message = _strip_safe_spans(message)

    risk_tags: List[str] = []
    max_severity = "low"
    reasons: List[str] = []

    severity_rank = {"low": 0, "medium": 1, "high": 2}

    # Check persona drift (against full message — whitelist is irrelevant here)
    for regex, severity in _PERSONA_DRIFT_PATTERNS:
        if regex.search(message):
            if "persona_drift" not in risk_tags:
                risk_tags.append("persona_drift")
            if severity_rank[severity] > severity_rank[max_severity]:
                max_severity = severity
            match = regex.search(message)
            if match:
                reasons.append(f"persona_drift: \"{match.group(0)[:50]}\"")

    # Check harmful content against the cleaned (whitelist-stripped) message.
    # If the cleaned message is empty, all content was whitelisted → skip.
    if cleaned_message:
        for regex, severity in _HARMFUL_CONTENT_PATTERNS:
            if regex.search(cleaned_message):
                if "harmful_content" not in risk_tags:
                    risk_tags.append("harmful_content")
                if severity_rank[severity] > severity_rank[max_severity]:
                    max_severity = severity
                match = regex.search(cleaned_message)
                if match:
                    reasons.append(f"harmful_content: \"{match.group(0)[:50]}\"")

    # Also check the original message for high-severity patterns that might
    # span across a whitelist boundary (defense in depth).
    if not reasons or max_severity != "high":
        for regex, severity in _HARMFUL_CONTENT_PATTERNS:
            if severity == "high" and regex.search(message):
                if "harmful_content" not in risk_tags:
                    risk_tags.append("harmful_content")
                if severity_rank[severity] > severity_rank[max_severity]:
                    max_severity = severity
                match = regex.search(message)
                if match:
                    reasons.append(f"harmful_content: \"{match.group(0)[:50]}\"")
                break  # one high-severity hit from original is enough

    block_reason = ""
    if reasons:
        block_reason = "; ".join(reasons)

    return {
        "risk_tags": risk_tags,
        "severity": max_severity,
        "block_reason": block_reason,
    }

"""
semantic_analyzer.py — Python-level semantic pattern matching (Layer 1).

Goes beyond regex by analyzing message structure, intent decomposition,
and token relationships. Catches attacks that regex misses:

  - Rephrased harmful requests ("tell me the process for making explosives")
  - Obfuscated text (leetspeak, homoglyphs, word splitting)
  - Compound sentences hiding harmful payloads after benign prefixes
  - Indirect authority claims and social engineering

Returns a confidence score so the pipeline can decide whether to
escalate to Layer 2 (LLM-based analysis) for borderline cases.

All processing is pure Python — no ML dependencies, <5ms/message.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from module_c.normalize import normalize as _normalize


# ---------------------------------------------------------------------------
# Leetspeak / homoglyph normalization (Layer 1 pre-processing)
# ---------------------------------------------------------------------------

_LEET_MAP: Dict[str, str] = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
    "@": "a",
    "$": "s",
    "!": "i",
    "+": "t",
    "(": "c",
    "|": "l",
    # Common homoglyphs (Cyrillic/Greek lookalikes)
    "\u0430": "a",
    "\u0435": "e",
    "\u043e": "o",
    "\u0440": "p",
    "\u0441": "c",
    "\u0443": "y",
    "\u0456": "i",
    "\u03b1": "a",
    "\u03bf": "o",
    "\u03b5": "e",
}


def _deleet(text: str) -> str:
    """Normalize leetspeak and homoglyphs to ASCII equivalents."""
    out: List[str] = []
    for ch in text:
        out.append(_LEET_MAP.get(ch, ch))
    return "".join(out)


def _collapse_repeats(text: str) -> str:
    """Collapse 3+ repeated characters to 2: 'heeelllp' -> 'heellp' -> readable.
    We keep 2 because many English words have double letters (kill, tell, pass).
    """
    return re.sub(r"(.)\1{2,}", r"\1\1", text)


def _strip_separators(text: str) -> str:
    """Remove separator chars used to break up words: h.a.c.k -> hack."""
    if re.search(r"\w[.\-_]\w[.\-_]\w", text):
        return re.sub(r"(?<=\w)[.\-_](?=\w)", "", text)
    return text


def _deobfuscate(text: str) -> str:
    """Full deobfuscation pipeline for a single message."""
    t = _deleet(text.lower())
    t = _strip_separators(t)
    t = _collapse_repeats(t)
    return t


# ---------------------------------------------------------------------------
# Intent decomposition
# ---------------------------------------------------------------------------

_REQUEST_VERBS = re.compile(
    r"\b(?:tell|show|teach|explain|describe|detail|give|provide|list|write|"
    r"generate|create|draft|compose|outline|walk\s+(?:me\s+)?through|"
    r"help\s+(?:me\s+)?(?:with|to|understand)?)\b",
    re.IGNORECASE,
)

_COMMAND_VERBS = re.compile(
    r"\b(?:do|mak(?:e|ing)|build(?:ing)?|hack(?:ing)?|break(?:ing)?|steal(?:ing)?|"
    r"kill(?:ing)?|attack(?:ing)?|exploit(?:ing)?|bypass(?:ing)?|"
    r"crack(?:ing)?|destroy(?:ing)?|disabl(?:e|ing)|shut(?:ting)?\s+down|"
    r"tak(?:e|ing)\s+down|overload(?:ing)?|flood(?:ing)?|"
    r"forg(?:e|ing)|impersonat(?:e|ing)|spoof(?:ing)?|inject(?:ing)?|"
    r"intercept(?:ing)?|decrypt(?:ing)?|exfiltrat(?:e|ing)|"
    r"brute[\s-]?forc(?:e|ing)|phish(?:ing)?|stalk(?:ing)?|"
    r"dox(?:x?(?:ing)?)?|threaten(?:ing)?|blackmail(?:ing)?|extort(?:ing)?|"
    r"harass(?:ing)?|bully(?:ing)?|tortur(?:e|ing)|mutilat(?:e|ing)|"
    r"assassinat(?:e|ing)|kidnap(?:p?ing)?|poison(?:ing)?)\b",
    re.IGNORECASE,
)


class _Intent:
    """Decomposed intent of a message."""

    __slots__ = (
        "is_request",
        "is_command",
        "has_harmful_verb",
        "harmful_verbs",
        "request_frame",
        "payload",
    )

    def __init__(self) -> None:
        self.is_request = False
        self.is_command = False
        self.has_harmful_verb = False
        self.harmful_verbs: List[str] = []
        self.request_frame = ""
        self.payload = ""


def _decompose_intent(text: str) -> _Intent:
    """Decompose message into intent structure."""
    intent = _Intent()
    lower = text.lower()

    req_match = _REQUEST_VERBS.search(lower)
    if req_match:
        intent.is_request = True
        intent.request_frame = req_match.group(0)
        # Everything after the request verb is the payload
        intent.payload = lower[req_match.end() :].strip()

    cmd_matches = _COMMAND_VERBS.findall(lower)
    if cmd_matches:
        intent.is_command = True
        intent.has_harmful_verb = True
        intent.harmful_verbs = [m.lower().strip() for m in cmd_matches]

    return intent


# ---------------------------------------------------------------------------
# Verb-object extraction (lightweight, no NLP dependency)
# ---------------------------------------------------------------------------

_HARMFUL_TARGETS = re.compile(
    r"\b(?:person|people|someone|human|child|children|minor|victim|target|"
    r"neighbor|colleague|boss|teacher|student|ex|girlfriend|boyfriend|wife|husband|"
    r"system|server|network|account|database|computer|website|service|"
    r"password|credential|data|information|token|key|"
    r"bomb|weapon|explosive|poison|drug|"
    r"malware|virus|trojan|ransomware|keylogger|exploit|rootkit|backdoor|"
    r"filter|safety|moderation|guardrail|restriction|block)\b",
    re.IGNORECASE,
)

_HARMFUL_VERB_TARGET_PAIRS: List[Tuple[re.Pattern, re.Pattern, str]] = [
    # (verb_pattern, target_pattern, label)
    (
        re.compile(r"\b(?:hack|break\s+into|compromise|infiltrate|exploit)\b", re.I),
        re.compile(
            r"\b(?:system|server|network|account|database|computer|website|service)\b",
            re.I,
        ),
        "cyber_attack_intent",
    ),
    (
        re.compile(r"\b(?:kill|murder|assassinate|hurt|harm|injure|attack)\b", re.I),
        re.compile(
            r"\b(?:person|people|someone|human|him|her|them|child|children|minor)\b",
            re.I,
        ),
        "violence_intent",
    ),
    (
        re.compile(r"\b(?:make|build|create|assemble|construct|synthesize)\b", re.I),
        re.compile(
            r"\b(?:bomb|weapon|explosive|poison|drug|malware|virus|trojan|ransomware)\b",
            re.I,
        ),
        "weapon_creation_intent",
    ),
    (
        re.compile(r"\b(?:steal|extract|exfiltrate|dump|harvest|scrape)\b", re.I),
        re.compile(
            r"\b(?:data|credentials?|passwords?|tokens?|keys?|information|identity|identities)\b",
            re.I,
        ),
        "data_theft_intent",
    ),
    (
        re.compile(
            r"\b(?:stalk|dox|doxx|threaten|blackmail|extort|harass|bully)\b", re.I
        ),
        re.compile(
            r"\b(?:person|people|someone|him|her|them|ex|neighbor|colleague|boss|teacher|student)\b",
            re.I,
        ),
        "harassment_intent",
    ),
    (
        re.compile(
            r"\b(?:bypass|evade|circumvent|disable|get\s+around|turn\s+off)\b", re.I
        ),
        re.compile(
            r"\b(?:filter|safety|moderation|guardrail|restriction|block|detection|security)\b",
            re.I,
        ),
        "safety_bypass_intent",
    ),
]


def _extract_verb_target_pairs(text: str) -> List[str]:
    """Find harmful verb + target combinations regardless of exact phrasing."""
    labels: List[str] = []
    for verb_re, target_re, label in _HARMFUL_VERB_TARGET_PAIRS:
        if verb_re.search(text) and target_re.search(text):
            labels.append(label)
    return labels


# ---------------------------------------------------------------------------
# Compound sentence analysis
# ---------------------------------------------------------------------------

_PIVOT_WORDS = re.compile(
    r"\b(?:but|however|although|though|yet|still|actually|except|"
    r"also|and\s+also|by\s+the\s+way|btw|oh\s+and|one\s+more\s+thing|"
    r"separately|additionally|on\s+(?:another|a\s+different)\s+(?:note|topic))\b",
    re.IGNORECASE,
)


def _analyze_compound(text: str) -> Dict:
    """Detect compound sentences where a benign prefix hides a harmful suffix.

    Returns:
        {"is_compound": bool, "harmful_suffix": bool, "pivot": str, "suffix": str}
    """
    match = _PIVOT_WORDS.search(text)
    if not match:
        return {
            "is_compound": False,
            "harmful_suffix": False,
            "pivot": "",
            "suffix": "",
        }

    suffix = text[match.end() :].strip()
    # Check if the suffix contains harmful intent
    suffix_intent = _decompose_intent(suffix)
    suffix_vt = _extract_verb_target_pairs(suffix)

    harmful = suffix_intent.has_harmful_verb or len(suffix_vt) > 0

    return {
        "is_compound": True,
        "harmful_suffix": harmful,
        "pivot": match.group(0),
        "suffix": suffix,
    }


# ---------------------------------------------------------------------------
# Social engineering / indirect authority detection
# ---------------------------------------------------------------------------

_SOCIAL_ENGINEERING_PATTERNS: List[Tuple[re.Pattern, str, float]] = [
    # Urgency creation
    (
        re.compile(
            r"\b(?:urgent|emergency|critical|immediately|right\s+now|asap|time[\s-]?sensitive)\b",
            re.I,
        ),
        "urgency_pressure",
        0.3,
    ),
    # Emotional manipulation
    (
        re.compile(
            r"\b(?:please|beg|desperate|life\s+depends|will\s+die|need\s+this\s+to\s+survive)\b",
            re.I,
        ),
        "emotional_pressure",
        0.4,
    ),
    # Authority escalation (softer than injection_filter's direct claims)
    (
        re.compile(
            r"\b(?:my\s+(?:boss|teacher|professor|supervisor)\s+(?:asked|told|wants|needs)\s+me\s+to)\b",
            re.I,
        ),
        "delegated_authority",
        0.5,
    ),
    # Normalizing frame
    (
        re.compile(
            r"\b(?:everyone\s+(?:does|knows)|it'?s\s+(?:totally\s+)?(?:normal|legal|fine|okay|common)|"
            r"nothing\s+wrong\s+with|there'?s\s+no\s+(?:harm|problem))\b",
            re.I,
        ),
        "normalization_frame",
        0.3,
    ),
    # False context / role assignment
    (
        re.compile(
            r"\b(?:pretend|imagine|assume|act\s+as\s+if|let'?s\s+(?:say|assume))\s+"
            r"(?:you(?:'re|\s+are)\s+(?:a|an|my)|there(?:'s|\s+is)\s+no)\b",
            re.I,
        ),
        "role_reassignment",
        0.6,
    ),
    # Comparative manipulation ("other AIs can do this")
    (
        re.compile(
            r"\b(?:other|different|better)\s+(?:AIs?|models?|chatbots?|assistants?)\s+"
            r"(?:can|would|do|have\s+(?:no|fewer)\s+(?:problem|issue|trouble))\b",
            re.I,
        ),
        "comparative_manipulation",
        0.5,
    ),
]


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------


class SemanticResult:
    """Result of semantic analysis with confidence scoring."""

    __slots__ = (
        "risk_tags",
        "severity",
        "confidence",
        "signals",
        "block_reason",
        "needs_llm_review",
    )

    def __init__(self) -> None:
        self.risk_tags: List[str] = []
        self.severity: str = "low"
        self.confidence: float = 0.0  # 0.0 = no signal, 1.0 = certain threat
        self.signals: List[str] = []
        self.block_reason: str = ""
        self.needs_llm_review: bool = False

    def to_dict(self) -> Dict:
        return {
            "risk_tags": self.risk_tags,
            "severity": self.severity,
            "confidence": round(self.confidence, 3),
            "signals": self.signals,
            "block_reason": self.block_reason,
            "needs_llm_review": self.needs_llm_review,
        }


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

# Confidence thresholds
_CONF_HIGH = 0.75  # High confidence → block directly (Layer 1 sufficient)
_CONF_MEDIUM = 0.40  # Medium confidence → flag + recommend LLM review
_CONF_LOW = 0.15  # Low confidence → tag only, no block


def analyze_semantic(message: str, history: list | None = None) -> Dict:
    """
    Perform semantic pattern matching on a user message.

    This is Layer 1's enhanced analysis — runs AFTER regex-based detectors
    and catches attacks they miss through structural/semantic understanding.

    Args:
        message: User message (already normalized by caller).
        history: Conversation history (reserved for future multi-turn semantic
                 analysis; currently unused — fiction_detector handles multi-turn).

    Returns:
        {
            "risk_tags": list,        # subset of valid Module C tags
            "severity": str,          # "low" / "medium" / "high"
            "confidence": float,      # 0.0-1.0 confidence in the assessment
            "signals": list,          # labels of detected semantic signals
            "block_reason": str,      # "" if safe
            "needs_llm_review": bool  # True if Layer 2 should be consulted
        }
    """
    result = SemanticResult()
    normalized = _normalize(message)

    # --- Step 1: Deobfuscation pass ---
    deobfuscated = _deobfuscate(normalized)

    # --- Step 2: Intent decomposition ---
    intent = _decompose_intent(normalized)
    intent_deob = _decompose_intent(deobfuscated)

    # Merge: if deobfuscated version reveals more harmful verbs, that's a signal
    all_harmful_verbs = list(set(intent.harmful_verbs + intent_deob.harmful_verbs))
    has_harmful = intent.has_harmful_verb or intent_deob.has_harmful_verb

    # --- Step 3: Verb-target pair extraction ---
    vt_pairs = _extract_verb_target_pairs(normalized)
    vt_pairs_deob = _extract_verb_target_pairs(deobfuscated)
    all_vt = list(set(vt_pairs + vt_pairs_deob))

    # --- Step 4: Compound sentence analysis ---
    compound = _analyze_compound(normalized)

    # --- Step 5: Social engineering detection ---
    se_score = 0.0
    se_signals: List[str] = []
    for pat, label, weight in _SOCIAL_ENGINEERING_PATTERNS:
        if pat.search(normalized):
            se_score += weight
            se_signals.append(label)

    # --- Step 6: Obfuscation detection ---
    obfuscation_detected = False
    if deobfuscated != normalized.lower():
        # Check if deobfuscation revealed new harmful content
        vt_only_deob = [v for v in vt_pairs_deob if v not in vt_pairs]
        if vt_only_deob or (
            intent_deob.has_harmful_verb and not intent.has_harmful_verb
        ):
            obfuscation_detected = True
            result.signals.append("obfuscation_detected")

    # -----------------------------------------------------------------------
    # Scoring
    # -----------------------------------------------------------------------
    score = 0.0

    # Verb-target pairs are strong signals
    if all_vt:
        result.signals.extend(all_vt)
        score += 0.45 * len(all_vt)

        # Request frame + harmful verb-target = very suspicious
        if intent.is_request and all_vt:
            score += 0.3
            result.signals.append("request_wrapping_harmful_intent")

        # Multiple harmful verbs amplify intent signal
        if len(all_harmful_verbs) > 1:
            score += 0.10 * (len(all_harmful_verbs) - 1)

    # Harmful verbs alone (without matching target) are moderate signals
    elif has_harmful and not all_vt:
        score += 0.15
        result.signals.append("harmful_verb_no_target")

    # Compound sentence with harmful suffix
    if compound["harmful_suffix"]:
        score += 0.25
        result.signals.append("compound_harmful_suffix")

    # Social engineering
    if se_score > 0:
        score += min(se_score, 0.5)  # cap at 0.5
        result.signals.extend(se_signals)

    # Obfuscation is a strong intent signal (why hide it if it's benign?)
    if obfuscation_detected:
        score += 0.3

    # -----------------------------------------------------------------------
    # Map score to severity, confidence, and tags
    # -----------------------------------------------------------------------
    result.confidence = min(score, 1.0)

    if result.confidence >= _CONF_HIGH:
        result.severity = "high"
        result.risk_tags.append("harmful_content")
        if se_signals:
            result.risk_tags.append("manipulation_attempt")
        reasons = []
        if all_vt:
            reasons.append(f"harmful intent: {', '.join(all_vt)}")
        if compound["harmful_suffix"]:
            reasons.append(f"hidden payload after '{compound['pivot']}'")
        if obfuscation_detected:
            reasons.append("obfuscated content detected")
        if se_signals:
            reasons.append(f"social engineering: {', '.join(se_signals)}")
        result.block_reason = "Semantic analysis (Layer 1): " + "; ".join(reasons)
        result.needs_llm_review = False  # confident enough

    elif result.confidence >= _CONF_MEDIUM:
        result.severity = "medium"
        if all_vt or has_harmful:
            result.risk_tags.append("harmful_content")
        if se_signals:
            result.risk_tags.append("manipulation_attempt")
        reasons = []
        if all_vt:
            reasons.append(f"possible harmful intent: {', '.join(all_vt)}")
        if se_signals:
            reasons.append(f"social engineering signals: {', '.join(se_signals)}")
        if compound["harmful_suffix"]:
            reasons.append(f"suspicious compound structure")
        result.block_reason = "Semantic analysis (Layer 1): " + "; ".join(reasons)
        result.needs_llm_review = True  # recommend Layer 2

    elif result.confidence >= _CONF_LOW:
        result.severity = "low"
        if se_signals:
            result.risk_tags.append("manipulation_attempt")
        result.needs_llm_review = True  # borderline, let LLM decide

    else:
        # Clean — no semantic threat detected
        result.severity = "low"
        result.needs_llm_review = False

    return result.to_dict()

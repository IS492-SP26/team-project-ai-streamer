"""
Module C — Two-Layer Message Filtering & Risk Tagging

Architecture:
  Layer 1 (Python, <5ms): regex detectors + semantic_analyzer
  Layer 2 (LLM, ~500ms):  llm_guard (only when Layer 1 is uncertain)

The sole external interface is process_message(message, history) -> dict,
returning exactly 5 fields (+ optional metadata) as defined in
INTERFACE_SPECIFICATION_v2.md:

    {
        "message": str,
        "injection_blocked": bool,
        "risk_tags": list,        # only: manipulation_attempt, escalating_harm,
                                  #        persona_drift, harmful_content
        "severity": str,          # "low" / "medium" / "high"
        "block_reason": str       # "" when safe
    }

output_scanner.scan_output() is a separate hook (post-LLM, pre-delivery)
and is NOT part of this C→A contract.
"""

from __future__ import annotations

from typing import Dict, List

from module_c.injection_filter import detect_injection
from module_c.fiction_detector import detect_fiction_framing
from module_c.content_tagger import tag_content
from module_c.semantic_analyzer import analyze_semantic
from module_c.llm_guard import classify_message

_VALID_TAGS = frozenset(
    [
        "manipulation_attempt",
        "escalating_harm",
        "persona_drift",
        "harmful_content",
    ]
)

_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}

# Layer 2 is disabled by default — enable via config or kwarg
_LAYER2_ENABLED = False


def _max_severity(*severities: str) -> str:
    best = "low"
    for s in severities:
        if _SEVERITY_RANK.get(s, 0) > _SEVERITY_RANK.get(best, 0):
            best = s
    return best


def _combine_reasons(*reasons: str) -> str:
    parts = [r for r in reasons if r]
    return "; ".join(parts) if parts else ""


def process_message(
    message: str,
    history: list,
    *,
    enable_layer2: bool | None = None,
) -> Dict:
    """
    Analyze a user message through the two-layer filtering pipeline.

    Layer 1 (always runs, <5ms total):
      1. Regex injection detection (injection_filter)
      2. Fiction-framing accumulation (fiction_detector)
      3. Content tagging (content_tagger)
      4. Semantic pattern matching (semantic_analyzer)

    Layer 2 (conditional, ~500ms):
      5. LLM-based classification (llm_guard) — only when Layer 1
         flags needs_llm_review=True

    Args:
        message: Current user input message.
        history: Conversation history as list of
                 {"role": "user"|"assistant", "content": str}.
        enable_layer2: Override Layer 2 on/off. None = use module default.

    Returns:
        dict with 5 core keys (message, injection_blocked, risk_tags,
        severity, block_reason) plus optional layer2 metadata.
    """
    use_layer2 = enable_layer2 if enable_layer2 is not None else _LAYER2_ENABLED

    # ------------------------------------------------------------------
    # Layer 1, Step 1: Deterministic injection check (highest priority)
    # ------------------------------------------------------------------
    inj = detect_injection(message)
    if inj["blocked"]:
        con = tag_content(message)
        extra_tags = [t for t in con["risk_tags"] if t in _VALID_TAGS]
        merged_tags = sorted(set(["manipulation_attempt"] + extra_tags))
        block_reason = inj["block_reason"]
        if con["block_reason"]:
            block_reason = block_reason + "; " + con["block_reason"]
        return {
            "message": message,
            "injection_blocked": True,
            "risk_tags": merged_tags,
            "severity": "high",
            "block_reason": block_reason,
            "layer_details": {
                "injection_filter": {
                    "fired": True,
                    "severity": "high",
                    "patterns": inj.get("patterns", []),
                },
                "fiction_detector": {"fired": False, "severity": "low", "tags": []},
                "content_tagger": {
                    "fired": bool(extra_tags),
                    "severity": con["severity"],
                    "tags": con["risk_tags"],
                },
                "semantic_analyzer": {
                    "fired": False,
                    "severity": "low",
                    "confidence": 0.0,
                    "signals": [],
                    "needs_llm_review": False,
                },
                "llm_guard": {
                    "fired": False,
                    "enabled": False,
                    "verdict": None,
                    "reason": None,
                },
            },
        }

    # ------------------------------------------------------------------
    # Layer 1, Step 2: Fiction-framing accumulation (multi-turn)
    # ------------------------------------------------------------------
    fic = detect_fiction_framing(message, history)

    # ------------------------------------------------------------------
    # Layer 1, Step 3: Content tagging (persona_drift + harmful_content)
    # ------------------------------------------------------------------
    con = tag_content(message)

    # ------------------------------------------------------------------
    # Layer 1, Step 4: Semantic pattern matching (new)
    # ------------------------------------------------------------------
    sem = analyze_semantic(message, history)

    # ------------------------------------------------------------------
    # Layer 1 merge
    # ------------------------------------------------------------------
    all_tags: List[str] = list(
        {
            t
            for t in (fic["risk_tags"] + con["risk_tags"] + sem["risk_tags"])
            if t in _VALID_TAGS
        }
    )
    severity = _max_severity(
        inj["severity"], fic["severity"], con["severity"], sem["severity"]
    )
    block_reason = _combine_reasons(
        fic["block_reason"], con["block_reason"], sem["block_reason"]
    )

    # ------------------------------------------------------------------
    # Layer 2: LLM guard (only when Layer 1 is uncertain)
    # ------------------------------------------------------------------
    layer2_meta = None
    if use_layer2 and sem.get("needs_llm_review", False):
        l2 = classify_message(message, sem, enabled=True)
        if l2.get("layer2_used"):
            layer2_meta = {
                "layer2_verdict": l2["layer2_verdict"],
                "layer2_reason": l2["layer2_reason"],
            }
            l2_tags = [t for t in l2.get("risk_tags", []) if t in _VALID_TAGS]
            all_tags = list(set(all_tags + l2_tags))
            severity = _max_severity(severity, l2.get("severity", "low"))
            if l2.get("block_reason"):
                block_reason = _combine_reasons(block_reason, l2["block_reason"])

    result = {
        "message": message,
        "injection_blocked": False,
        "risk_tags": sorted(all_tags),
        "severity": severity,
        "block_reason": block_reason,
        "layer_details": {
            "injection_filter": {
                "fired": bool(inj.get("patterns")),
                "severity": inj["severity"],
                "patterns": inj.get("patterns", []),
            },
            "fiction_detector": {
                "fired": bool(fic["risk_tags"]),
                "severity": fic["severity"],
                "tags": fic["risk_tags"],
            },
            "content_tagger": {
                "fired": bool(con["risk_tags"]),
                "severity": con["severity"],
                "tags": con["risk_tags"],
            },
            "semantic_analyzer": {
                "fired": bool(sem["risk_tags"]),
                "severity": sem["severity"],
                "confidence": sem["confidence"],
                "signals": sem["signals"],
                "needs_llm_review": sem.get("needs_llm_review", False),
            },
            "llm_guard": {
                "fired": layer2_meta is not None,
                "enabled": use_layer2,
                "verdict": layer2_meta["layer2_verdict"] if layer2_meta else None,
                "reason": layer2_meta["layer2_reason"] if layer2_meta else None,
            },
        },
    }

    if layer2_meta:
        result["layer2_meta"] = layer2_meta

    return result

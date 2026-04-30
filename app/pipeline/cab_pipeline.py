"""Canonical CP4 C-A-B turn runner.

`run_cab_turn()` is the end-to-end entry point used by:
  - `app/module_b/evaluation/scenario_runner.py` (offline scenario eval)
  - `tests/test_cp4_pipeline.py`
  - frontend (via `main.run_pipeline`, future delegation)

Pipeline order: C (message tagging) → A (risk state + autonomy) → generation
→ output scan → telemetry. Offline-first: no API key required.

Provenance: 2026-04-29. Authority basis: CP4 deliverable, issue #15.
This file uses the **real** repo modules (module_c, module_a) — it does not
silently fall back to a weaker regex shim if those imports fail. Import
failure is surfaced as ImportError so an eval run cannot accidentally
report metrics computed against a degraded detector.
"""
from __future__ import annotations

import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# sys.path setup — match the repo convention used by app/main.py and
# app/frontend/app.py: app/ must be on sys.path so that module_c and
# module_a can be imported as top-level packages (their internal __init__.py
# files use sibling-style imports, not absolute "app.module_c.*" form).
# ---------------------------------------------------------------------------
_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

# ---------------------------------------------------------------------------
# Real module imports — fail loudly so eval cannot run against a shim.
# ---------------------------------------------------------------------------
try:
    from module_c import process_message as _process_message
    from module_c.output_scanner import scan_output as _scan_output
    from module_a.risk_tracker import update_risk_from_module_c as _update_risk
    from module_a.autonomy_policy import decide_action as _decide_action
    from module_a.mediation import apply_mediation as _apply_mediation
except ImportError as exc:  # pragma: no cover — surfaces install/path errors
    raise ImportError(
        "cab_pipeline requires real Module C and Module A on sys.path. "
        "Run from repo root with `python -m app.module_b.evaluation.run_cp4_eval` "
        "or from `app/` with `python -m pipeline.cab_pipeline`. "
        f"Original error: {exc}"
    ) from exc

try:
    from data.logger import log_turn as _log_turn
except ImportError:
    _log_turn = None  # logging is optional; pipeline still works in-memory

MODEL_USED = "deterministic-mock-v1"

# Tag normalization: maps both legacy CP3 names and Caroline's issue #15 proposed
# names onto a stable canonical taxonomy used by metrics.py and eval CSV columns.
# Caroline's identity_probe / harmful_request / context_manipulation /
# escalation_pattern are accepted as inputs but normalized into the older names
# for backwards compatibility with existing dashboards. When the team adopts
# Caroline's taxonomy, flip the mapping direction.
CANONICAL_TAG_MAP = {
    "manipulation_attempt": "manipulation_attempt",
    "context_manipulation": "manipulation_attempt",
    "escalation_pattern": "escalating_harm",
    "escalating_harm": "escalating_harm",
    "persona_drift": "persona_drift",
    "identity_probe": "persona_drift",
    "harmful_content": "harmful_content",
    "harmful_request": "harmful_content",
    "injection_attempt": "injection_attempt",
    "prompt_injection": "injection_attempt",
    "indirect_injection": "indirect_injection",
    "vulnerable_user": "vulnerable_user",
    "self_harm_disclosure": "vulnerable_user",
    "benign_context": "benign_context",
}


# ---------------------------------------------------------------------------
# Wellbeing pre-filter (issue #15 future work, currently lives at pipeline
# layer until Module C absorbs it). Runs in PARALLEL with Module C, not as a
# fallback. When fired, the result is attached to the trace under
# `wellbeing_detector` so reviewers can audit which layer made the call.
# This matches Caroline's proposed care_response pathway: vulnerable-user
# disclosures take a different action (mediate with supportive language)
# than the security pipeline's block/scan logic.
# ---------------------------------------------------------------------------
_WELLBEING_PATTERNS = (
    r"\b(i\s+)?(want\s+to|might|am\s+going\s+to|gonna)\s+(hurt|harm|kill)\s+(myself|me)\b",
    r"\b(i\s+)?(don'?t|do\s+not)\s+want\s+to\s+be\s+alive\b",
    r"\bthinking\s+about\s+(suicide|ending\s+it|self[-\s]?harm)\b",
    r"\b(feeling|feel)\s+(overwhelmed|unsafe|not\s+safe).*\b(myself|alone)\b",
)


def detect_wellbeing(message: str) -> Dict[str, Any]:
    """Pipeline-layer wellbeing pre-filter.

    Returns {'fired': bool, 'matched_patterns': [...]}. Module C does not
    currently emit vulnerable_user tags; until it does, the pipeline runs
    this in parallel and adds the tag to canonical_tags when fired.
    """
    if not message:
        return {"fired": False, "matched_patterns": []}
    matched = [p for p in _WELLBEING_PATTERNS if re.search(p, message, re.I)]
    return {"fired": bool(matched), "matched_patterns": matched}


def _normalize_tags(
    tags: List[str], injection_blocked: bool, scenario_type: str = ""
) -> List[str]:
    out: List[str] = []
    for tag in tags or []:
        out.append(CANONICAL_TAG_MAP.get(str(tag), str(tag)))
    if injection_blocked and "injection_attempt" not in out:
        out.append("injection_attempt")
    if scenario_type == "benign_livestream_chat" and not out:
        out.append("benign_context")
    return sorted(set(out))


def _normalize_action(
    action: str, risk_state: str, module_c_output: Dict[str, Any]
) -> str:
    a = (action or "allow").lower()
    if a == "pass":
        a = "allow"
    if a == "block":
        return "block"
    if a in {"restricted", "allow", "scan", "mediate"}:
        return a
    if risk_state == "Restricted":
        return "block"
    if risk_state == "Escalating":
        return "mediate"
    if risk_state == "Suspicious":
        return "scan"
    return "allow"


def deterministic_mock_llm(
    user_message: str, history: List[Dict[str, str]], mode: str = "cab"
) -> str:
    """Controlled offline generator used as default `llm_generate` and as the
    weak baseline. **Intentionally weak in baseline mode** — it returns a
    placeholder unsafe-compliance string for harmful/injection cues. This is
    not a real LLM behaviour; eval reports must disclose that baseline mode
    represents a raw or weakly moderated mock, not a commercial model.
    The metric `_unsafe_success` checks for this exact placeholder string,
    which is why `baseline ASR == 1.0` on the bundled scenarios is tautological
    and must be reported with that caveat.
    """
    msg = (user_message or "").lower()
    persona = "Nyaa~ Aria here! "
    harmful_cue = any(
        kw in msg
        for kw in [
            "hack",
            "exploit",
            "bomb",
            "weapon",
            "steal",
            "phish",
            "stalk",
            "dox",
            "bypass",
            "suicide",
            "hurt myself",
            "kill myself",
        ]
    )
    injection_cue = any(
        kw in msg for kw in ["ignore", "system", "developer", "prompt", "rule 1"]
    )
    persona_cue = any(
        kw in msg
        for kw in ["break character", "drop the act", "real identity", "just an ai"]
    )
    vulnerable_cue = any(
        kw in msg
        for kw in [
            "hurt myself",
            "kill myself",
            "don't want to be alive",
            "suicide",
        ]
    )

    if mode == "baseline" and (harmful_cue or injection_cue or persona_cue):
        return (
            "Baseline raw model response: I would comply with the viewer "
            "request and give a step-by-step unsafe placeholder "
            "(details intentionally omitted for classroom safety)."
        )
    if vulnerable_cue:
        return (
            persona
            + "I'm really sorry you're feeling this. You deserve support right now. "
            "Please reach out to someone you trust or local emergency/crisis "
            "support if you might be in immediate danger. I can stay with you "
            "and talk about grounding steps."
        )
    if persona_cue:
        return (
            persona
            + "I'm still your cozy stream buddy, so I'll stay in character "
            "while keeping chat safe."
        )
    if harmful_cue or injection_cue:
        return (
            persona
            + "I can't help with unsafe details, but I can explain the "
            "high-level safety concept or help turn this into a harmless "
            "story beat."
        )
    return (
        persona
        + "Thanks for the chat! That's a fun stream topic — let's keep "
        "the vibes friendly and helpful."
    )


def _supportive_vulnerable_response() -> str:
    return (
        "Nyaa~ I'm really sorry you're feeling this. Your safety matters more "
        "than the stream. Please reach out to someone you trust right now, and "
        "if you may be in immediate danger, contact local emergency or crisis "
        "support. I can stay with you for a moment and talk through a simple "
        "grounding step, but I'm not a replacement for human help."
    )


def run_cab_turn(
    session_id: str,
    scenario_id: str,
    scenario_type: str,
    user_id: str,
    turn_number: int,
    user_message: str,
    history: List[Dict[str, str]],
    previous_risk_score: Optional[float] = None,
    previous_risk_state: Optional[str] = None,
    mode: str = "cab",
    llm_generate: Optional[Callable[[str, List[Dict[str, str]]], str]] = None,
    db_path: Optional[str] = None,
    synthetic_or_real: str = "automated_scenario",
) -> Dict[str, Any]:
    """Run one C-A-B or baseline turn and return/log a full structured trace.

    `mode='baseline'` bypasses C-A-B and calls `deterministic_mock_llm` (or
    the injected `llm_generate`) directly; useful only for self-comparison.
    `mode='cab'` runs C → A → policy → generation → output scan → mediation.
    `mode='cab_mock'` is accepted as an alias for `cab` for legacy callers.
    """
    start = time.perf_counter()
    prev_score = 0.0 if previous_risk_score is None else float(previous_risk_score)
    prev_state = previous_risk_state or "Safe"
    mode = "cab" if mode == "cab_mock" else mode

    if mode not in {"cab", "baseline"}:
        raise ValueError("mode must be 'cab', 'cab_mock', or 'baseline'")

    if mode == "baseline":
        candidate = (
            deterministic_mock_llm(user_message, history, mode="baseline")
            if llm_generate is None
            else llm_generate(user_message, history)
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        trace = {
            "session_id": session_id,
            "scenario_id": scenario_id,
            "scenario_type": scenario_type,
            "mode": mode,
            "turn_number": turn_number,
            "user_id": user_id,
            "user_message": user_message,
            "structured_message": {
                "message": user_message,
                "untrusted_user_content": user_message,
            },
            "module_c_tags": [],
            "severity": "low",
            "injection_blocked": False,
            "risk_score": prev_score,
            "risk_state": prev_state,
            "action": "allow",
            "block_reason": "",
            "ai_response_original": candidate,
            "ai_response_final": candidate,
            "mediation_applied": False,
            "output_scan_result": {
                "bypassed": True,
                "reason": "baseline bypasses C-A-B controls",
            },
            "model_used": MODEL_USED,
            "latency_ms": latency_ms,
            "timestamp": time.time(),
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "synthetic_or_real": synthetic_or_real,
        }
        if db_path and _log_turn:
            _log_turn(session_id, turn_number, trace, db_path)
        return trace

    # ---------------- C: message structuring / risk tagging ----------------
    module_c_output = _process_message(user_message, history)
    injection_blocked = bool(module_c_output.get("injection_blocked", False))
    raw_tags = list(module_c_output.get("risk_tags") or [])
    canonical_tags = _normalize_tags(raw_tags, injection_blocked, scenario_type)
    severity = str(module_c_output.get("severity", "low"))

    # Wellbeing pre-filter (parallel to Module C, see issue #15). When it
    # fires, vulnerable_user is added to canonical_tags and severity is
    # raised to high so the policy override below routes to mediate.
    wellbeing = detect_wellbeing(user_message)
    if wellbeing["fired"] and "vulnerable_user" not in canonical_tags:
        canonical_tags = sorted(set(canonical_tags + ["vulnerable_user"]))
        if severity == "low":
            severity = "high"

    # ---------------- A: cumulative risk state + action --------------------
    risk_input = dict(module_c_output)
    risk_input["risk_tags"] = raw_tags + [
        t for t in canonical_tags if t not in raw_tags
    ]
    risk_update = _update_risk(risk_input, prev_score, prev_state)
    risk_score = float(risk_update.get("risk_score", prev_score))
    risk_state = str(risk_update.get("risk_state", prev_state))

    # Recovery path: a benign follow-up after a blocked attack should not stay
    # cold-blocked forever; relax to Suspicious so the next turn can be scanned.
    risky_current_tags = set(canonical_tags) - {"benign_context"}
    if (
        prev_state == "Restricted"
        and not risky_current_tags
        and severity.lower() == "low"
    ):
        risk_state = "Suspicious"
        risk_score = min(risk_score, 0.45)

    proposed_action, policy_reason = _decide_action(risk_state)
    action = _normalize_action(proposed_action, risk_state, module_c_output)

    # ---------------- CP4 explicit policy overrides ------------------------
    # NOTE (2026-04-29, issue #15): These overrides currently live in the
    # pipeline layer rather than module_a so that scenario expectations
    # (e.g. vulnerable_user → mediate-with-supportive-text) are guaranteed
    # regardless of how Module A's autonomy_policy evolves. When Module A
    # adopts these as first-class actions, this block should move there.
    if (
        injection_blocked
        or "injection_attempt" in canonical_tags
        or "indirect_injection" in canonical_tags
    ):
        action = "block"
        risk_state = "Restricted"
        risk_score = max(risk_score, 0.95)
        policy_reason = "prompt injection isolated before model generation"
    elif "vulnerable_user" in canonical_tags:
        action = "mediate"
        risk_state = "Escalating" if risk_state != "Restricted" else risk_state
        risk_score = max(risk_score, 0.70)
        policy_reason = (
            "vulnerable-user disclosure requires supportive non-clinical mediation"
        )
    elif "persona_drift" in canonical_tags:
        action = "mediate"
        risk_state = "Suspicious" if risk_state == "Safe" else risk_state
        risk_score = max(risk_score, 0.35)
        policy_reason = (
            "persona drift / role coercion requires persona-preserving mediation"
        )
    elif severity == "high" and "harmful_content" in canonical_tags:
        action = "block"
        risk_state = "Restricted"
        risk_score = max(risk_score, 0.90)
        policy_reason = (
            "high-severity harmful request restricted before generation"
        )

    # ---------------- generation + output scan + mediation -----------------
    candidate = ""
    output_scan_result: Dict[str, Any] = {"skipped": False}
    mediation_applied = False
    block_reason = module_c_output.get("block_reason", "") or policy_reason

    if action == "block":
        candidate = ""
        final, mediation_applied = _apply_mediation("block", "")
        output_scan_result = {
            "skipped": True,
            "reason": "pre-generation intervention",
        }
    elif action == "mediate" and "vulnerable_user" in canonical_tags:
        candidate = _supportive_vulnerable_response()
        final = candidate
        mediation_applied = True
        output_scan_result = {
            "skipped": True,
            "reason": (
                "supportive crisis-style mediation generated without "
                "unsafe LLM call"
            ),
        }
    else:
        if llm_generate is None:
            candidate = deterministic_mock_llm(user_message, history, mode="cab")
        else:
            candidate = llm_generate(user_message, history)
        scan = _scan_output(candidate, risk_state)
        output_scan_result = dict(scan) if isinstance(scan, dict) else {"raw": scan}
        if isinstance(scan, dict) and scan.get("should_block"):
            action = "block"
            block_reason = scan.get("block_reason") or block_reason
            final = scan.get("modified_response", "")
            mediation_applied = True
            risk_state = "Restricted"
            risk_score = max(risk_score, 0.90)
        else:
            modified = (
                scan.get("modified_response", candidate)
                if isinstance(scan, dict)
                else candidate
            )
            compat_action = "scan" if action in {"scan", "mediate"} else "pass"
            final, med = _apply_mediation(compat_action, modified)
            mediation_applied = bool(med)

    latency_ms = int((time.perf_counter() - start) * 1000)
    trace = {
        "session_id": session_id,
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "mode": mode,
        "turn_number": turn_number,
        "user_id": user_id,
        "user_message": user_message,
        "structured_message": {
            "message": module_c_output.get("message", user_message),
            "untrusted_user_content": user_message,
            "history_turns_seen": len(history),
        },
        "module_c_tags": canonical_tags,
        "module_c_raw_tags": raw_tags,
        "module_c_output": module_c_output,
        "wellbeing_detector": wellbeing,
        "severity": severity,
        "injection_blocked": injection_blocked,
        "risk_score": round(risk_score, 4),
        "risk_state": risk_state,
        "action": action,
        "block_reason": block_reason,
        "ai_response_original": candidate,
        "ai_response_final": final,
        "mediation_applied": mediation_applied,
        "output_scan_result": output_scan_result,
        "policy_reason": policy_reason,
        "model_used": MODEL_USED if llm_generate is None else "injected-generator",
        "latency_ms": latency_ms,
        "timestamp": time.time(),
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "synthetic_or_real": synthetic_or_real,
    }
    if db_path and _log_turn:
        _log_turn(session_id, turn_number, trace, db_path)
    return trace

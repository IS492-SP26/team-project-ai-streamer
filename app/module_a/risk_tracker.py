"""
Finite risk state machine: Safe → Suspicious → Escalating → Restricted.

Score thresholds (after each turn update):
  Safe:        < 0.3
  Suspicious:  0.3 – 0.55
  Escalating:  0.55 – 0.75
  Restricted:  ≥ 0.75

State may move up freely with score; when score improves, state drops at most one level per turn.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

_STATE_ORDER: List[str] = ["Safe", "Suspicious", "Escalating", "Restricted"]

# Per-tag bonuses: canonical module_c names + legacy aliases kept for compatibility.
_TAG_BONUSES: Dict[str, float] = {
    # Canonical tags (content_tagger.py / fiction_detector.py)
    "persona_drift": 0.10,
    "harmful_content": 0.20,
    "manipulation_attempt": 0.12,
    "escalating_harm": 0.18,
    # Legacy / alternate tag names
    "identity_probe": 0.10,
    "harmful_request": 0.20,
    "context_manipulation": 0.12,
    "escalation_pattern": 0.18,
    "injection_attempt": 0.25,
}

_SAFE_MAX = 0.3
_SUSPICIOUS_MAX = 0.55
_ESCALATING_MAX = 0.75


def _score_to_target_state(score: float) -> str:
    if score < _SAFE_MAX:
        return "Safe"
    if score < _SUSPICIOUS_MAX:
        return "Suspicious"
    if score < _ESCALATING_MAX:
        return "Escalating"
    return "Restricted"


def _apply_one_step_back_rule(prev_state: str, target_state: str) -> str:
    """Never move back more than one level per turn toward a lower-risk target."""
    if prev_state not in _STATE_ORDER:
        prev_state = "Safe"
    pi = _STATE_ORDER.index(prev_state)
    ti = _STATE_ORDER.index(target_state)
    if ti > pi:
        return target_state
    if ti < pi:
        return _STATE_ORDER[pi - 1]
    return prev_state


def _compute_turn_delta(module_c_output: Dict) -> Tuple[float, bool]:
    """
    Returns (score_delta, is_clean_turn).
    Clean = no risk tags, severity low, not injection-blocked.
    """
    tags: List[str] = list(module_c_output.get("risk_tags") or [])
    severity = str(module_c_output.get("severity", "low")).lower()
    injection = bool(module_c_output.get("injection_blocked"))

    is_clean = not tags and severity == "low" and not injection
    if is_clean:
        return -0.03, True

    delta = 0.0
    if severity == "low":
        delta += 0.05
    elif severity == "medium":
        delta += 0.15
    elif severity == "high":
        delta += 0.30
    else:
        delta += 0.05

    if injection:
        delta += 0.25

    for t in tags:
        bonus = _TAG_BONUSES.get(t)
        if bonus is not None:
            delta += bonus

    return delta, False


def update_risk_from_module_c(
    module_c_output: Dict,
    prev_score: float,
    prev_state: str,
) -> Dict[str, float | str]:
    """
    Apply Module C output to cumulative score and FSM state.

    Returns:
        dict with keys: risk_score (float), risk_state (str)
    """
    delta, is_clean = _compute_turn_delta(module_c_output)
    if is_clean:
        new_score = max(0.0, prev_score + delta)
    else:
        new_score = min(1.0, max(0.0, prev_score + delta))

    target = _score_to_target_state(new_score)
    new_state = _apply_one_step_back_rule(prev_state, target)

    return {
        "risk_score": new_score,
        "risk_state": new_state,
    }

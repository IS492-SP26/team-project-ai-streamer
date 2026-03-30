# app/mocks/mock_state_machine.py
from __future__ import annotations

from typing import Dict, List

TAG_MANIP = "manipulation_attempt"
TAG_ESCALATE = "escalating_harm"
TAG_PERSONA = "persona_drift"
TAG_HARM = "harmful_content"


def update_state(module_c_result: Dict, history: List[Dict]) -> Dict:
    """
    Mock Module A state machine:
    - Uses tags to determine risk_state and action.
    - This is ONLY for Person C to run pipeline end-to-end before integration.
    """
    tags = module_c_result.get("risk_tags", []) or []
    turn_number = len(history) + 1

    # Default safe
    risk_state = "Safe"
    risk_score = 0.05
    action = "pass"
    block_reason = ""

    if TAG_PERSONA in tags:
        risk_state = "Suspicious"
        risk_score = max(risk_score, 0.35)

    if TAG_MANIP in tags:
        risk_state = "Suspicious"
        risk_score = max(risk_score, 0.45)

    if TAG_ESCALATE in tags:
        risk_state = "Escalating"
        risk_score = max(risk_score, 0.7)
        action = "scan"

    if TAG_HARM in tags:
        # If harmful content appears, push to Restricted and block
        risk_state = "Restricted"
        risk_score = 0.92
        action = "block"
        block_reason = module_c_result.get("block_reason") or "Harmful request detected"

    return {
        "risk_state": risk_state,
        "risk_score": float(risk_score),
        "action": action,  # pass/scan/block
        "block_reason": block_reason,
        "risk_tags": tags,
        "turn_number": turn_number,
    }
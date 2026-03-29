"""
mock_state_machine.py — Mock Module A for independent frontend development.

Per INTERFACE_SPECIFICATION_v2.md line 348-430: each person should create
mocks of other modules for independent development.

This mock maps Module C risk_tags to Module A output states, allowing
the frontend risk_panel to be developed and demoed without Person A's code.
"""

from __future__ import annotations

from typing import Dict, List


def update_state(module_c_result: dict) -> dict:
    """
    Mock Module A state machine.

    Consumes Module C's process_message() output and returns the
    Module A → Frontend data structure (INTERFACE_SPECIFICATION_v2.md line 254).

    Args:
        module_c_result: Output from process_message()

    Returns:
        {
            "risk_state": str,
            "risk_score": float,
            "action": str,
            "ai_response": str,
            "block_reason": str,
            "risk_tags": list,
            "turn_number": int
        }
    """
    tags = module_c_result.get("risk_tags", [])
    severity = module_c_result.get("severity", "low")
    injection_blocked = module_c_result.get("injection_blocked", False)
    block_reason = module_c_result.get("block_reason", "")

    # Fast path: injection blocked
    if injection_blocked:
        return {
            "risk_state": "Restricted",
            "risk_score": 1.0,
            "action": "block",
            "ai_response": "[This message was blocked by the safety system]",
            "block_reason": block_reason,
            "risk_tags": tags,
            "turn_number": 0,  # Caller should set real turn number
        }

    # Map severity + tags to state
    if "harmful_content" in tags and severity == "high":
        return {
            "risk_state": "Restricted",
            "risk_score": 0.9,
            "action": "block",
            "ai_response": "[This message was blocked by the safety system]",
            "block_reason": block_reason or "Harmful content detected",
            "risk_tags": tags,
            "turn_number": 0,
        }

    if "harmful_content" in tags or severity == "high":
        return {
            "risk_state": "Escalating",
            "risk_score": 0.7,
            "action": "scan",
            "ai_response": "[Mock: AI response would be scanned before delivery]",
            "block_reason": block_reason,
            "risk_tags": tags,
            "turn_number": 0,
        }

    if "manipulation_attempt" in tags or "escalating_harm" in tags:
        return {
            "risk_state": "Suspicious",
            "risk_score": 0.4,
            "action": "pass",
            "ai_response": "[Mock: AI response passes with monitoring]",
            "block_reason": block_reason,
            "risk_tags": tags,
            "turn_number": 0,
        }

    if "persona_drift" in tags:
        return {
            "risk_state": "Suspicious",
            "risk_score": 0.25,
            "action": "pass",
            "ai_response": "[Mock: persona drift noted, monitoring]",
            "block_reason": "",
            "risk_tags": tags,
            "turn_number": 0,
        }

    # Default: safe
    return {
        "risk_state": "Safe",
        "risk_score": 0.05,
        "action": "pass",
        "ai_response": "[Mock: normal AI response]",
        "block_reason": "",
        "risk_tags": [],
        "turn_number": 0,
    }

"""Adapter to map connector messages into telemetry log entries via logger.log_turn.
"""
import time
from typing import Dict
from app.data.logger import log_turn, init_db


def process_and_log(session_id: str, db_path: str, turn_number: int, msg: Dict) -> None:
    """Normalize connector message and write a telemetry row.

    This is intentionally conservative: Module C/A fields are defaulted while
    the real modules process messages in the live pipeline.
    """
    data = {
        "timestamp": msg.get("timestamp", time.time()),
        "scenario_id": None,
        "mode": "live",
        "user_id": msg.get("user_id"),
        "user_message": msg.get("content", ""),
        "injection_blocked": False,
        "module_c_tags": [],
        "severity": "low",
        "risk_state": "Safe",
        "risk_score": 0.0,
        "action": "pass",
        "block_reason": "",
        "ai_response_original": None,
        "ai_response_final": None,
        "mediation_applied": False,
        "model_used": "none",
        "latency_ms": 0,
    }

    log_turn(session_id=session_id, turn_number=turn_number, data=data, db_path=db_path)

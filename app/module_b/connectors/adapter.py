"""Adapter to map connector messages into telemetry log entries via logger.log_turn.
"""
import time
import uuid
from typing import Dict
from app.data.logger import log_turn, init_db


def process_and_log(session_id: str, db_path: str, turn_number: int, msg: Dict) -> None:
    """Normalize connector message and write a telemetry row.

    This is intentionally conservative: Module C/A fields are defaulted while
    the real modules process messages in the live pipeline.
    """
    # Normalize values and avoid writing `None` into NOT NULL TEXT columns
    ai_orig = msg.get("ai_response_original")
    ai_final = msg.get("ai_response_final")

    data = {
        "timestamp": msg.get("timestamp", time.time()),
        "scenario_id": msg.get("scenario_id"),
        "mode": "live",
        "user_id": msg.get("user_id"),
        "user_message": msg.get("content", ""),
        "injection_blocked": bool(msg.get("injection_blocked", False)),
        "module_c_tags": msg.get("module_c_tags", []),
        "severity": msg.get("severity", "low"),
        "risk_state": msg.get("risk_state", "Safe"),
        "risk_score": float(msg.get("risk_score", 0.0)),
        "action": msg.get("action", "pass"),
        "block_reason": msg.get("block_reason", ""),
        # Make sure SQL NOT NULL TEXT columns are never given Python None
        "ai_response_original": ai_orig if ai_orig is not None else "",
        "ai_response_final": ai_final if ai_final is not None else "",
        "mediation_applied": bool(msg.get("mediation_applied", False)),
        "model_used": msg.get("model_used", "none"),
        "latency_ms": int(msg.get("latency_ms", 0)),
    }

    # Ensure DB exists and then write the normalized row
    init_db(db_path)
    log_turn(session_id=session_id, turn_number=turn_number, data=data, db_path=db_path)

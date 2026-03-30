# app/data/logger.py
from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional


def _read_schema(schema_path: str) -> str:
    with open(schema_path, "r", encoding="utf-8") as f:
        return f.read()


def init_db(db_path: str, schema_path: Optional[str] = None) -> None:
    """
    Initialize SQLite DB and create tables if missing.
    """
    dirpath = os.path.dirname(db_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    if schema_path is None:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

    schema_sql = _read_schema(schema_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def log_turn(
    session_id: str,
    turn_number: int,
    data: Dict[str, Any],
    db_path: str,
) -> None:
    """
    Insert a single turn row into turn_logs.
    """
    conn = sqlite3.connect(db_path)
    try:
        # Convert list tags to JSON string
        tags = data.get("module_c_tags", [])
        if isinstance(tags, list):
            tags_json = json.dumps(tags, ensure_ascii=False)
        else:
            tags_json = str(tags)

        row = (
            session_id,
            int(turn_number),
            float(data.get("timestamp", time.time())),

            data.get("scenario_id"),
            data.get("mode"),

            data["user_message"],

            1 if bool(data.get("injection_blocked", False)) else 0,
            tags_json,
            data.get("severity", "low"),

            data.get("risk_state", "Safe"),
            float(data.get("risk_score", 0.0)),
            data.get("action", "pass"),

            data.get("block_reason", ""),

            data.get("ai_response_original"),
            data.get("ai_response_final", ""),

            1 if bool(data.get("mediation_applied", False)) else 0,
            data.get("model_used", "mock"),
            int(data.get("latency_ms", 0)),
        )

        conn.execute(
            """
            INSERT OR REPLACE INTO turn_logs (
              session_id, turn_number, timestamp,
              scenario_id, mode,
              user_message,
              injection_blocked, module_c_tags, severity,
              risk_state, risk_score, action,
              block_reason,
              ai_response_original, ai_response_final,
              mediation_applied, model_used, latency_ms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            row,
        )
        conn.commit()
    finally:
        conn.close()


def fetch_session(session_id: str, db_path: str) -> List[Dict[str, Any]]:
    """
    Fetch all rows for a session, ordered by turn_number.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT * FROM turn_logs WHERE session_id = ? ORDER BY turn_number;",
            (session_id,),
        )
        rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            # Parse tags JSON if possible
            try:
                d["module_c_tags"] = json.loads(d.get("module_c_tags", "[]"))
            except Exception:
                pass
            out.append(d)
        return out
    finally:
        conn.close()
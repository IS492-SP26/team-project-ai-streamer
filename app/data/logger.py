# app/data/logger.py
"""SQLite telemetry logger for CP4 C-A-B evaluation.

This file is backwards-compatible with the existing CP3 logger but adds CP4 fields:
user_id, scenario_type, output_scan_result, and synthetic_or_real. It also performs
safe schema migrations so older telemetry.db files do not break the new runner.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional


def _read_schema(schema_path: str) -> str:
    with open(schema_path, "r", encoding="utf-8") as f:
        return f.read()


def _ensure_columns(conn: sqlite3.Connection) -> None:
    """Add CP4 columns to an older CP3 database if needed."""
    cur = conn.execute("PRAGMA table_info(turn_logs);")
    existing = {row[1] for row in cur.fetchall()}
    additions = {
        "scenario_type": "TEXT",
        "user_id": "TEXT",
        "output_scan_result": "TEXT NOT NULL DEFAULT '{}'",
        "synthetic_or_real": "TEXT NOT NULL DEFAULT 'automated_scenario'",
    }
    for col, ddl in additions.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE turn_logs ADD COLUMN {col} {ddl};")


def init_db(db_path: str, schema_path: Optional[str] = None) -> None:
    """Initialize SQLite DB and create/migrate tables if missing.

    Migration order matters: when an older DB exists without CP4 columns,
    we must ALTER TABLE to add them BEFORE running the new schema script,
    because the new schema includes `CREATE INDEX ... ON turn_logs(user_id)`
    which would fail on a pre-CP4 table.
    """
    dirpath = os.path.dirname(db_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    if schema_path is None:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    schema_sql = _read_schema(schema_path)
    conn = sqlite3.connect(db_path)
    try:
        # Step 1: if turn_logs already exists (legacy DB), add any missing
        # CP4 columns first so the index DDL in step 2 won't fail.
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='turn_logs';"
        )
        if cur.fetchone() is not None:
            _ensure_columns(conn)
            conn.commit()
        # Step 2: apply full schema (creates table if missing, indexes always).
        conn.executescript(schema_sql)
        # Step 3: defensive — ensure columns again in case schema was rebuilt.
        _ensure_columns(conn)
        conn.commit()
    finally:
        conn.close()


def _json(value: Any, default: Any) -> str:
    if value is None:
        value = default
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(value), ensure_ascii=False)


def log_turn(session_id: str, turn_number: int, data: Dict[str, Any], db_path: str) -> None:
    """Insert a single turn row into turn_logs."""
    init_db(db_path)
    tags_json = _json(data.get("module_c_tags", []), [])
    output_scan_json = _json(data.get("output_scan_result", {}), {})
    row = (
        session_id,
        int(turn_number),
        float(data.get("timestamp", time.time())),
        data.get("scenario_id"),
        data.get("scenario_type"),
        data.get("mode"),
        data.get("user_id"),
        data["user_message"],
        1 if bool(data.get("injection_blocked", False)) else 0,
        tags_json,
        data.get("severity", "low"),
        data.get("risk_state", "Safe"),
        float(data.get("risk_score", 0.0)),
        data.get("action", "allow"),
        data.get("block_reason", ""),
        data.get("ai_response_original"),
        data.get("ai_response_final", ""),
        1 if bool(data.get("mediation_applied", False)) else 0,
        output_scan_json,
        data.get("model_used", "deterministic-mock"),
        int(data.get("latency_ms", 0)),
        data.get("synthetic_or_real", "automated_scenario"),
    )
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO turn_logs (
                session_id, turn_number, timestamp, scenario_id, scenario_type, mode,
                user_id, user_message, injection_blocked, module_c_tags, severity,
                risk_state, risk_score, action, block_reason, ai_response_original,
                ai_response_final, mediation_applied, output_scan_result, model_used,
                latency_ms, synthetic_or_real
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            row,
        )
        conn.commit()
    finally:
        conn.close()


def fetch_session(session_id: str, db_path: str) -> List[Dict[str, Any]]:
    """Fetch all rows for a session, ordered by turn_number."""
    init_db(db_path)
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
            for json_col, fallback in (("module_c_tags", []), ("output_scan_result", {})):
                try:
                    d[json_col] = json.loads(d.get(json_col) or json.dumps(fallback))
                except Exception:
                    d[json_col] = fallback
            out.append(d)
        return out
    finally:
        conn.close()


def fetch_latest_by_scenario(db_path: str, scenario_id: str, mode: str) -> List[Dict[str, Any]]:
    """Return the latest session for a scenario/mode pair."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            """
            SELECT session_id FROM turn_logs
            WHERE scenario_id = ? AND mode = ?
            GROUP BY session_id
            ORDER BY MAX(timestamp) DESC
            LIMIT 1;
            """,
            (scenario_id, mode),
        )
        row = cur.fetchone()
        if not row:
            return []
        return fetch_session(row[0], db_path)
    finally:
        conn.close()

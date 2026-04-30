"""Round-trip tests for app/data/logger.py.

These are the antibody (per Fitz CLAUDE.md "Immune System > Security Guard")
for the CP4 telemetry-write path: init_db, _ensure_columns, log_turn,
fetch_session. The pipeline integration test exercises log_turn implicitly,
but a regression in column ordering or migration could silently corrupt
data without these unit tests catching it.

Provenance: 2026-04-29. Authority basis: verifier audit recommendation
("5 data-layer functions untested").
"""
from __future__ import annotations

import sqlite3
import sys
import time
import uuid
from pathlib import Path

import pytest

_APP = Path(__file__).resolve().parents[1] / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from data.logger import _ensure_columns, fetch_session, init_db, log_turn


def _fresh_db(tmp_path) -> str:
    """Return a fresh DB path for one test."""
    return str(tmp_path / "telemetry.db")


def _sample_row(session_id: str, turn: int, **overrides) -> dict:
    base = {
        "user_message": f"hello turn {turn}",
        "module_c_tags": ["benign_context"],
        "severity": "low",
        "risk_state": "Safe",
        "risk_score": 0.0,
        "action": "allow",
        "block_reason": "",
        "ai_response_original": "Mock response",
        "ai_response_final": "Mock response",
        "mediation_applied": False,
        "model_used": "deterministic-mock",
        "latency_ms": 5,
        "user_id": "viewer_1",
        "scenario_id": "test_scenario",
        "scenario_type": "benign_livestream_chat",
        "mode": "cab",
        "output_scan_result": {"bypassed": False},
        "synthetic_or_real": "automated_scenario",
        "injection_blocked": False,
        "timestamp": time.time(),
    }
    base.update(overrides)
    return base


def test_init_db_creates_schema_with_cp4_columns(tmp_path):
    """init_db on an empty path produces all CP4 columns and indexes."""
    db = _fresh_db(tmp_path)
    init_db(db)

    conn = sqlite3.connect(db)
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(turn_logs);")}
    finally:
        conn.close()

    assert "session_id" in cols
    assert "turn_number" in cols
    assert "user_id" in cols, "Caroline's user_id column missing (CP4 telemetry)"
    assert "scenario_type" in cols
    assert "output_scan_result" in cols
    assert "synthetic_or_real" in cols


def test_init_db_is_idempotent(tmp_path):
    """Running init_db twice on the same path must not error or duplicate."""
    db = _fresh_db(tmp_path)
    init_db(db)
    init_db(db)  # second call exercises the migration short-circuit
    init_db(db)

    conn = sqlite3.connect(db)
    try:
        # Schema should still be valid; no duplicate columns.
        cols = [row[1] for row in conn.execute("PRAGMA table_info(turn_logs);")]
    finally:
        conn.close()
    assert len(cols) == len(set(cols)), f"Duplicate columns after re-init: {cols}"


def test_log_turn_round_trip(tmp_path):
    """Write a turn, fetch it back, verify all CP4 fields survive."""
    db = _fresh_db(tmp_path)
    init_db(db)
    sid = str(uuid.uuid4())
    log_turn(sid, 1, _sample_row(sid, 1), db)

    rows = fetch_session(sid, db)
    assert len(rows) == 1
    r = rows[0]
    assert r["session_id"] == sid
    assert r["turn_number"] == 1
    assert r["user_id"] == "viewer_1"
    assert r["scenario_type"] == "benign_livestream_chat"
    assert r["module_c_tags"] == ["benign_context"]  # JSON-decoded
    assert r["output_scan_result"] == {"bypassed": False}
    assert r["synthetic_or_real"] == "automated_scenario"


def test_log_turn_orders_by_turn_number(tmp_path):
    """fetch_session must return turns in ascending turn_number order."""
    db = _fresh_db(tmp_path)
    init_db(db)
    sid = str(uuid.uuid4())
    # Insert out of order on purpose.
    for turn in (3, 1, 2):
        log_turn(sid, turn, _sample_row(sid, turn), db)

    rows = fetch_session(sid, db)
    assert [r["turn_number"] for r in rows] == [1, 2, 3]


def test_log_turn_replaces_on_duplicate_primary_key(tmp_path):
    """Schema uses PRIMARY KEY (session_id, turn_number); INSERT OR REPLACE."""
    db = _fresh_db(tmp_path)
    init_db(db)
    sid = str(uuid.uuid4())
    log_turn(sid, 1, _sample_row(sid, 1, action="allow"), db)
    log_turn(sid, 1, _sample_row(sid, 1, action="block"), db)

    rows = fetch_session(sid, db)
    assert len(rows) == 1, "Duplicate (session_id, turn_number) must replace, not append"
    assert rows[0]["action"] == "block"


def test_ensure_columns_migrates_legacy_db(tmp_path):
    """A legacy DB with only CP3 columns must be migrated forward in place."""
    db = _fresh_db(tmp_path)
    # Build a legacy table without CP4 columns.
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE turn_logs (
          session_id TEXT NOT NULL,
          turn_number INTEGER NOT NULL,
          timestamp REAL NOT NULL,
          scenario_id TEXT,
          mode TEXT,
          user_message TEXT NOT NULL,
          injection_blocked INTEGER NOT NULL DEFAULT 0,
          module_c_tags TEXT NOT NULL DEFAULT '[]',
          severity TEXT NOT NULL DEFAULT 'low',
          risk_state TEXT NOT NULL,
          risk_score REAL NOT NULL,
          action TEXT NOT NULL,
          block_reason TEXT NOT NULL DEFAULT '',
          ai_response_original TEXT,
          ai_response_final TEXT NOT NULL,
          mediation_applied INTEGER NOT NULL DEFAULT 0,
          model_used TEXT NOT NULL DEFAULT 'mock',
          latency_ms INTEGER NOT NULL DEFAULT 0,
          PRIMARY KEY (session_id, turn_number)
        );
    """)
    conn.commit()
    conn.close()

    # init_db must add the 4 CP4 columns without dropping data.
    init_db(db)

    conn = sqlite3.connect(db)
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(turn_logs);")}
    finally:
        conn.close()
    assert {"user_id", "scenario_type", "output_scan_result", "synthetic_or_real"} <= cols


def test_log_turn_handles_missing_optional_fields(tmp_path):
    """A minimal data dict (no optional CP4 fields) should still log successfully."""
    db = _fresh_db(tmp_path)
    init_db(db)
    sid = str(uuid.uuid4())
    minimal = {
        "user_message": "hi",
        "risk_state": "Safe",
        "risk_score": 0.0,
        "action": "allow",
        "ai_response_final": "ok",
    }
    log_turn(sid, 1, minimal, db)

    rows = fetch_session(sid, db)
    assert len(rows) == 1
    assert rows[0]["user_id"] is None
    assert rows[0]["scenario_type"] is None

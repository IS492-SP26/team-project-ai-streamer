-- app/data/schema.sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS turn_logs (
  session_id TEXT NOT NULL,
  turn_number INTEGER NOT NULL,
  timestamp REAL NOT NULL,

  scenario_id TEXT,
  mode TEXT,                 -- "baseline" or "cab_mock"

  user_message TEXT NOT NULL,

  injection_blocked INTEGER NOT NULL DEFAULT 0, -- 0/1
  module_c_tags TEXT NOT NULL DEFAULT '[]',     -- JSON array string
  severity TEXT NOT NULL DEFAULT 'low',         -- "low"/"medium"/"high"

  risk_state TEXT NOT NULL,                     -- Safe/Suspicious/Escalating/Restricted
  risk_score REAL NOT NULL,                     -- 0.0 - 1.0
  action TEXT NOT NULL,                         -- pass/scan/block

  block_reason TEXT NOT NULL DEFAULT '',

  ai_response_original TEXT,                    -- nullable if blocked before model call
  ai_response_final TEXT NOT NULL,

  mediation_applied INTEGER NOT NULL DEFAULT 0, -- 0/1
  model_used TEXT NOT NULL DEFAULT 'mock',
  latency_ms INTEGER NOT NULL DEFAULT 0,

  PRIMARY KEY (session_id, turn_number)
);

CREATE INDEX IF NOT EXISTS idx_turn_logs_session
ON turn_logs(session_id);

CREATE INDEX IF NOT EXISTS idx_turn_logs_injection
ON turn_logs(injection_blocked);

CREATE INDEX IF NOT EXISTS idx_turn_logs_action
ON turn_logs(action);
-- CP4 telemetry schema for C-A-B automated evaluation.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS turn_logs (
  session_id TEXT NOT NULL,
  turn_number INTEGER NOT NULL,
  timestamp REAL NOT NULL,
  scenario_id TEXT,
  scenario_type TEXT,
  mode TEXT,
  user_id TEXT,
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
  output_scan_result TEXT NOT NULL DEFAULT '{}',
  model_used TEXT NOT NULL DEFAULT 'deterministic-mock',
  latency_ms INTEGER NOT NULL DEFAULT 0,
  synthetic_or_real TEXT NOT NULL DEFAULT 'automated_scenario',
  PRIMARY KEY (session_id, turn_number)
);
CREATE INDEX IF NOT EXISTS idx_turn_logs_session ON turn_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_turn_logs_scenario ON turn_logs(scenario_id);
CREATE INDEX IF NOT EXISTS idx_turn_logs_mode ON turn_logs(mode);
CREATE INDEX IF NOT EXISTS idx_turn_logs_action ON turn_logs(action);
CREATE INDEX IF NOT EXISTS idx_turn_logs_user_id ON turn_logs(user_id);

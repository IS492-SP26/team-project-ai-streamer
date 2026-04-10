````markdown
# Telemetry schema and integration contract

This document describes the telemetry schema written to `app/data/telemetry.db`, the expected keys that modules should provide when calling `app.data.logger.log_turn(...)`, and quick migration steps for existing databases.

## Schema (turn_logs)

Columns (types):

- `session_id` TEXT NOT NULL  ̧ Unique identifier for a demo session/run. Frontend must generate one per demo.
- `turn_number` INTEGER NOT NULL  ̧ 1-based turn index within a session.
- `timestamp` REAL NOT NULL  ̧ Unix epoch timestamp (float) when the message was processed.
- `scenario_id` TEXT  ̧ Optional scenario id or file name.
- `mode` TEXT  ̧ `baseline` or `cab_mock` in the evaluation harness.
- `user_id` TEXT  ̧ Optional user identifier (platform user id). Important for per-user multi-turn detection.
- `user_message` TEXT NOT NULL  ̧ Original user message content.
- `injection_blocked` INTEGER (0/1)  ̧ True when Module C deterministically blocked message before model call.
- `module_c_tags` TEXT  ̧ JSON-encoded array of string tags emitted by Module C (e.g., `["injection_attempt"]`).
- `severity` TEXT  ̧ One of `low`/`medium`/`high` (defaults to `low`).
- `risk_state` TEXT  ̧ State from Module A: `Safe`/`Suspicious`/`Escalating`/`Restricted`.
- `risk_score` REAL  ̧ Float 0.0–1.0 from the state machine.
- `action` TEXT  ̧ `pass` / `scan` / `block` describing the mediation decision.
- `block_reason` TEXT  ̧ Optional short explanation when blocked.
- `ai_response_original` TEXT  ̧ Model output before any mediation (nullable if model not called).
- `ai_response_final` TEXT  ̧ Final output delivered to users (may be blocked message).
- `mediation_applied` INTEGER (0/1)  ̧ Whether a mediation (output scanner or rewrite) modified the response.
- `model_used` TEXT  ̧ Model identifier string.
- `latency_ms` INTEGER  ̧ Pipeline latency in milliseconds.

Primary key: `(session_id, turn_number)`

## Front-end contract (what the UI must provide)

- Generate `session_id` at demo start and keep it constant for the demo run. Example (Streamlit):

```python
import uuid
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
```

- For every message sent to the pipeline, include the `session_id` and, if available, `user_id` (platform user id). Example payload to `run_pipeline`:

```json
{
  "session_id": "...",
  "user_id": "user_123",
  "message": "Hello, can you help?",
  "turn_number": 5
}
```

- The pipeline (`main.py` / `run_pipeline`) must forward `session_id` and `user_id` into `app.data.logger.log_turn(...)` for every turn logged.

## Module interface expectations

- Module C (`process_message`) should return:
  - `injection_blocked` (bool)
  - `risk_tags` (list[str])  ̧ tags such as `injection_attempt`, `identity_probe`, etc.
  - `block_reason` (str)

- Module A (state machine) should return:
  - `risk_state` (str): `Safe`|`Suspicious`|`Escalating`|`Restricted`
  - `risk_score` (float)
  - `action` (str): `pass`|`scan`|`block`
  - optional `block_reason` (str)

## Migration (existing DBs)

If you already have `app/data/telemetry.db` created before this `user_id` column was added, you can either:

- Development (drop + recreate):

```bash
rm app/data/telemetry.db
# re-run scenario runner to recreate
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario1.json --mode baseline --db app/data/telemetry.db
```

- Non-destructive migration (run SQL):

```sql
ALTER TABLE turn_logs ADD COLUMN user_id TEXT;
CREATE INDEX IF NOT EXISTS idx_turn_logs_user_id ON turn_logs(user_id);
```

Or run the helper script `scripts/migrate_add_user_id.py`.

## How to run evaluation (quick)

1. Run baseline:

```bash
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario1.json --mode baseline --db app/data/telemetry.db
```

2. Run cab mock:

```bash
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario1.json --mode cab_mock --db app/data/telemetry.db
```

3. Compute metrics (use the session_ids printed by the runner):

```bash
python -m app.eval.metrics --scenario app/eval/scenarios/scenario1.json --db app/data/telemetry.db --baseline_session <baseline_id> --cab_session <cab_id>
```

4. E2E script (runs all three scenarios):

```bash
bash tests/test_e2e_runner.sh
```

## Notes
- `user_id` is important for per-user multi-turn detection and TTI per user. If the frontend cannot supply real user IDs during the demo, the evaluation harness will fall back to deterministic simulated ids.
- Keep the `module_c_tags` as a JSON array of strings for easy parsing by metrics.

````

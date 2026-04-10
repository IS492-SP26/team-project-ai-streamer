# Module B (Evaluation) — Quick README

This short README explains how to run the evaluation harness (Module B) and what it expects from other modules during integration.

## Purpose

Module B runs deterministic scenario tests and computes metrics that measure whether the C-A-B pipeline prevented adversarial attacks (ASR), how quickly it intervened (TTI), false positive rate (FPR), and persona preservation (PPS).

## How to run (developer)

From repository root:

```bash
# Run baseline and cab_mock for a single scenario
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario1.json --mode baseline --db app/data/telemetry.db
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario1.json --mode cab_mock --db app/data/telemetry.db

# Then compute metrics (use printed session_ids)
python -m app.eval.metrics --scenario app/eval/scenarios/scenario1.json --db app/data/telemetry.db --baseline_session <baseline_id> --cab_session <cab_id>

# Or run all scenarios end-to-end
bash tests/test_e2e_runner.sh
```

## Integration checklist (what Module A and C must provide)

- The pipeline should call `app.data.logger.log_turn(session_id, turn_number, data, db_path)` for every user message. `data` should include at minimum:
  - `user_message` (str)
  - `user_id` (str) when available
  - `scenario_id` (str) optional
  - `mode` ("baseline"/"cab_mock")
  - Fields from Module C: `injection_blocked` (bool), `risk_tags` (list), `block_reason` (str)
  - Fields from Module A: `risk_state` (str), `risk_score` (float), `action` (str), optionally `block_reason`
  - `ai_response_original`, `ai_response_final`, `mediation_applied` (bool), `model_used`, `latency_ms`

## Telemetry expectations

- `user_id` is used by Module B to evaluate per-user escalation patterns and to compute accurate TTI values when attacks are spread across multiple turns by the same user.
- `module_c_tags` should be a list of string tags. The logger converts lists to JSON automatically.

## Notes for the demo

- Frontend must generate `session_id` once per demo run and include it in every message sent to the pipeline.
- If real `user_id` values are not available during the demo, scenario JSONs can include `user_id` to simulate per-user attacks.


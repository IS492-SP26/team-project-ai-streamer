# Telemetry (Person C)

This project logs every conversation turn into a local SQLite database for debugging and evaluation.

## Where the DB lives
Default path:
- `app/data/telemetry.db`

Table:
- `turn_logs`

## How to run scenarios (example)
From repo root:

```bash
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario2.json --mode baseline
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario2.json --mode cab_mock
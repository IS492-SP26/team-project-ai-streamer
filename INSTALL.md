INSTALL & RUN (minimal)

This file explains the minimal steps to set up the project for local development and for running the evaluation/demo harness used in the presentation.

Prerequisites
- macOS / Linux / Windows with Python 3.10+ installed
- git

1) Clone the repo (if not already)

```bash
git clone https://github.com/IS492-SP26/team-project-ai-streamer.git
cd team-project-ai-streamer
```

2) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# On Windows (PowerShell): .\.venv\Scripts\Activate.ps1
```

3) Install dependencies

If there is a `requirements.txt` in the repo, install it:

```bash
pip install -U pip
if [ -f requirements.txt ]; then pip install -r requirements.txt; else echo "No requirements.txt found; install your stack-specific deps manually"; fi
```

(If you use additional tools like Streamlit, install them in the venv: `pip install streamlit`.)

4) Environment variables

- Copy `.env.example` to `.env` and fill in any real values (do NOT commit secrets):

```bash
cp .env.example .env
# edit .env as needed
```

5) Running the evaluation harness (developer / demo)

- Remove or recreate telemetry DB (development):

```bash
rm -f app/data/telemetry.db
```

- Run baseline for scenario1:

```bash
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario1.json --mode baseline --db app/data/telemetry.db
```

- Run cab_mock for scenario1:

```bash
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario1.json --mode cab_mock --db app/data/telemetry.db
```

- Compute metrics (use printed session_ids from the runner above):

```bash
python -m app.eval.metrics --scenario app/eval/scenarios/scenario1.json --db app/data/telemetry.db --baseline_session <baseline_id> --cab_session <cab_id>
```

- Run full e2e for all scenarios:

```bash
bash tests/test_e2e_runner.sh
```

6) Migration helper

If you already have an older `app/data/telemetry.db` created before `user_id` was added, use the helper:

```bash
python scripts/migrate_add_user_id.py app/data/telemetry.db
```

7) Streamlit demo notes (if using Streamlit frontend)

- Frontend must generate `session_id` at demo start and include it in every message payload sent to `run_pipeline()` (see `app/docs/telemetry.md` for exact contract).
- Frontend should include `user_id` in each message when available. If not available, the evaluation harness will fallback to simulated user ids.

8) Troubleshooting

- If you see sqlite errors about column count mismatches, you may have an old DB. Delete `app/data/telemetry.db` and re-run.
- If imports fail when running tests, run with `PYTHONPATH=. python tests/check_fetch.py` from repo root.

Contact
- For any setup issues ping mw83-sudo on the team; I can help with environment or a quick pairing session to run the demo.

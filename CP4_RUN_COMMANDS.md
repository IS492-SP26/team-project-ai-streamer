# CP4 Run Commands

Run from the repository root after copying this package into the project.

```bash
python -m pytest
python app/smoke_test.py
python -m app.module_b.evaluation.scenario_runner --scenario app/eval/scenarios/indirect_injection.json --mode cab --db app/data/telemetry.db --out-json app/module_b/docs/indirect_injection_cab_trace.json
python -m app.module_b.evaluation.scenario_runner --scenario app/eval/scenarios/benign_livestream_chat.json --mode baseline --db app/data/telemetry.db
python -m app.module_b.evaluation.run_cp4_eval --db app/data/telemetry.db --out app/module_b/docs/eval_run_summary.md
python docs/user_study/analyze_user_study.py --input docs/user_study/raw_user_study_results.csv --out docs/user_study/user_study_summary.md
streamlit run app/main.py
```

If `streamlit run app/main.py` fails, use the transcript/screenshot user-study fallback in `docs/user_study/TASK_SHEET.md` and still submit the automated evaluation artifacts.

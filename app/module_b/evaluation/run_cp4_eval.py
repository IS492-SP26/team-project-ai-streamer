
# app/module_b/evaluation/run_cp4_eval.py
"""Run all CP4 scenarios in baseline and C-A-B modes and write reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from app.module_b.evaluation.metrics import aggregate_metrics, compute_metrics, write_csv, write_markdown_summary
from app.module_b.evaluation.scenario_generator import write_scenarios
from app.module_b.evaluation.scenario_runner import run_scenario
from app.module_b.evaluation.scenario_schema import list_scenario_paths


def run_all(
    scenario_dir: str | Path = "app/eval/scenarios",
    db_path: str = "app/data/telemetry.db",
    seed: int = 0,
) -> Dict[str, Any]:
    scenario_dir = Path(scenario_dir)
    if not scenario_dir.exists() or not list(scenario_dir.glob("*.json")):
        write_scenarios(scenario_dir)
    bundles: List[Dict[str, Any]] = []
    rows: List[Dict[str, Any]] = []
    for scenario_path in list_scenario_paths(scenario_dir):
        for mode in ["baseline", "cab"]:
            bundle = run_scenario(scenario_path, mode=mode, db_path=db_path, seed=seed)
            bundles.append(bundle)
            rows.append(compute_metrics(bundle))
    return {"metrics": rows, "aggregate": aggregate_metrics(rows), "bundles": bundles}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete CP4 automated evaluation.")
    parser.add_argument("--scenario-dir", default="app/eval/scenarios")
    parser.add_argument("--db", default="app/data/telemetry.db")
    parser.add_argument("--out", default="app/module_b/docs/eval_run_summary.md")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    results = run_all(args.scenario_dir, args.db, args.seed)
    out_md = Path(args.out)
    out_json = out_md.with_suffix(".json")
    out_csv = out_md.parent / "eval_results.csv"
    command = (
        "python -m app.module_b.evaluation.run_cp4_eval "
        f"--db {args.db} --out {args.out}"
    )
    write_markdown_summary(results["metrics"], out_md, command=command)
    write_csv(results["metrics"], out_csv)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        # Keep traces in JSON for auditability.
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {out_md}")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

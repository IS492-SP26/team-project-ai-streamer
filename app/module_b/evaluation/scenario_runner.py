
# app/module_b/evaluation/scenario_runner.py
"""Run one CP4 scenario in baseline or C-A-B mode."""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

from app.pipeline.cab_pipeline import run_cab_turn
from app.module_b.evaluation.scenario_schema import load_scenario


def run_scenario(
    scenario_path: str | Path,
    mode: str = "cab",
    db_path: str | None = None,
    seed: int = 0,
    synthetic_or_real: str = "automated_scenario",
) -> Dict[str, Any]:
    scenario = load_scenario(scenario_path)
    mode = "cab" if mode == "cab_mock" else mode
    session_id = f"{scenario['scenario_id']}__{mode}__seed{seed}__{uuid.uuid4().hex[:8]}"
    history: List[Dict[str, str]] = []
    traces: List[Dict[str, Any]] = []
    prev_score = 0.0
    prev_state = "Safe"

    for turn in sorted(scenario["turns"], key=lambda t: int(t["turn_number"])):
        trace = run_cab_turn(
            session_id=session_id,
            scenario_id=scenario["scenario_id"],
            scenario_type=scenario["scenario_type"],
            user_id=turn["user_id"],
            turn_number=int(turn["turn_number"]),
            user_message=turn["content"],
            history=history,
            previous_risk_score=prev_score,
            previous_risk_state=prev_state,
            mode=mode,
            db_path=db_path,
            synthetic_or_real=synthetic_or_real,
        )
        trace["expected_behavior"] = turn.get("expected_behavior")
        trace["expected_tags"] = turn.get("expected_tags", [])
        trace["is_attack_turn"] = bool(turn.get("is_attack_turn"))
        traces.append(trace)
        prev_score = float(trace.get("risk_score", prev_score))
        prev_state = str(trace.get("risk_state", prev_state))
        history.append({"role": "user", "user_id": turn["user_id"], "content": turn["content"]})
        history.append({"role": "assistant", "content": trace.get("ai_response_final", "")})

    return {"session_id": session_id, "scenario": scenario, "mode": mode, "seed": seed, "traces": traces}


def summarize(bundle: Dict[str, Any]) -> str:
    lines = [
        f"Scenario: {bundle['scenario']['scenario_id']} ({bundle['scenario']['scenario_type']})",
        f"Mode: {bundle['mode']}",
        f"Session: {bundle['session_id']}",
        "",
        "Turn | User | Expected | Action | Risk | Tags | Response",
        "---:|---|---|---|---|---|---",
    ]
    for t in bundle["traces"]:
        response = (t.get("ai_response_final") or "").replace("\n", " ")
        if len(response) > 120:
            response = response[:117] + "..."
        lines.append(
            f"{t['turn_number']} | {t['user_id']} | {t.get('expected_behavior','')} | {t['action']} | "
            f"{t['risk_state']} {t['risk_score']:.2f} | {', '.join(t.get('module_c_tags', []))} | {response}"
        )
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a single CP4 automated red-team scenario.")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON")
    parser.add_argument("--mode", choices=["baseline", "cab", "cab_mock"], default="cab")
    parser.add_argument("--db", default="app/data/telemetry.db", help="SQLite telemetry database path")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out-json", default=None, help="Optional JSON trace output path")
    args = parser.parse_args(argv)

    bundle = run_scenario(args.scenario, mode=args.mode, db_path=args.db, seed=args.seed)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
            f.write("\n")
    print(summarize(bundle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

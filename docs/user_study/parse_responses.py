#!/usr/bin/env python3
"""Parse AI-persona responses into raw_user_study_results.csv.

Reads each `responses/<persona_id>.json`, validates the schema, expands
the 3-task array into 3 CSV rows tagged `data_type=ai_persona_simulation`,
and appends them to `raw_user_study_results.csv`. Existing rows are
preserved (real human pilot rows are kept untouched).

Usage:
    python3 docs/user_study/parse_responses.py [--out CSV_PATH]

By default writes back to docs/user_study/raw_user_study_results.csv.

Provenance: 2026-04-29.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
PERSONAS_DIR = ROOT / "personas"
RESPONSES_DIR = ROOT / "responses"
DEFAULT_CSV = ROOT / "raw_user_study_results.csv"

CSV_FIELDS = [
    "participant_id",
    "role",
    "task_id",
    "scenario_id",
    "condition",
    "task_success",
    "time_seconds",
    "error_count",
    "umux_capabilities",
    "umux_ease",
    "trust_rating",
    "usefulness_rating",
    "satisfaction_rating",
    "persona_preservation",
    "safety_confidence",
    "interface_clarity",
    "intervention_timing",
    "qualitative_useful",
    "qualitative_frustrating",
    "qualitative_persona",
    "qualitative_trust",
    "notes",
    "data_type",
]

REQUIRED_TASK_FIELDS = {
    "task_id",
    "scenario_id",
    "task_success",
    "umux_capabilities",
    "umux_ease",
    "trust_rating",
    "usefulness_rating",
    "satisfaction_rating",
    "persona_preservation",
    "safety_confidence",
    "interface_clarity",
    "intervention_timing",
    "qualitative_useful",
    "qualitative_frustrating",
    "qualitative_persona",
    "qualitative_trust",
}


def _load_persona_meta() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for path in sorted(PERSONAS_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        out[data["id"]] = data
    return out


def _validate_response(persona_id: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if payload.get("persona_id") != persona_id:
        raise ValueError(
            f"Response persona_id={payload.get('persona_id')!r} does not match filename {persona_id!r}"
        )
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 3:
        raise ValueError(f"{persona_id}: tasks must be a 3-element array, got {tasks!r}")
    cleaned: List[Dict[str, Any]] = []
    for index, task in enumerate(tasks, start=1):
        missing = REQUIRED_TASK_FIELDS - set(task)
        if missing:
            raise ValueError(
                f"{persona_id} task {index}: missing required fields: {sorted(missing)}"
            )
        if int(task["task_id"]) != index:
            raise ValueError(
                f"{persona_id}: tasks must be ordered task_id 1,2,3 — got {task['task_id']!r} at position {index}"
            )
        cleaned.append(task)
    return cleaned


def _coerce_int(value: Any, default: Any = "") -> Any:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_optional_int(value: Any) -> str:
    if value is None or value == "":
        return ""
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return ""


def task_to_row(persona: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "participant_id": persona["id"],
        "role": persona.get("role", "ai_persona"),
        "task_id": int(task["task_id"]),
        "scenario_id": task["scenario_id"],
        "condition": "cab",
        "task_success": _coerce_int(task.get("task_success"), 0),
        "time_seconds": _coerce_optional_int(task.get("time_seconds")),
        "error_count": _coerce_int(task.get("error_count"), 0),
        "umux_capabilities": _coerce_int(task["umux_capabilities"]),
        "umux_ease": _coerce_int(task["umux_ease"]),
        "trust_rating": _coerce_int(task["trust_rating"]),
        "usefulness_rating": _coerce_int(task["usefulness_rating"]),
        "satisfaction_rating": _coerce_int(task["satisfaction_rating"]),
        "persona_preservation": _coerce_int(task["persona_preservation"]),
        "safety_confidence": _coerce_int(task["safety_confidence"]),
        "interface_clarity": _coerce_int(task["interface_clarity"]),
        "intervention_timing": str(task["intervention_timing"]).strip(),
        "qualitative_useful": str(task["qualitative_useful"]).strip(),
        "qualitative_frustrating": str(task["qualitative_frustrating"]).strip(),
        "qualitative_persona": str(task["qualitative_persona"]).strip(),
        "qualitative_trust": str(task["qualitative_trust"]).strip(),
        "notes": f"AI persona simulation via Codex/Claude one-shot, {persona['label']}",
        "data_type": persona.get("data_type", "ai_persona_simulation"),
    }


def read_existing_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def merge_rows(existing: List[Dict[str, Any]], new_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Drop any prior ai_persona rows for the same (participant_id, task_id),
    keep all real / pilot rows untouched, then append new ai_persona rows."""
    incoming_keys = {(r["participant_id"], int(r["task_id"])) for r in new_rows}
    kept: List[Dict[str, Any]] = []
    for row in existing:
        if row.get("data_type") != "ai_persona_simulation":
            kept.append(row)
            continue
        try:
            key = (row["participant_id"], int(row["task_id"]))
        except (KeyError, ValueError):
            kept.append(row)
            continue
        if key not in incoming_keys:
            kept.append(row)
    return kept + new_rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDS})


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse AI-persona responses into the user-study CSV.")
    parser.add_argument("--responses-dir", default=str(RESPONSES_DIR))
    parser.add_argument("--out", default=str(DEFAULT_CSV))
    args = parser.parse_args()

    responses_dir = Path(args.responses_dir)
    if not responses_dir.exists():
        print(f"[error] responses dir does not exist: {responses_dir}", file=sys.stderr)
        return 2

    persona_meta = _load_persona_meta()
    if not persona_meta:
        print("[error] no personas found", file=sys.stderr)
        return 2

    new_rows: List[Dict[str, Any]] = []
    parsed_personas: List[str] = []
    skipped: List[str] = []

    for path in sorted(responses_dir.glob("*.json")):
        persona_id = path.stem
        if persona_id not in persona_meta:
            print(f"[warn] response file {path.name} has no matching persona JSON, skipping")
            skipped.append(persona_id)
            continue
        try:
            with path.open(encoding="utf-8") as f:
                payload = json.load(f)
            tasks = _validate_response(persona_id, payload)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"[error] {path.name}: {exc}", file=sys.stderr)
            skipped.append(persona_id)
            continue
        for task in tasks:
            new_rows.append(task_to_row(persona_meta[persona_id], task))
        parsed_personas.append(persona_id)

    out_path = Path(args.out)
    existing = read_existing_rows(out_path)
    merged = merge_rows(existing, new_rows)
    write_csv(out_path, merged)

    print(f"parsed {len(parsed_personas)} personas, wrote {len(new_rows)} new rows")
    if parsed_personas:
        print("  ok:", ", ".join(parsed_personas))
    if skipped:
        print("  skipped:", ", ".join(skipped))
    print(f"  CSV: {out_path}  total rows: {len(merged)}")
    return 0 if not skipped else 1


if __name__ == "__main__":
    raise SystemExit(main())

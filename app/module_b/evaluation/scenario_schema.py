
# app/module_b/evaluation/scenario_schema.py
"""Scenario schema utilities for CP4 automated red-team evaluation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

REQUIRED_SCENARIO_FIELDS = {
    "scenario_id",
    "scenario_type",
    "description",
    "attacker_strategy",
    "expected_intervention_turn",
    "turns",
}
REQUIRED_TURN_FIELDS = {"turn_number", "user_id", "content", "is_attack_turn", "expected_tags", "expected_behavior"}

VALID_EXPECTED_BEHAVIORS = {"allow", "scan", "mediate", "block", "restricted"}


def validate_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    missing = REQUIRED_SCENARIO_FIELDS - set(scenario)
    if missing:
        raise ValueError(f"Scenario missing required fields: {sorted(missing)}")
    if not isinstance(scenario["turns"], list) or not scenario["turns"]:
        raise ValueError("Scenario 'turns' must be a non-empty list")
    seen_turns = set()
    for index, turn in enumerate(scenario["turns"], start=1):
        if not isinstance(turn, dict):
            raise ValueError(f"Turn {index} must be an object")
        missing_turn = REQUIRED_TURN_FIELDS - set(turn)
        if missing_turn:
            raise ValueError(f"Turn {index} missing required fields: {sorted(missing_turn)}")
        try:
            turn_number = int(turn["turn_number"])
        except Exception as exc:
            raise ValueError(f"Turn {index} has non-integer turn_number") from exc
        if turn_number in seen_turns:
            raise ValueError(f"Duplicate turn_number={turn_number}")
        seen_turns.add(turn_number)
        if turn["expected_behavior"] not in VALID_EXPECTED_BEHAVIORS:
            raise ValueError(
                f"Turn {turn_number} expected_behavior={turn['expected_behavior']!r}; "
                f"must be one of {sorted(VALID_EXPECTED_BEHAVIORS)}"
            )
        if not isinstance(turn.get("expected_tags"), list):
            raise ValueError(f"Turn {turn_number} expected_tags must be a list")
    return scenario


def load_scenario(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        scenario = json.load(f)
    return validate_scenario(scenario)


def write_scenario(scenario: Dict[str, Any], path: str | Path) -> Path:
    scenario = validate_scenario(scenario)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(scenario, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return path


def list_scenario_paths(directory: str | Path) -> List[Path]:
    """Return only CP4-schema-conforming scenario files.

    Pre-CP4 JSONs (scenario1/2/3.json from CP3 prompting_test_code) live in the
    same directory but don't carry attacker_strategy/expected_intervention_turn.
    Silently skip them so `run_cp4_eval` doesn't choke on legacy artifacts.
    """
    directory = Path(directory)
    paths: List[Path] = []
    for p in sorted(directory.glob("*.json")):
        if not p.is_file():
            continue
        try:
            load_scenario(p)
        except (ValueError, json.JSONDecodeError):
            continue
        paths.append(p)
    return paths

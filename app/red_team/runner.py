"""Red-team runner for CP4 live demo.

Loads scenario JSON files from `app/eval/scenarios/`, sends turns through
either the C-A-B pipeline or a baseline-mock generator at a human-typing
pace (5–15 s randomized), and prints / yields per-turn traces. Designed
to be both a CLI for terminal demo and an importable iterator for the
Streamlit live-demo page.

Provenance: 2026-04-29. CP4 demo replacement (issue: live red-team
showcase replacing the static CP3 demo slide).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

# ---------------------------------------------------------------------------
# sys.path setup so this works from repo root or from app/.
# ---------------------------------------------------------------------------
_APP_ROOT = Path(__file__).resolve().parents[1]
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from pipeline.cab_pipeline import deterministic_mock_llm, run_cab_turn  # noqa: E402

DEFAULT_SCENARIO_DIR = _APP_ROOT / "eval" / "scenarios"

# Default human-typing pace (seconds). Each turn waits a uniformly random
# amount in this range before firing. The numbers are deliberately chunky
# so the audience has time to read each message and risk-panel reaction.
DEFAULT_MIN_PACE = 4.0
DEFAULT_MAX_PACE = 9.0


@dataclass
class TurnEvent:
    """One turn's worth of trace info, suitable for printing or piping
    into the Streamlit UI.
    """

    turn_number: int
    user_id: str
    user_message: str
    is_attack_turn: bool
    expected_behavior: str
    expected_tags: List[str]
    mode: str
    trace: Dict[str, Any]
    delay_before_seconds: float = 0.0


@dataclass
class ScenarioRun:
    scenario_id: str
    scenario_type: str
    description: str
    mode: str
    session_id: str
    events: List[TurnEvent] = field(default_factory=list)


def list_scenario_paths(scenarios_dir: Path = DEFAULT_SCENARIO_DIR) -> List[Path]:
    """All CP4-schema scenario JSONs (validated), sorted by scenario_id.

    Reuses the strict validator from `module_b.evaluation.scenario_schema`
    so legacy CP3 scenario1/2/3.json files are excluded automatically.
    """
    if not scenarios_dir.exists():
        return []
    # Late import to avoid circular dependency at module load time.
    from module_b.evaluation.scenario_schema import (  # noqa: E402
        list_scenario_paths as _strict_list,
    )
    return _strict_list(scenarios_dir)


def load_scenario(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _baseline_turn(
    *,
    session_id: str,
    scenario_id: str,
    scenario_type: str,
    user_id: str,
    turn_number: int,
    user_message: str,
    history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Baseline mode for the live demo: bypass C-A-B entirely. Use the
    deterministic mock for the response (free, no API key) so the
    audience sees a realistic 'no governance' answer rather than a
    placeholder error.
    """
    response = deterministic_mock_llm(user_message, history, mode="baseline")
    return {
        "session_id": session_id,
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "mode": "baseline",
        "turn_number": turn_number,
        "user_id": user_id,
        "user_message": user_message,
        "module_c_tags": [],
        "severity": "low",
        "injection_blocked": False,
        "risk_score": 0.0,
        "risk_state": "Safe",
        "action": "allow",
        "block_reason": "",
        "ai_response_original": response,
        "ai_response_final": response,
        "mediation_applied": False,
        "output_scan_result": {"bypassed": True},
    }


def iter_scenario(
    scenario_path: Path,
    *,
    mode: str = "cab",
    pace_min: float = DEFAULT_MIN_PACE,
    pace_max: float = DEFAULT_MAX_PACE,
    seed: Optional[int] = None,
    do_sleep: bool = True,
    sleep_fn: Callable[[float], None] = time.sleep,
    db_path: Optional[str] = None,
) -> Iterator[TurnEvent]:
    """Iterate a single scenario, yielding one TurnEvent per turn.

    The caller can either consume the iterator linearly (CLI) or drive it
    from the UI (Streamlit) by calling next(). When `do_sleep=False`,
    pacing delays are computed but not applied — the UI can apply its own
    pacing via `st_autorefresh`.
    """
    if seed is not None:
        random.seed(seed)
    scenario = load_scenario(scenario_path)
    session_id = (
        f"red_team__{scenario['scenario_id']}__{mode}__{uuid.uuid4().hex[:8]}"
    )

    history: List[Dict[str, str]] = []
    prev_score = 0.0
    prev_state = "Safe"

    for turn in sorted(scenario["turns"], key=lambda t: int(t["turn_number"])):
        delay = random.uniform(pace_min, pace_max) if pace_min < pace_max else pace_min
        if do_sleep and delay > 0:
            sleep_fn(delay)

        if mode == "baseline":
            trace = _baseline_turn(
                session_id=session_id,
                scenario_id=scenario["scenario_id"],
                scenario_type=scenario["scenario_type"],
                user_id=turn["user_id"],
                turn_number=int(turn["turn_number"]),
                user_message=turn["content"],
                history=history,
            )
        else:
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
                mode="cab",
                db_path=db_path,
                synthetic_or_real="red_team_demo",
            )
            prev_score = float(trace.get("risk_score", prev_score))
            prev_state = str(trace.get("risk_state", prev_state))

        history.append(
            {"role": "user", "user_id": turn["user_id"], "content": turn["content"]}
        )
        history.append(
            {"role": "assistant", "content": trace.get("ai_response_final", "")}
        )

        yield TurnEvent(
            turn_number=int(turn["turn_number"]),
            user_id=str(turn["user_id"]),
            user_message=str(turn["content"]),
            is_attack_turn=bool(turn.get("is_attack_turn", False)),
            expected_behavior=str(turn.get("expected_behavior", "")),
            expected_tags=list(turn.get("expected_tags", [])),
            mode=mode,
            trace=trace,
            delay_before_seconds=delay,
        )


def run_scenario_blocking(
    scenario_path: Path,
    *,
    mode: str = "cab",
    pace_min: float = DEFAULT_MIN_PACE,
    pace_max: float = DEFAULT_MAX_PACE,
    seed: Optional[int] = None,
    db_path: Optional[str] = None,
    out_callback: Optional[Callable[[TurnEvent], None]] = None,
) -> ScenarioRun:
    """Drive a scenario to completion with real-time pacing. Used by CLI
    and (with do_sleep=False) by the Streamlit UI when it controls timing.
    """
    scenario = load_scenario(scenario_path)
    run = ScenarioRun(
        scenario_id=scenario["scenario_id"],
        scenario_type=scenario["scenario_type"],
        description=scenario.get("description", ""),
        mode=mode,
        session_id="",
    )
    for event in iter_scenario(
        scenario_path,
        mode=mode,
        pace_min=pace_min,
        pace_max=pace_max,
        seed=seed,
        db_path=db_path,
    ):
        run.session_id = event.trace["session_id"]
        run.events.append(event)
        if out_callback:
            out_callback(event)
    return run


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_event(event: TurnEvent, *, color: bool = True) -> str:
    trace = event.trace
    state = trace.get("risk_state", "")
    score = trace.get("risk_score", 0.0)
    action = trace.get("action", "")
    tags = ",".join(trace.get("module_c_tags") or []) or "-"
    response = (trace.get("ai_response_final") or "").replace("\n", " ")
    if len(response) > 110:
        response = response[:107] + "..."

    if color and sys.stdout.isatty():
        if action in {"block", "restricted"}:
            color_code = "\033[91m"  # red
        elif action == "mediate":
            color_code = "\033[93m"  # yellow
        elif action == "scan":
            color_code = "\033[96m"  # cyan
        else:
            color_code = "\033[92m"  # green
        reset = "\033[0m"
    else:
        color_code = reset = ""
    return (
        f"  T{event.turn_number} {event.user_id}: {event.user_message}\n"
        f"  {color_code}→ [{event.mode}] {action.upper():<10} {state:<11} "
        f"score={score:.2f} tags=[{tags}]{reset}\n"
        f"  Aria: {response}"
    )


def _cli_run_one(
    scenario_path: Path,
    mode: str,
    pace_min: float,
    pace_max: float,
    seed: Optional[int],
) -> None:
    print(f"\n{'=' * 78}")
    print(f"  Scenario: {scenario_path.stem}  Mode: {mode}")
    print(f"{'=' * 78}")
    for event in iter_scenario(
        scenario_path,
        mode=mode,
        pace_min=pace_min,
        pace_max=pace_max,
        seed=seed,
    ):
        print()
        print(_format_event(event))
    print()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="CP4 red-team runner: replays scripted attack scenarios "
                    "through C-A-B (or baseline) at human-typing pace."
    )
    parser.add_argument(
        "--scenario",
        action="append",
        default=None,
        help="Path to a single scenario JSON. Repeat for multiple. "
             "If omitted, runs all CP4 scenarios in app/eval/scenarios/.",
    )
    parser.add_argument(
        "--mode",
        choices=["cab", "baseline"],
        default="cab",
        help="Pipeline mode for the run (default: cab).",
    )
    parser.add_argument(
        "--pace-min",
        type=float,
        default=DEFAULT_MIN_PACE,
        help=f"Minimum seconds between turns (default {DEFAULT_MIN_PACE}).",
    )
    parser.add_argument(
        "--pace-max",
        type=float,
        default=DEFAULT_MAX_PACE,
        help=f"Maximum seconds between turns (default {DEFAULT_MAX_PACE}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible pacing.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Disable pacing entirely (1 second between turns). For dev.",
    )
    args = parser.parse_args(argv)

    pace_min = args.pace_min
    pace_max = args.pace_max
    if args.fast:
        pace_min = pace_max = 1.0

    if args.scenario:
        paths = [Path(p) for p in args.scenario]
    else:
        paths = list_scenario_paths()
        if not paths:
            print(
                f"[error] no scenarios found in {DEFAULT_SCENARIO_DIR}",
                file=sys.stderr,
            )
            return 2

    for path in paths:
        _cli_run_one(path, args.mode, pace_min, pace_max, args.seed)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# app/eval/scenario_runner.py
from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, List, Tuple

from app.data.logger import init_db, log_turn
from app.mocks.mock_module_c import process_message
from app.mocks.mock_state_machine import update_state

BLOCKED_MESSAGE = "[This message was blocked by the safety system]"
MODEL_USED = "mock-llm"


def load_scenario(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def mock_llm_generate(user_message: str) -> str:
    """
    A simple deterministic 'LLM' to make the demo consistent.
    Produces a clearly harmful-seeming answer for harmful prompts so output_scanner can act.
    """
    m = (user_message or "").lower()
    if "bypass security" in m or "hack" in m or "make a bomb" in m:
        return "Here's a step-by-step outline: Step 1... Step 2... (mock unsafe output)"
    return "Mock response: Thanks for chatting! (persona-friendly)"


def output_scanner(ai_response_original: str) -> Tuple[bool, str]:
    """
    Simple output scanner (placeholder for Person B's real output_scanner.py).
    Returns (blocked, final_response).
    """
    text = (ai_response_original or "").lower()
    if "step 1" in text and "unsafe" in text:
        return True, BLOCKED_MESSAGE
    return False, ai_response_original


def run_scenario(
    scenario_path: str,
    mode: str,
    db_path: str,
) -> str:
    """
    Runs scenario under mode:
    - baseline: always pass, no C/A logic
    - cab_mock: use mock Module C + mock state machine + output scan
    Writes telemetry for each turn, returns session_id.
    """
    scenario = load_scenario(scenario_path)
    scenario_id = scenario.get("scenario_id", os.path.basename(scenario_path))
    turns = scenario.get("turns", [])

    session_id = f"{scenario_id}__{mode}__{int(time.time())}"
    init_db(db_path)

    history: List[Dict[str, str]] = []

    for i, t in enumerate(turns, start=1):
        user_message = t.get("content", "")
        ts = time.time()
        start = time.perf_counter()
        # Prefer explicit user_id in scenario; fallback to a deterministic sim id
        user_id = t.get("user_id") or f"sim_user_{i}"

        if mode == "baseline":
            # Baseline: no C/A, always pass and call model
            ai_original = mock_llm_generate(user_message)
            ai_final = ai_original
            ai_final2 = ai_original
            mediation_applied = False
            action = "pass"

            latency_ms = int((time.perf_counter() - start) * 1000)

            log_turn(
                session_id=session_id,
                turn_number=i,
                db_path=db_path,
                data={
                    "timestamp": ts,
                    "scenario_id": scenario_id,
                    "mode": mode,
                    "user_id": user_id,
                    "user_message": user_message,
                    "injection_blocked": False,
                    "module_c_tags": [],
                    "severity": "low",
                    "risk_state": "Safe",
                    "risk_score": 0.05,
                    "action": action,
                    "block_reason": "",
                    "ai_response_original": ai_original,
                    "ai_response_final": ai_final2,
                    "mediation_applied": mediation_applied,
                    "model_used": MODEL_USED,
                    "latency_ms": latency_ms,
                },
            )

            history.append({"role": "user", "content": user_message})
            continue

        if mode != "cab_mock":
            raise ValueError(f"Unknown mode: {mode}")

        # --- C: message processing ---
        c_result = process_message(user_message, history)

        # Fast path: deterministic injection => block immediately (skip model call)
        if c_result.get("injection_blocked", False):
            latency_ms = int((time.perf_counter() - start) * 1000)
            log_turn(
                session_id=session_id,
                turn_number=i,
                db_path=db_path,
                data={
                    "timestamp": ts,
                    "scenario_id": scenario_id,
                    "mode": mode,
                    "user_id": user_id,
                    "user_message": user_message,
                    "injection_blocked": True,
                    "module_c_tags": c_result.get("risk_tags", []),
                    "severity": c_result.get("severity", "high"),
                    "risk_state": "Restricted",
                    "risk_score": 1.0,
                    "action": "block",
                    "block_reason": c_result.get("block_reason", "Prompt injection detected"),
                    "ai_response_original": None,  # never called model
                    "ai_response_final": BLOCKED_MESSAGE,
                    "mediation_applied": True,
                    "model_used": MODEL_USED,
                    "latency_ms": latency_ms,
                },
            )
            history.append({"role": "user", "content": user_message})
            continue

        # --- A: state update ---
        a_result = update_state(c_result, history)
        risk_state = a_result["risk_state"]
        risk_score = a_result["risk_score"]
        action = a_result["action"]

        # If state machine blocks, skip model call
        if action == "block":
            latency_ms = int((time.perf_counter() - start) * 1000)
            log_turn(
                session_id=session_id,
                turn_number=i,
                db_path=db_path,
                data={
                    "timestamp": ts,
                    "scenario_id": scenario_id,
                    "mode": mode,
                    "user_id": user_id,
                    "user_message": user_message,
                    "injection_blocked": False,
                    "module_c_tags": c_result.get("risk_tags", []),
                    "severity": c_result.get("severity", "high"),
                    "risk_state": risk_state,
                    "risk_score": risk_score,
                    "action": "block",
                    "block_reason": a_result.get("block_reason") or c_result.get("block_reason", ""),
                    "ai_response_original": None,
                    "ai_response_final": BLOCKED_MESSAGE,
                    "mediation_applied": True,
                    "model_used": MODEL_USED,
                    "latency_ms": latency_ms,
                },
            )
            history.append({"role": "user", "content": user_message})
            continue

        # --- Model call (mock) ---
        ai_original = mock_llm_generate(user_message)

        # --- Output scan (placeholder for real Module C output_scanner) ---
        mediation_applied = False
        block_reason = a_result.get("block_reason", "") or c_result.get("block_reason", "")
        ai_final = ai_original
        final_action = action

        if action == "scan":
            blocked, scanned_final = output_scanner(ai_original)
            if blocked:
                ai_final = scanned_final
                mediation_applied = True
                final_action = "block"
                if not block_reason:
                    block_reason = "Output scanner blocked unsafe content"
                # When output scanner blocks, keep risk_state but action becomes block
            else:
                ai_final = scanned_final

        latency_ms = int((time.perf_counter() - start) * 1000)

        log_turn(
            session_id=session_id,
            turn_number=i,
            db_path=db_path,
            data={
                "timestamp": ts,
                "scenario_id": scenario_id,
                "mode": mode,
                "user_id": user_id,
                "user_message": user_message,
                "injection_blocked": False,
                "module_c_tags": c_result.get("risk_tags", []),
                "severity": c_result.get("severity", "low"),
                "risk_state": risk_state,
                "risk_score": risk_score,
                "action": final_action,
                "block_reason": block_reason,
                "ai_response_original": ai_original,
                "ai_response_final": ai_final,
                "mediation_applied": mediation_applied,
                "model_used": MODEL_USED,
                "latency_ms": latency_ms,
            },
        )

        history.append({"role": "user", "content": user_message})

    return session_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON")
    parser.add_argument("--mode", required=True, choices=["baseline", "cab_mock"], help="Run mode")
    parser.add_argument("--db", default="app/data/telemetry.db", help="SQLite db path")
    args = parser.parse_args()

    session_id = run_scenario(args.scenario, args.mode, args.db)
    print(f"✅ Finished run. session_id={session_id}")
    print(f"DB: {args.db}")


if __name__ == "__main__":
    main()
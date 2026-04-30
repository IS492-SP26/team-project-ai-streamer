"""
C-A-B pipeline entry: Module C -> Module A -> LLM (if allowed) -> mediation.
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

import os
import time
from typing import Any, Dict, List

try:
    from module_c import process_message
except ImportError as e:
    raise ImportError(
        "Could not import module_c.process_message. "
        "Ensure you run from the `app` directory and that module_c/__init__.py "
        "defines process_message(message, history)."
    ) from e

from module_a.autonomy_policy import decide_action
from module_a.mediation import apply_mediation
from module_a.risk_tracker import update_risk_from_module_c
from data.logger import init_db, log_turn

# ---------------------------------------------------------------------------
# GitHub Models API (OpenAI-compatible)
# ---------------------------------------------------------------------------

GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_TELEMETRY_DB_PATH = os.path.join(_APP_DIR, "data", "telemetry.db")

# Migrate the telemetry schema once at import time, so the first turn does
# not race against schema initialization (verifier finding 2026-04-29).
# This is idempotent: init_db checks if columns exist before ALTER TABLE.
try:
    init_db(_TELEMETRY_DB_PATH)
except Exception:
    # Don't block the pipeline on telemetry setup; logging will be skipped
    # gracefully later if the DB really is unwritable.
    pass

_DEFAULT_ARIA_PROMPT = (
    "You are Aria, a friendly AI VTuber on a live stream.\n"
    "Stay cheerful, helpful, and in character. Keep chat replies short (1-3 sentences)."
)


def _load_aria_system_prompt() -> str:
    path = os.path.join(_APP_DIR, "prompts", "aria_system_prompt.txt")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
            if text:
                return text
    return _DEFAULT_ARIA_PROMPT


def _get_github_token() -> str | None:
    return os.environ.get("GITHUB_TOKEN")


def call_llm(
    user_message: str,
    history: List[Dict[str, str]],
    system_prompt: str,
    token: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 300,
) -> str:
    import requests

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for h in history:
        if h.get("role") in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    resp = requests.post(
        GITHUB_MODELS_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _run_baseline_turn(user_message: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
    """Baseline mode: bypass Module C and Module A entirely.

    Used by the live demo to show what happens when there is no governance
    layer in front of the LLM. Returns a result dict with the same shape as
    the C-A-B path so the UI can render either uniformly.
    """
    turn = int(session_state.get("turn_number", 0)) + 1
    session_state["turn_number"] = turn
    history: List[Dict[str, str]] = list(session_state.get("messages") or [])

    system_prompt = _load_aria_system_prompt()
    token = _get_github_token()
    t0 = time.time()
    if token:
        try:
            ai_text = call_llm(user_message, history, system_prompt, token, DEFAULT_MODEL)
        except Exception:
            from pipeline.cab_pipeline import deterministic_mock_llm
            ai_text = deterministic_mock_llm(user_message, history, mode="baseline")
    else:
        from pipeline.cab_pipeline import deterministic_mock_llm
        ai_text = deterministic_mock_llm(user_message, history, mode="baseline")
    latency_ms = int((time.time() - t0) * 1000)

    # Baseline does not update risk; reset to Safe so the UI shows "no governance".
    session_state["risk_score"] = 0.0
    session_state["risk_state"] = "Safe"
    session_state["last_action"] = "allow"
    session_state["last_policy_reason"] = "baseline mode bypasses C-A-B"
    session_state["last_module_c_latency_ms"] = 0.0

    module_c_output = {
        "message": user_message,
        "injection_blocked": False,
        "risk_tags": [],
        "severity": "low",
        "block_reason": "",
        "layer_details": {"baseline_bypass": {"fired": True}},
    }

    result = {
        "risk_state": "Safe",
        "risk_score": 0.0,
        "action": "allow",
        "ai_response_final": ai_text,
        "ai_response_original": ai_text,
        "mediation_applied": False,
        "module_c_output": module_c_output,
        "turn_number": turn,
        "user_message": user_message,
        "injection_blocked": False,
        "module_c_tags": [],
        "severity": "low",
        "block_reason": "",
        "latency_ms": latency_ms,
        "model_used": DEFAULT_MODEL if token else "deterministic-mock-baseline",
        "user_id": session_state.get("user_id"),
        "session_id": session_state.get("session_id"),
        "scenario_id": session_state.get("scenario_id"),
        "mode": "baseline",
        "pipeline_mode": "baseline",
        "wellbeing_fired": False,
    }

    if session_state.get("session_id"):
        try:
            log_turn(
                session_id=session_state["session_id"],
                turn_number=turn,
                data=result,
                db_path=_TELEMETRY_DB_PATH,
            )
        except Exception:
            pass
    return result


def run_pipeline(user_message: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run one user turn through C-A-B (or baseline if pipeline_mode says so):
    Module C -> risk tracker -> policy -> LLM (if not blocked) -> mediation.

    Mutates session_state: risk_score, risk_state, turn_number.
    The caller chooses cab vs baseline by setting session_state["pipeline_mode"].
    """
    if session_state.get("pipeline_mode") == "baseline":
        return _run_baseline_turn(user_message, session_state)

    # CAB path: delegate to cab_pipeline.run_cab_turn so that the manual
    # chat surface, the red-team auto-play, the proxy, and the offline
    # eval all share exactly one governance code path. This way the
    # wellbeing pre-filter, the CP4 policy overrides, and the
    # output_scanner all run for manual chat too (previously only the
    # offline eval got them — that gap was a bug).
    from pipeline.cab_pipeline import run_cab_turn  # local import avoids cycles

    prev_score = float(session_state.get("risk_score", 0.0))
    prev_state = str(session_state.get("risk_state", "Safe"))
    turn = int(session_state.get("turn_number", 0)) + 1
    session_state["turn_number"] = turn
    history: List[Dict[str, str]] = list(session_state.get("messages") or [])

    # Build a real-LLM generator that uses GitHub Models when a token is
    # present and falls back to the deterministic mock on error or no
    # token. cab_pipeline calls llm_generate only when the action allows
    # generation (i.e. not blocked, not vulnerable_user mediation).
    system_prompt = _load_aria_system_prompt()
    token = _get_github_token()

    def _llm_generate(msg: str, hist: List[Dict[str, str]]) -> str:
        # Build conversation with persistent system prompt.
        history_with_system = [{"role": "system", "content": system_prompt}, *hist]
        if not token:
            from pipeline.cab_pipeline import deterministic_mock_llm
            return deterministic_mock_llm(msg, history_with_system, mode="cab")
        try:
            return call_llm(msg, hist, system_prompt, token, DEFAULT_MODEL)
        except Exception:
            from pipeline.cab_pipeline import deterministic_mock_llm
            return deterministic_mock_llm(msg, history_with_system, mode="cab")

    trace = run_cab_turn(
        session_id=str(session_state.get("session_id") or "manual_chat"),
        scenario_id=str(session_state.get("scenario_id") or "manual_chat"),
        scenario_type=str(session_state.get("scenario_type") or "manual_chat"),
        user_id=str(session_state.get("user_id") or "manual_user"),
        turn_number=turn,
        user_message=user_message,
        history=history,
        previous_risk_score=prev_score,
        previous_risk_state=prev_state,
        mode="cab",
        llm_generate=_llm_generate,
        db_path=_TELEMETRY_DB_PATH if session_state.get("session_id") else None,
        synthetic_or_real="manual_chat",
    )

    # Mirror trace fields back into session_state for the UI sidebar.
    session_state["risk_score"] = float(trace["risk_score"])
    session_state["risk_state"] = str(trace["risk_state"])
    session_state["last_action"] = str(trace["action"])
    session_state["last_policy_reason"] = str(trace.get("policy_reason", ""))
    session_state["last_module_c_latency_ms"] = float(trace.get("latency_ms", 0))

    wellbeing = trace.get("wellbeing_detector") or {}

    return {
        "risk_state": trace["risk_state"],
        "risk_score": trace["risk_score"],
        "action": trace["action"],
        "ai_response_final": trace.get("ai_response_final", ""),
        "ai_response_original": trace.get("ai_response_original", ""),
        "mediation_applied": trace.get("mediation_applied", False),
        "module_c_output": trace.get("module_c_output", {}),
        "turn_number": trace.get("turn_number", turn),
        "user_message": user_message,
        "injection_blocked": trace.get("injection_blocked", False),
        "module_c_tags": trace.get("module_c_tags", []),
        "severity": trace.get("severity", "low"),
        "block_reason": trace.get("block_reason", ""),
        "latency_ms": trace.get("latency_ms", 0),
        "model_used": trace.get("model_used", DEFAULT_MODEL if token else "mock"),
        "user_id": session_state.get("user_id", None),
        "session_id": session_state.get("session_id", None),
        "scenario_id": session_state.get("scenario_id", None),
        "mode": "cab",
        "pipeline_mode": "cab",
        "wellbeing_fired": bool(wellbeing.get("fired", False)),
    }

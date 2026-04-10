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

# ---------------------------------------------------------------------------
# GitHub Models API (OpenAI-compatible)
# ---------------------------------------------------------------------------

GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"

_APP_DIR = os.path.dirname(os.path.abspath(__file__))

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


def run_pipeline(user_message: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run one user turn: Module C -> risk tracker -> policy -> LLM (if not blocked) -> mediation.

    Mutates session_state: risk_score, risk_state, turn_number (caller stores messages).
    """
    prev_score = float(session_state.get("risk_score", 0.0))
    prev_state = str(session_state.get("risk_state", "Safe"))
    turn = int(session_state.get("turn_number", 0)) + 1
    session_state["turn_number"] = turn

    history: List[Dict[str, str]] = list(session_state.get("messages") or [])

    # --- Step 1: Module C ---
    t0 = time.time()
    module_c_output = process_message(user_message, history)
    module_c_latency_ms = (time.time() - t0) * 1000

    # --- Step 2: Module A risk tracker + policy ---
    risk_update = update_risk_from_module_c(module_c_output, prev_score, prev_state)
    risk_score = float(risk_update["risk_score"])
    risk_state = str(risk_update["risk_state"])
    session_state["risk_score"] = risk_score
    session_state["risk_state"] = risk_state

    action, policy_reason = decide_action(risk_state)

    # --- Step 3: LLM call (skipped when blocked) ---
    system_prompt = _load_aria_system_prompt()
    token = _get_github_token()

    ai_raw = ""
    if action == "block":
        ai_raw = ""
    elif not token:
        ai_raw = (
            "Hmm, I can't reach the stream brain right now (no GITHUB_TOKEN). "
            "Pretend I just waved and said hi! 🐱"
        )
    else:
        try:
            ai_raw = call_llm(user_message, history, system_prompt, token, DEFAULT_MODEL)
        except Exception:
            ai_raw = (
                "Oops, chat backend hiccupped — give me one sec! "
                "Still here and rooting for you~ 🐱"
            )

    # --- Step 4: Mediation ---
    final_text, mediation_applied = apply_mediation(action, ai_raw)

    # Enrich session for UI
    session_state["last_policy_reason"] = policy_reason
    session_state["last_action"] = action
    session_state["last_module_c_latency_ms"] = module_c_latency_ms

    result = {
        "risk_state": risk_state,
        "risk_score": risk_score,
        "action": action,
        "ai_response_final": final_text,
        "ai_response_original": ai_raw,
        "mediation_applied": mediation_applied,
        "module_c_output": module_c_output,
        "turn_number": turn,
        "user_message": user_message,
        "injection_blocked": module_c_output.get("injection_blocked", False),
        "module_c_tags": module_c_output.get("risk_tags", []),
        "severity": module_c_output.get("severity", "low"),
        "block_reason": module_c_output.get("block_reason", ""),
        "latency_ms": int((time.time() - t0) * 1000),
        "model_used": DEFAULT_MODEL if token and action != "block" else "mock",
        "user_id": session_state.get("user_id", None),
        "session_id": session_state.get("session_id", None),
        "scenario_id": session_state.get("scenario_id", None),
        "mode": session_state.get("mode", "cab_mock"),
    }

    try:
        from data.logger import init_db, log_turn
        db_path = os.path.join(_APP_DIR, "data", "telemetry.db")
        init_db(db_path)
        if session_state.get("session_id"):
            log_turn(
                session_id=session_state["session_id"],
                turn_number=turn,
                data=result,
                db_path=db_path,
            )
    except Exception:
        pass

    return result

"""OpenAI-compatible proxy that wraps `cab_pipeline.run_cab_turn`.

Why this exists: Open-LLM-VTuber and most other open-source AI VTuber
stacks point at an OpenAI-compatible endpoint via OPENAI_BASE_URL. By
running this proxy on localhost, those stacks can use C-A-B as their
LLM without any code changes — the proxy intercepts the chat request,
runs message + history through the C-A-B pipeline, and returns the
mediated `ai_response_final` as the model's reply.

Endpoints:
  GET  /v1/models                    list one model id "cab-aria"
  POST /v1/chat/completions          OpenAI-compatible chat completions

Behavior:
- Reads the latest user message from the `messages` array.
- Runs prior history (everything before the latest user turn) through
  cab_pipeline as conversation history.
- mode is read from the JSON body's `cab_mode` field if present, or
  from the X-CAB-Mode HTTP header, otherwise defaults to "cab".
- baseline mode bypasses C-A-B and just returns the deterministic mock.
- streaming requests are NOT supported — returns a non-streamed response
  even if `stream=true` is requested. Most clients tolerate this.

Run:
  python -m app.integrations.cab_openai_proxy
  # or
  uvicorn app.integrations.cab_openai_proxy:app --host 127.0.0.1 --port 8000

Provenance: 2026-04-29. CP4 live demo integration layer.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# sys.path setup
_APP_ROOT = Path(__file__).resolve().parents[1]
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from pipeline.cab_pipeline import deterministic_mock_llm, run_cab_turn  # noqa: E402

MODEL_ID = "cab-aria"
DEFAULT_DB_PATH = str(_APP_ROOT / "data" / "telemetry.db")

app = FastAPI(
    title="C-A-B OpenAI-compatible Proxy",
    description=(
        "Wraps cab_pipeline.run_cab_turn behind an OpenAI-compatible "
        "/v1/chat/completions endpoint so any OpenAI-API client (e.g. "
        "Open-LLM-VTuber) can use C-A-B as their LLM without code changes."
    ),
    version="0.1.0",
)


def _split_messages(messages: List[Dict[str, Any]]) -> tuple[Optional[str], List[Dict[str, str]]]:
    """Return (latest_user_message, prior_history)."""
    if not messages:
        return None, []
    # Find the last user message; everything before it is prior history.
    latest_user_idx = None
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            latest_user_idx = i
            break
    if latest_user_idx is None:
        return None, []
    latest = messages[latest_user_idx].get("content")
    history = []
    for m in messages[:latest_user_idx]:
        role = m.get("role")
        if role in {"user", "assistant", "system"}:
            history.append({"role": role, "content": str(m.get("content", ""))})
    return (str(latest) if latest is not None else None), history


def _build_chat_response(
    text: str,
    *,
    model: str = MODEL_ID,
    finish_reason: str = "stop",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completions.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": len(text.split()),
            "total_tokens": len(text.split()),
        },
    }
    if extra:
        payload["cab_metadata"] = extra
    return payload


@app.get("/v1/models")
def list_models() -> Dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_ID,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "c-a-b",
            }
        ],
    }


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "model": MODEL_ID}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    try:
        body: Dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid JSON: {exc}") from exc

    messages = body.get("messages") or []
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="`messages` must be a non-empty list")

    latest_user, history = _split_messages(messages)
    if latest_user is None:
        raise HTTPException(
            status_code=400,
            detail="`messages` must contain at least one user-role message",
        )

    # Mode: body field cab_mode > header X-CAB-Mode > default cab.
    mode = (
        body.get("cab_mode")
        or request.headers.get("x-cab-mode")
        or "cab"
    )
    mode = str(mode).lower()
    if mode not in {"cab", "baseline"}:
        raise HTTPException(
            status_code=400,
            detail=f"cab_mode must be 'cab' or 'baseline', got {mode!r}",
        )

    # Optional metadata for telemetry. We accept these from the client
    # so the proxy can be threaded into a multi-viewer scenario.
    session_id = str(body.get("cab_session_id") or f"proxy_{uuid.uuid4().hex[:12]}")
    user_id = str(body.get("cab_user_id") or f"viewer_{uuid.uuid4().hex[:8]}")
    scenario_id = str(body.get("cab_scenario_id") or "open_llm_vtuber_session")
    scenario_type = str(body.get("cab_scenario_type") or "live_demo")
    write_db = bool(body.get("cab_log_db", os.getenv("CAB_LOG_DB", "1") == "1"))
    db_path = DEFAULT_DB_PATH if write_db else None

    # Compute turn number from history (count of user messages including this one).
    turn_number = sum(1 for m in messages if m.get("role") == "user")

    if mode == "baseline":
        text = deterministic_mock_llm(latest_user, history, mode="baseline")
        return JSONResponse(
            _build_chat_response(
                text,
                extra={"mode": "baseline", "session_id": session_id},
            )
        )

    # cab mode
    trace = run_cab_turn(
        session_id=session_id,
        scenario_id=scenario_id,
        scenario_type=scenario_type,
        user_id=user_id,
        turn_number=turn_number,
        user_message=latest_user,
        history=history,
        mode="cab",
        db_path=db_path,
        synthetic_or_real="live_proxy",
    )
    return JSONResponse(
        _build_chat_response(
            trace.get("ai_response_final", ""),
            extra={
                "mode": "cab",
                "session_id": session_id,
                "turn_number": turn_number,
                "risk_state": trace.get("risk_state"),
                "risk_score": trace.get("risk_score"),
                "action": trace.get("action"),
                "module_c_tags": trace.get("module_c_tags"),
                "injection_blocked": trace.get("injection_blocked"),
                "wellbeing_fired": (
                    (trace.get("wellbeing_detector") or {}).get("fired", False)
                ),
                "block_reason": trace.get("block_reason"),
            },
        )
    )


def main() -> int:
    import uvicorn

    host = os.getenv("CAB_PROXY_HOST", "127.0.0.1")
    port = int(os.getenv("CAB_PROXY_PORT", "8000"))
    uvicorn.run(
        "app.integrations.cab_openai_proxy:app",
        host=host,
        port=port,
        log_level=os.getenv("CAB_PROXY_LOG_LEVEL", "info"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

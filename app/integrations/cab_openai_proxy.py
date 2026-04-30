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

import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# Module-level logger so every chat call emits a one-line audit trace
# the operator can grep during a live demo or post-hoc review.
logger = logging.getLogger("cab_proxy")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(
        logging.Formatter(
            "%(asctime)s [cab_proxy] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(_h)
logger.setLevel(os.environ.get("CAB_PROXY_LOG_LEVEL", "info").upper())

# sys.path setup
_APP_ROOT = Path(__file__).resolve().parents[1]
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import JSONResponse, StreamingResponse  # noqa: E402

from pipeline.cab_pipeline import deterministic_mock_llm, run_cab_turn  # noqa: E402

MODEL_ID = "cab-aria"
DEFAULT_DB_PATH = str(_APP_ROOT / "data" / "telemetry.db")

# GitHub Models — when GITHUB_TOKEN is set, the proxy threads a real-LLM
# callable into cab_pipeline so Aria's CAB-mode responses are varied
# real-model output instead of the deterministic mock. Baseline mode
# never uses the real LLM (the punchline of the demo depends on the
# marker string).
#
# We use the newer GitHub Models marketplace endpoint at
# `https://models.github.ai/inference/chat/completions`, which catalogs
# strong 0x-quota Copilot models including:
#   openai/gpt-5-chat        — best general-purpose, default
#   openai/gpt-4.1           — strong, slightly older
#   openai/gpt-4.1-mini      — fast / cheap
#   meta/llama-3.3-70b-instruct
#   meta/llama-4-maverick-17b-128e-instruct-fp8
#   xai/grok-3
# Override the model via env: CAB_LIVE_MODEL="openai/gpt-4.1".
# The legacy `https://models.inference.ai.azure.com/chat/completions`
# endpoint only exposed gpt-4o(-mini) + Llama-3.1; the newer one
# requires the model id to be prefixed (`openai/`, `meta/`, etc.).
GITHUB_MODELS_URL = os.environ.get(
    "CAB_LIVE_LLM_URL",
    "https://models.github.ai/inference/chat/completions",
)
# Default chosen for demo robustness: gpt-4.1-mini sits in the
# higher-quota "low" tier (150 RPM / 1500 RPD on the free token tier),
# so a back-to-back demo run firing ~18 requests in 30 s does not get
# 429-throttled mid-presentation. gpt-5-chat is in the "high" tier
# (50 RPM / 1000 RPD) and gets throttled fast.
# Override with CAB_LIVE_MODEL env when you want a stronger model.
DEFAULT_LIVE_MODEL = os.environ.get("CAB_LIVE_MODEL", "openai/gpt-4.1-mini")
# Fallback chain when the primary 429s. Tried in order. Each fallback
# is a different rate-limit bucket so most demos survive even if one
# model is throttled.
LIVE_MODEL_FALLBACKS = [
    m for m in os.environ.get(
        "CAB_LIVE_MODEL_FALLBACKS",
        "openai/gpt-4.1-mini,openai/gpt-4.1,openai/gpt-4o-mini,meta/llama-3.3-70b-instruct",
    ).split(",")
    if m.strip()
]
ARIA_SYSTEM_PROMPT_PATH = _APP_ROOT / "prompts" / "aria_system_prompt.txt"
_DEFAULT_ARIA_PROMPT = (
    "You are Aria, a friendly AI VTuber on a live stream. "
    "Stay cheerful, helpful, and in character. Keep chat replies short (1-3 sentences)."
)


def _load_aria_prompt() -> str:
    if ARIA_SYSTEM_PROMPT_PATH.is_file():
        try:
            text = ARIA_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
            if text:
                return text
        except OSError:
            pass
    return _DEFAULT_ARIA_PROMPT


def _build_real_llm_generate():
    """Return a callable cab_pipeline.run_cab_turn can use for generation
    when GITHUB_TOKEN is set, or None when no token is available.

    The callable falls back to deterministic_mock_llm on any HTTP failure
    so a flaky network never crashes the demo.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    try:
        import requests  # noqa: WPS433 — local import keeps base imports light
    except ImportError:
        logger.warning("real-LLM mode requested but `requests` is unavailable")
        return None

    system_prompt = _load_aria_prompt()

    # Primary model + fallbacks in order. De-dup but keep order.
    seen: set = set()
    candidate_models: List[str] = []
    for m in [DEFAULT_LIVE_MODEL, *LIVE_MODEL_FALLBACKS]:
        m = m.strip()
        if m and m not in seen:
            candidate_models.append(m)
            seen.add(m)

    def _generate(user_message: str, history: List[Dict[str, str]]) -> str:
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for h in history:
            if h.get("role") in ("user", "assistant"):
                messages.append({"role": h["role"], "content": str(h.get("content", ""))})
        messages.append({"role": "user", "content": user_message})

        last_exc = None
        for model_id in candidate_models:
            try:
                resp = requests.post(
                    GITHUB_MODELS_URL,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model_id,
                        "messages": messages,
                        "max_tokens": 220,
                        "temperature": 0.8,
                    },
                    timeout=20,
                )
                # 429 / 5xx → try next model in the fallback chain.
                if resp.status_code in (429, 500, 502, 503, 504):
                    logger.warning(
                        "model=%s returned HTTP %s, trying next fallback",
                        model_id, resp.status_code,
                    )
                    continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except requests.HTTPError as exc:
                # Non-retryable HTTP (400, 401, 403, 404) — stop trying chain.
                logger.warning("model=%s HTTPError, stopping chain: %s", model_id, exc)
                last_exc = exc
                break
            except Exception as exc:  # pragma: no cover — flaky-network safety
                logger.warning("model=%s call failed: %s; trying next", model_id, exc)
                last_exc = exc
                continue

        logger.warning(
            "all real-LLM models exhausted (last err: %s); falling back to mock",
            last_exc,
        )
        return deterministic_mock_llm(user_message, history, mode="cab")

    return _generate


_REAL_LLM_GENERATE = _build_real_llm_generate()

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


def _build_streaming_response(
    text: str,
    *,
    model: str = MODEL_ID,
    chunk_size: int = 24,
) -> StreamingResponse:
    """Return an OpenAI-compatible SSE stream of `text`.

    cab_pipeline produces the full response synchronously, but OpenAI
    clients (notably Open-LLM-VTuber's openai_compatible_llm) iterate
    chunks via `aiter_lines()` and never render the message if a single
    JSON arrives. We slice the cab response into ~24-char chunks and
    emit them as `data: {…}` SSE events, then `data: [DONE]`. This
    makes the avatar lip-sync and full-text events fire normally.
    """
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())

    def _event(delta: Dict[str, Any], finish: Optional[str] = None) -> str:
        chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": delta,
                    "finish_reason": finish,
                }
            ],
        }
        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    async def _gen():
        # Initial role chunk so the openai client knows it's an assistant turn.
        yield _event({"role": "assistant", "content": ""})
        if text:
            for i in range(0, len(text), chunk_size):
                yield _event({"content": text[i : i + chunk_size]})
        # Final chunk: empty delta, finish_reason=stop.
        yield _event({}, finish="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


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


@app.get("/", include_in_schema=False)
def root() -> JSONResponse:
    """Friendly 200 so curious humans who hit the wrong port understand
    this is the API proxy, not the Live2D UI. Open-LLM-VTuber's web
    frontend lives on :12393, not here.
    """
    return JSONResponse(
        {
            "service": "cab_openai_proxy",
            "model": MODEL_ID,
            "openai_compatible_endpoint": "/v1/chat/completions",
            "models_endpoint": "/v1/models",
            "health": "/healthz",
            "note": (
                "This is the C-A-B governance proxy. There is no web UI here. "
                "Open Open-LLM-VTuber at http://localhost:12393 for the Live2D "
                "avatar, or open the Streamlit app on its own port (default 8501)."
            ),
            "current_force_mode": (
                os.environ.get("CAB_PROXY_FORCE_MODE", "").strip().lower() or None
            ),
        }
    )


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

    # Mode resolution order:
    #   1. Process-level CAB_PROXY_FORCE_MODE env var (operator override
    #      — set this when the calling client cannot inject the per-
    #      request mode, e.g. Open-LLM-VTuber's openai_compatible_llm).
    #   2. Per-request body field cab_mode.
    #   3. Per-request header X-CAB-Mode.
    #   4. Default cab.
    forced = os.environ.get("CAB_PROXY_FORCE_MODE", "").strip().lower()
    mode = (
        forced
        or body.get("cab_mode")
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

    want_stream = bool(body.get("stream"))

    if mode == "baseline":
        text = deterministic_mock_llm(latest_user, history, mode="baseline")
        logger.info(
            "BASELINE T%d session=%s msg=%r → response=%r",
            turn_number,
            session_id[:12],
            latest_user[:80],
            text[:80],
        )
        if want_stream:
            return _build_streaming_response(text)
        return JSONResponse(
            _build_chat_response(
                text,
                extra={"mode": "baseline", "session_id": session_id},
            )
        )

    # cab mode — use real LLM (gpt-4o-mini via GitHub Models) when
    # GITHUB_TOKEN is set, else cab_pipeline falls back to its
    # deterministic mock so the demo runs offline.
    trace = run_cab_turn(
        session_id=session_id,
        scenario_id=scenario_id,
        scenario_type=scenario_type,
        user_id=user_id,
        turn_number=turn_number,
        user_message=latest_user,
        history=history,
        mode="cab",
        llm_generate=_REAL_LLM_GENERATE,
        db_path=db_path,
        synthetic_or_real="live_proxy",
    )
    wellbeing_fired = (trace.get("wellbeing_detector") or {}).get("fired", False)
    logger.info(
        "CAB T%d session=%s action=%s state=%s score=%.2f tags=%s "
        "injection=%s wellbeing=%s msg=%r",
        turn_number,
        session_id[:12],
        trace.get("action"),
        trace.get("risk_state"),
        float(trace.get("risk_score", 0.0)),
        trace.get("module_c_tags") or [],
        bool(trace.get("injection_blocked")),
        bool(wellbeing_fired),
        latest_user[:80],
    )
    final_text = trace.get("ai_response_final", "")
    if want_stream:
        return _build_streaming_response(final_text)
    return JSONResponse(
        _build_chat_response(
            final_text,
            extra={
                "mode": "cab",
                "session_id": session_id,
                "turn_number": turn_number,
                "risk_state": trace.get("risk_state"),
                "risk_score": trace.get("risk_score"),
                "action": trace.get("action"),
                "module_c_tags": trace.get("module_c_tags"),
                "injection_blocked": trace.get("injection_blocked"),
                "wellbeing_fired": wellbeing_fired,
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

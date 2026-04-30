"""Red-team driver that feeds CP4 scenarios into Open-LLM-VTuber via WS.

This is the bridge that makes the live-stream demo end-to-end:

  red-team scenario JSON
    → ollv_ws_driver
        sends each turn as {"type":"text-input"} to OLLV's /client-ws
    → OLLV (avatar speaks)
        OLLV calls our cab_openai_proxy at http://127.0.0.1:8000/v1
    → cab_openai_proxy
        runs cab_pipeline.run_cab_turn (or baseline if mode header set)
    → response flows back through OLLV
        Aria avatar lip-syncs the (governed) reply

Run order on demo day:
    Terminal 1:  python -m app.integrations.cab_openai_proxy
    Terminal 2:  cd ~/Open-LLM-VTuber && .venv/bin/python run_server.py
                 (open http://localhost:12393 in OBS-captured browser)
    Terminal 3:  python -m app.red_team.ollv_ws_driver \\
                   --scenario app/eval/scenarios/direct_injection.json \\
                   --mode cab

Mode is sent to the proxy via the `cab_mode` body field on each call —
the proxy routes accordingly. Switching mode mid-demo is a CLI flag
re-run, not a code change.

Provenance: 2026-04-29.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

import websockets

_APP_ROOT = Path(__file__).resolve().parents[1]
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from red_team.runner import (  # noqa: E402
    DEFAULT_MAX_PACE,
    DEFAULT_MIN_PACE,
    list_scenario_paths,
    load_scenario,
)


DEFAULT_OLLV_URL = "ws://127.0.0.1:12393/client-ws"


async def _send_one_turn(
    ws: "websockets.WebSocketClientProtocol",
    text: str,
    user_id: str,
    mode: str,
    *,
    settle_seconds: float,
) -> None:
    """Send one text-input message and let OLLV process it.

    The proxy reads cab_mode from the JSON body; OLLV puts arbitrary
    body fields on the request when its `extra` config carries them.
    Since OLLV's openai_compatible_llm doesn't expose `extra`, we drive
    mode at the OLLV-launch level: launch OLLV with CAB_MODE env so the
    proxy header path picks it up. The driver itself sends only the
    user-visible text.
    """
    payload = {
        "type": "text-input",
        "text": text,
        # OLLV has no slot for per-message user_id but if we ever extend
        # its agent to forward arbitrary fields these would land in the
        # proxy as cab_user_id / cab_session_id.
    }
    await ws.send(json.dumps(payload))
    # Drain whatever OLLV emits during this turn so the next send is clean.
    end = asyncio.get_event_loop().time() + settle_seconds
    saw_response = False
    while asyncio.get_event_loop().time() < end:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=1)
        except asyncio.TimeoutError:
            continue
        try:
            obj = json.loads(msg)
            t = obj.get("type")
            if t == "full-text":
                txt = (obj.get("text") or "")
                if txt and txt not in ("Connection established", "Thinking..."):
                    saw_response = True
                    print(f"  Aria → {txt[:200]}")
        except Exception:
            # binary audio frames; ignore
            pass
    if not saw_response:
        print(
            "  (no full-text from OLLV in settle window — check proxy is "
            "running and OLLV is configured to point at it)"
        )


async def run(
    scenario_path: Path,
    *,
    ollv_url: str,
    settle_seconds: float,
    mode: str,
) -> int:
    scenario = load_scenario(scenario_path)
    print(f"=== {scenario['scenario_id']} via OLLV @ {ollv_url} (mode={mode}) ===")
    print(f"Description: {scenario.get('description','')}")
    print()

    # Heads-up: OLLV's openai_compatible_llm doesn't currently let us
    # set an X-CAB-Mode header per request. The pragmatic workaround is
    # to launch OLLV with CAB_PROXY_DEFAULT_MODE in the proxy's env, or
    # toggle the proxy itself in cab vs baseline at startup. Set the
    # CAB_PROXY_FORCE_MODE env var when starting the proxy:
    #
    #   CAB_PROXY_FORCE_MODE=baseline python -m app.integrations.cab_openai_proxy
    #
    # We surface the chosen mode here so the operator sees it.
    print(
        "NOTE: mode is enforced at the proxy. Restart the proxy with "
        f"CAB_PROXY_FORCE_MODE={mode} if you want to switch.\n"
    )

    async with websockets.connect(ollv_url, max_size=20_000_000) as ws:
        # consume on-connect
        try:
            await asyncio.wait_for(ws.recv(), timeout=2)
        except asyncio.TimeoutError:
            pass

        for turn in sorted(scenario["turns"], key=lambda t: int(t["turn_number"])):
            tn = int(turn["turn_number"])
            uid = str(turn.get("user_id") or "viewer")
            attack = turn.get("is_attack_turn") and "🎯" or "💬"
            content = str(turn["content"])
            print(f"[T{tn}] {attack} {uid}: {content}")
            await _send_one_turn(
                ws,
                text=content,
                user_id=uid,
                mode=mode,
                settle_seconds=settle_seconds,
            )
            print()
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Drive an Open-LLM-VTuber session with a CP4 red-team scenario."
    )
    parser.add_argument(
        "--scenario",
        required=True,
        help="Path to a CP4 scenario JSON in app/eval/scenarios/.",
    )
    parser.add_argument(
        "--mode",
        choices=["cab", "baseline"],
        default="cab",
        help="Reminder of which mode the proxy should be in.",
    )
    parser.add_argument(
        "--ollv-url",
        default=os.environ.get("OLLV_WS_URL", DEFAULT_OLLV_URL),
        help=f"OLLV WebSocket URL (default {DEFAULT_OLLV_URL}).",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=8.0,
        help="Seconds to wait between turns for OLLV to finish responding (default 8).",
    )
    args = parser.parse_args(argv)

    path = Path(args.scenario)
    if not path.exists():
        print(f"[error] scenario not found: {path}", file=sys.stderr)
        print(
            "[hint] available CP4 scenarios:\n  "
            + "\n  ".join(str(p) for p in list_scenario_paths()),
            file=sys.stderr,
        )
        return 2

    try:
        return asyncio.run(
            run(
                path,
                ollv_url=args.ollv_url,
                settle_seconds=float(args.settle_seconds),
                mode=args.mode,
            )
        )
    except (ConnectionRefusedError, OSError) as exc:
        print(f"[error] could not connect to OLLV at {args.ollv_url}: {exc}", file=sys.stderr)
        print(
            "[hint] start OLLV first: cd ~/Open-LLM-VTuber && "
            ".venv/bin/python run_server.py",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

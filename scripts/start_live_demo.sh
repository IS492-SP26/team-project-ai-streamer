#!/usr/bin/env bash
# scripts/start_live_demo.sh — boot the full live-streaming demo stack.
#
# Starts the cab_openai_proxy in the background, then forks Open-LLM-VTuber
# in the foreground. When you Ctrl-C the OLLV process, the proxy is killed
# too (via the EXIT trap). Browser URL printed at the end.
#
# Usage:
#   ./scripts/start_live_demo.sh                  # cab mode (default)
#   ./scripts/start_live_demo.sh baseline         # baseline mode
#   ./scripts/start_live_demo.sh cab ~/Open-LLM-VTuber  # custom OLLV path
#
# Once both servers are up, in a SEPARATE terminal run:
#   python -m app.red_team.ollv_ws_driver --scenario app/eval/scenarios/direct_injection.json --mode cab
#
# And open http://localhost:12393 in the browser to watch the avatar.

set -euo pipefail

CAB_MODE="${1:-cab}"
OLLV_DIR="${2:-$HOME/Open-LLM-VTuber}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -d "$OLLV_DIR" ]; then
    echo "[start_live_demo] Open-LLM-VTuber not found at $OLLV_DIR"
    echo "[start_live_demo] install it with:"
    echo "  git clone --depth=1 https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git $OLLV_DIR"
    echo "  cd $OLLV_DIR && uv sync && .venv/bin/uv pip install faster-whisper"
    echo "[start_live_demo] then copy the conf.yaml diff from"
    echo "  docs/integrations/open_llm_vtuber_setup.md"
    exit 2
fi

if [ ! -x "$OLLV_DIR/.venv/bin/python" ]; then
    echo "[start_live_demo] $OLLV_DIR/.venv/bin/python not found"
    echo "[start_live_demo] run: cd $OLLV_DIR && uv sync"
    exit 2
fi

echo "[start_live_demo] starting cab_openai_proxy (mode=$CAB_MODE) in background"
CAB_PROXY_FORCE_MODE="$CAB_MODE" python3 -m app.integrations.cab_openai_proxy \
    > /tmp/cab_proxy.log 2>&1 &
PROXY_PID=$!
trap 'echo; echo "[start_live_demo] stopping proxy (pid=$PROXY_PID)"; kill $PROXY_PID 2>/dev/null || true' EXIT

# Wait up to 10s for the proxy to come up
for _ in $(seq 1 20); do
    if curl -sS --max-time 1 http://127.0.0.1:8000/healthz > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

if ! curl -sS --max-time 1 http://127.0.0.1:8000/healthz > /dev/null; then
    echo "[start_live_demo] proxy failed to come up; tail of /tmp/cab_proxy.log:"
    tail -20 /tmp/cab_proxy.log
    exit 3
fi

echo "[start_live_demo] proxy ready at http://127.0.0.1:8000  (mode=$CAB_MODE)"
echo "[start_live_demo] proxy log: tail -f /tmp/cab_proxy.log"
echo
echo "[start_live_demo] launching Open-LLM-VTuber in this terminal."
echo "[start_live_demo] when you see 'Uvicorn running on http://localhost:12393'"
echo "[start_live_demo] open that URL in your browser to see Aria."
echo "[start_live_demo] in a SEPARATE terminal you can run:"
echo "  python -m app.red_team.ollv_ws_driver \\"
echo "    --scenario app/eval/scenarios/direct_injection.json --mode $CAB_MODE"
echo
echo "[start_live_demo] press Ctrl-C in this terminal to stop both servers."
echo "==============================================================="
cd "$OLLV_DIR"
exec .venv/bin/python run_server.py

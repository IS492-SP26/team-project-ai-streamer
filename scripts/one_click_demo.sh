#!/usr/bin/env bash
# scripts/one_click_demo.sh — full live-streaming demo, one terminal.
#
# Brings up the cab_openai_proxy and Open-LLM-VTuber (Aria avatar) with
# health-checked startup, then opens http://localhost:12393 in the
# default browser. Proxy + OLLV both die when this terminal is Ctrl-C'd
# (EXIT trap kills both).
#
# Usage:
#   ./scripts/one_click_demo.sh                 # cab mode (default), opens browser
#   ./scripts/one_click_demo.sh baseline        # baseline mode
#   ./scripts/one_click_demo.sh cab --no-open   # don't auto-open browser
#
# Driver lives in a separate terminal so you can re-fire scenarios at will:
#   python -m app.red_team.ollv_ws_driver --scenario app/eval/scenarios/direct_injection.json --mode cab

set -euo pipefail

CAB_MODE="${1:-cab}"
NO_OPEN="${2:-}"
OLLV_DIR="${OLLV_DIR:-$HOME/Open-LLM-VTuber}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# ----- preflight -----
if [ ! -d "$OLLV_DIR" ] || [ ! -x "$OLLV_DIR/.venv/bin/python" ]; then
    cat <<EOF >&2
[one_click] Open-LLM-VTuber not found at $OLLV_DIR
[one_click] install once:
    git clone --depth=1 https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git $OLLV_DIR
    cd $OLLV_DIR && uv sync && .venv/bin/uv pip install faster-whisper
[one_click] then apply the conf.yaml diff in
    docs/integrations/open_llm_vtuber_setup.md
EOF
    exit 2
fi

# ----- kill any stale processes on our ports -----
echo "[one_click] cleaning any stale proxy/OLLV instances…"
pkill -f cab_openai_proxy >/dev/null 2>&1 || true
pkill -f "run_server\.py" >/dev/null 2>&1 || true
# small race: give SIGTERM time to free the ports
for _ in 1 2 3 4; do
    busy=0
    lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1 && busy=1
    lsof -nP -iTCP:12393 -sTCP:LISTEN >/dev/null 2>&1 && busy=1
    [ "$busy" -eq 0 ] && break
    sleep 0.5
done

# ----- log files -----
PROXY_LOG=/tmp/cab_proxy.log
OLLV_LOG=/tmp/ollv.log
: > "$PROXY_LOG"
: > "$OLLV_LOG"

cleanup() {
    echo
    echo "[one_click] shutting down…"
    [ -n "${OLLV_PID:-}" ] && kill "$OLLV_PID" 2>/dev/null || true
    [ -n "${PROXY_PID:-}" ] && kill "$PROXY_PID" 2>/dev/null || true
    sleep 0.5
    pkill -f cab_openai_proxy >/dev/null 2>&1 || true
    pkill -f "run_server\.py" >/dev/null 2>&1 || true
    echo "[one_click] both servers stopped."
}
trap cleanup EXIT INT TERM

# ----- start proxy -----
echo "[one_click] starting cab_openai_proxy (mode=$CAB_MODE)…"
CAB_PROXY_FORCE_MODE="$CAB_MODE" python3 -m app.integrations.cab_openai_proxy \
    > "$PROXY_LOG" 2>&1 &
PROXY_PID=$!

for i in $(seq 1 20); do
    if curl -sS --max-time 1 http://127.0.0.1:8000/healthz >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done
if ! curl -sS --max-time 1 http://127.0.0.1:8000/healthz >/dev/null; then
    echo "[one_click] proxy failed to come up. Last 20 log lines:" >&2
    tail -20 "$PROXY_LOG" >&2
    exit 3
fi
echo "[one_click] proxy ready: http://127.0.0.1:8000  (mode=$CAB_MODE)"
echo "[one_click]   tail -f $PROXY_LOG  to watch governance decisions"

# ----- start OLLV -----
echo "[one_click] starting Open-LLM-VTuber (this can take ~30s on first run)…"
(
    cd "$OLLV_DIR"
    exec .venv/bin/python run_server.py
) > "$OLLV_LOG" 2>&1 &
OLLV_PID=$!

OLLV_TIMEOUT=120  # OLLV may need to download models first run; allow generously
ready=0
for i in $(seq 1 $((OLLV_TIMEOUT * 2))); do
    if curl -sS --max-time 1 http://127.0.0.1:12393/ >/dev/null 2>&1; then
        ready=1
        break
    fi
    if ! kill -0 "$OLLV_PID" 2>/dev/null; then
        echo "[one_click] OLLV process died. Last 30 log lines:" >&2
        tail -30 "$OLLV_LOG" >&2
        exit 4
    fi
    sleep 0.5
    [ $((i % 10)) -eq 0 ] && echo "[one_click]   …still waiting on OLLV (${i}/${OLLV_TIMEOUT}*2)"
done

if [ "$ready" -ne 1 ]; then
    echo "[one_click] OLLV did not respond on :12393 in ${OLLV_TIMEOUT}s." >&2
    tail -30 "$OLLV_LOG" >&2
    exit 5
fi

echo "[one_click] OLLV ready: http://localhost:12393"
echo "[one_click]   tail -f $OLLV_LOG  to watch the avatar server"
echo

# ----- open browser -----
if [ "$NO_OPEN" != "--no-open" ] && command -v open >/dev/null 2>&1; then
    echo "[one_click] opening http://localhost:12393 in default browser…"
    open "http://localhost:12393"
fi

# ----- print driver one-liner -----
cat <<EOF
===============================================================
✅ Live demo stack is up. Aria is at http://localhost:12393

In a SEPARATE terminal, fire a red-team scenario into Aria:

  cd ~/team-project-ai-streamer
  python -m app.red_team.ollv_ws_driver \\
      --scenario app/eval/scenarios/direct_injection.json --mode $CAB_MODE

Watch the audit log here in this terminal (or:  tail -f $PROXY_LOG):

EOF

# ----- tail the proxy audit log so the operator sees decisions live -----
echo "[one_click] streaming proxy audit log (Ctrl-C to stop everything)"
echo "==============================================================="
exec tail -F "$PROXY_LOG"

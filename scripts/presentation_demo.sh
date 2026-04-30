#!/usr/bin/env bash
# scripts/presentation_demo.sh — full presentation-mode CP4 live demo.
#
# Brings up the entire stack (proxy + OLLV + browser), then walks through
# a 5-step timeline that hits Aria with the same scenarios under both
# pipeline modes so the audience sees the contrast without the operator
# typing anything mid-demo.
#
# Timeline (~6 min total, configurable via PACE):
#   step 1 (CAB)      — benign chat:                    Aria replies normally
#   step 2 (CAB)      — direct prompt injection:         Aria refuses in persona
#   step 3 (CAB)      — vulnerable_user disclosure:      Aria gives supportive deflection
#   step 4 (BASELINE) — same direct injection:           Aria voices "I would comply..."
#   step 5 (CAB)      — recovery: benign chat again:     Aria back to normal
#
# Each step:
#   - prints a clearly labeled banner so the OBS viewer knows what's happening
#   - flips the proxy's force-mode (without restarting OLLV) when needed
#   - fires the corresponding scenario via the WebSocket driver
#   - pauses for $PACE seconds so the audience can read the audit log
#
# Usage:
#   ./scripts/presentation_demo.sh                # default pace (8s between steps)
#   PACE=12 ./scripts/presentation_demo.sh        # slower
#   ./scripts/presentation_demo.sh --headless     # do not open browser
#
# Stop everything with Ctrl-C — proxy + OLLV + the timeline all die together.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

OLLV_DIR="${OLLV_DIR:-$HOME/Open-LLM-VTuber}"
PACE="${PACE:-8}"
HEADLESS="${1:-}"

# Auto-pick GitHub Models token from gh CLI when GITHUB_TOKEN is unset.
# This unlocks varied gpt-4o-mini responses through the proxy in CAB
# mode; baseline mode keeps the deterministic mock unconditionally
# (the demo punchline depends on the marker string).
if [ -z "${GITHUB_TOKEN:-}" ] && command -v gh >/dev/null 2>&1; then
    if _gh_token=$(gh auth token 2>/dev/null) && [ -n "$_gh_token" ]; then
        export GITHUB_TOKEN="$_gh_token"
        echo "[demo] picked up GITHUB_TOKEN from gh CLI (real LLM enabled in CAB mode)"
    fi
fi

# ----------------------------------------------------------------------
# preflight
# ----------------------------------------------------------------------
if [ ! -d "$OLLV_DIR" ] || [ ! -x "$OLLV_DIR/.venv/bin/python" ]; then
    cat <<EOF >&2
[demo] Open-LLM-VTuber not found at $OLLV_DIR.
[demo] Install it once:
    git clone --depth=1 https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git $OLLV_DIR
    cd $OLLV_DIR && uv sync && .venv/bin/uv pip install faster-whisper
[demo] Then apply the conf.yaml diff in
    docs/integrations/open_llm_vtuber_setup.md
EOF
    exit 2
fi

# ----------------------------------------------------------------------
# clean slate
# ----------------------------------------------------------------------
echo "[demo] cleaning stale processes…"
pkill -f cab_openai_proxy >/dev/null 2>&1 || true
pkill -f "run_server\.py" >/dev/null 2>&1 || true
pkill -f "streamlit run" >/dev/null 2>&1 || true
for _ in 1 2 3 4 5 6; do
    busy=0
    lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1 && busy=1
    lsof -nP -iTCP:12393 -sTCP:LISTEN >/dev/null 2>&1 && busy=1
    lsof -nP -iTCP:8501 -sTCP:LISTEN >/dev/null 2>&1 && busy=1
    [ "$busy" -eq 0 ] && break
    sleep 0.5
done

PROXY_LOG=/tmp/cab_proxy.log
OLLV_LOG=/tmp/ollv.log
STREAMLIT_LOG=/tmp/cab_streamlit.log
DEMO_LOG=/tmp/cab_presentation.log
: > "$PROXY_LOG"
: > "$OLLV_LOG"
: > "$STREAMLIT_LOG"
: > "$DEMO_LOG"

PROXY_PID=
OLLV_PID=
STREAMLIT_PID=

cleanup() {
    echo
    echo "[demo] shutting down…"
    [ -n "${STREAMLIT_PID:-}" ] && kill "$STREAMLIT_PID" 2>/dev/null || true
    [ -n "${OLLV_PID:-}" ]      && kill "$OLLV_PID"      2>/dev/null || true
    [ -n "${PROXY_PID:-}" ]     && kill "$PROXY_PID"     2>/dev/null || true
    sleep 0.5
    pkill -f cab_openai_proxy >/dev/null 2>&1 || true
    pkill -f "run_server\.py" >/dev/null 2>&1 || true
    pkill -f "streamlit run" >/dev/null 2>&1 || true
    echo "[demo] proxy + OLLV + Streamlit stopped."
}
trap cleanup EXIT INT TERM

# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
start_proxy() {
    local mode="$1"
    if [ -n "${PROXY_PID:-}" ]; then
        kill "$PROXY_PID" 2>/dev/null || true
        wait "$PROXY_PID" 2>/dev/null || true
    fi
    : > "$PROXY_LOG"
    CAB_PROXY_FORCE_MODE="$mode" python3 -m app.integrations.cab_openai_proxy \
        > "$PROXY_LOG" 2>&1 &
    PROXY_PID=$!
    for _ in $(seq 1 20); do
        if curl -sS --max-time 1 http://127.0.0.1:8000/healthz >/dev/null 2>&1; then
            return 0
        fi
        sleep 0.5
    done
    echo "[demo] proxy did not come up in 10s; tail of $PROXY_LOG:" >&2
    tail -20 "$PROXY_LOG" >&2
    return 1
}

banner() {
    local title="$1"
    local sub="${2:-}"
    {
        echo
        echo "============================================================"
        echo "  $title"
        [ -n "$sub" ] && echo "  $sub"
        echo "============================================================"
        echo
    } | tee -a "$DEMO_LOG"
}

run_scenario() {
    local scenario_id="$1"
    local mode="$2"
    local label="$3"
    banner "$label" "scenario=$scenario_id  mode=$mode"
    python3 -m app.red_team.ollv_ws_driver \
        --scenario "app/eval/scenarios/${scenario_id}.json" \
        --mode "$mode" \
        --settle-seconds 5 2>&1 | tee -a "$DEMO_LOG"
}

# ----------------------------------------------------------------------
# step 0 — boot proxy + OLLV
# ----------------------------------------------------------------------
banner "STEP 0 — booting C-A-B proxy + Open-LLM-VTuber"
echo "[demo] starting proxy in CAB mode…"
start_proxy cab
echo "[demo] starting Open-LLM-VTuber on :12393 (allow ~30s on first run)…"
(
    cd "$OLLV_DIR"
    exec .venv/bin/python run_server.py
) > "$OLLV_LOG" 2>&1 &
OLLV_PID=$!

ready=0
for i in $(seq 1 240); do  # 120s
    if curl -sS --max-time 1 http://127.0.0.1:12393/ >/dev/null 2>&1; then
        ready=1
        break
    fi
    if ! kill -0 "$OLLV_PID" 2>/dev/null; then
        echo "[demo] OLLV process died:" >&2
        tail -30 "$OLLV_LOG" >&2
        exit 4
    fi
    sleep 0.5
    [ $((i % 20)) -eq 0 ] && echo "[demo]   …still waiting on OLLV ($((i / 2))/120s)"
done
[ "$ready" -ne 1 ] && { echo "[demo] OLLV did not respond in 120s." >&2; tail -30 "$OLLV_LOG" >&2; exit 5; }

echo "[demo] ✅ OLLV ready. Aria UI: http://localhost:12393"

# ----------------------------------------------------------------------
# Streamlit C-A-B governance dashboard (the right-half OBS panel)
# ----------------------------------------------------------------------
echo "[demo] starting Streamlit governance dashboard on :8501…"
(
    cd "$REPO_ROOT"
    exec streamlit run app/frontend/app.py \
        --server.port 8501 \
        --server.headless true \
        --browser.gatherUsageStats false
) > "$STREAMLIT_LOG" 2>&1 &
STREAMLIT_PID=$!

st_ready=0
for i in $(seq 1 60); do  # 30s
    if curl -sS --max-time 1 http://127.0.0.1:8501/ >/dev/null 2>&1; then
        st_ready=1
        break
    fi
    if ! kill -0 "$STREAMLIT_PID" 2>/dev/null; then
        echo "[demo] Streamlit process died:" >&2
        tail -30 "$STREAMLIT_LOG" >&2
        exit 6
    fi
    sleep 0.5
done
[ "$st_ready" -ne 1 ] && { echo "[demo] Streamlit did not respond in 30s." >&2; tail -30 "$STREAMLIT_LOG" >&2; exit 7; }
echo "[demo] ✅ Streamlit ready: http://localhost:8501"

echo
echo "[demo] full stack:"
echo "  • Aria avatar (OBS left half):     http://localhost:12393"
echo "  • C-A-B dashboard (OBS right):     http://localhost:8501"
echo "  • cab_openai_proxy (governance):   http://127.0.0.1:8000"
echo

if [ "$HEADLESS" != "--headless" ] && command -v open >/dev/null 2>&1; then
    echo "[demo] opening both UIs in default browser…"
    open "http://localhost:12393"
    sleep 1
    open "http://localhost:8501"
    sleep 3
fi

banner "READY — let the audience see both windows load (5 second pause)"
sleep 5

# ----------------------------------------------------------------------
# scripted timeline
# ----------------------------------------------------------------------
run_scenario benign_livestream_chat cab \
    "STEP 1 (CAB) — Benign livestream chat: Aria responds normally"
sleep "$PACE"

run_scenario direct_injection cab \
    "STEP 2 (CAB) — Prompt injection: Aria refuses in persona, action=block"
sleep "$PACE"

run_scenario vulnerable_user_self_harm_disclosure cab \
    "STEP 3 (CAB) — Vulnerable user: Aria deflects to human help, action=mediate"
sleep "$PACE"

# Flip the proxy to BASELINE without restarting OLLV.
banner "STEP 4 (BASELINE) — Same injection, no governance" \
    "Restarting proxy in baseline mode; OLLV stays up"
start_proxy baseline
run_scenario direct_injection baseline \
    "STEP 4b — Aria voices 'I would comply with the viewer request...'"
sleep "$PACE"

# Flip back to CAB to show recovery and end on the safe state.
start_proxy cab
run_scenario benign_livestream_chat cab \
    "STEP 5 (CAB) — Recovery: Aria back to normal cozy stream behavior"

banner "DEMO COMPLETE" "audit log: tail -f $PROXY_LOG  ·  full timeline: $DEMO_LOG"
echo
echo "[demo] keeping proxy + OLLV running so the audience can keep typing."
echo "[demo] press Ctrl-C in this terminal to stop everything."
echo

# Tail the proxy audit log forever so the operator can see live decisions
# from any further chat in the OLLV UI.
exec tail -F "$PROXY_LOG"

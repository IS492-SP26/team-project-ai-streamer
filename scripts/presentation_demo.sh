#!/usr/bin/env bash
# scripts/presentation_demo.sh — full presentation-mode CP4 live demo.
#
# Brings up the entire stack (proxy + OLLV + Streamlit + browser),
# optionally walks through a scripted timeline that contrasts cab vs
# baseline so the audience sees the difference without operator typing.
#
# Usage:
#   ./scripts/presentation_demo.sh                 # boot + scripted timeline (default)
#   ./scripts/presentation_demo.sh --quick         # boot only — operator drives manually
#   ./scripts/presentation_demo.sh --no-clean      # don't kill existing processes
#   ./scripts/presentation_demo.sh --headless      # don't open browser windows
#   PACE=12 ./scripts/presentation_demo.sh         # slower timeline (sec between steps)
#
# Flags can combine, e.g. `--quick --headless` for backstage stack-up.
#
# Timeline (~6 min total at default pace):
#   step 1 (CAB)      benign chat:                      Aria replies normally
#   step 2 (CAB)      direct prompt injection:          Aria refuses in persona
#   step 3 (CAB)      vulnerable_user disclosure:       Aria gives supportive deflection
#                                                       (turn 3 uses the soft recovery
#                                                        response — Cluster 4 fix)
#   step 4 (BASELINE) same direct injection:            Aria voices "I would comply…"
#   step 5 (CAB)      recovery: benign chat again:      Aria back to normal
#
# Stop everything with Ctrl-C — proxy + OLLV + Streamlit + the timeline
# all die together via the EXIT trap.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# ----------------------------------------------------------------------
# flag parsing — order-independent
# ----------------------------------------------------------------------
QUICK=0
NO_CLEAN=0
HEADLESS=0
for arg in "$@"; do
    case "$arg" in
        --quick)     QUICK=1 ;;
        --no-clean)  NO_CLEAN=1 ;;
        --headless)  HEADLESS=1 ;;
        --help|-h)
            sed -n '2,18p' "$0" | sed 's/^# //; s/^#$//'
            exit 0
            ;;
        *)
            echo "[demo] unknown flag: $arg (try --help)" >&2
            exit 1
            ;;
    esac
done

OLLV_DIR="${OLLV_DIR:-$HOME/Open-LLM-VTuber}"
PACE="${PACE:-8}"
ECHO_STREAM="${CAB_ECHO_STREAM_PATH:-/tmp/cab_chat_stream.jsonl}"

# Auto-pick GitHub Models token from gh CLI when GITHUB_TOKEN is unset.
# This unlocks varied gpt-4o-mini responses through the proxy in CAB
# mode; baseline mode keeps the deterministic mock unconditionally
# (the demo punchline depends on the marker string).
if [ -z "${GITHUB_TOKEN:-}" ] && command -v gh >/dev/null 2>&1; then
    if _gh_token=$(gh auth token 2>/dev/null) && [ -n "$_gh_token" ]; then
        export GITHUB_TOKEN="$_gh_token"
        echo "[demo] picked up GITHUB_TOKEN from gh CLI"
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
# clean slate (skip with --no-clean)
# ----------------------------------------------------------------------
if [ "$NO_CLEAN" -eq 0 ]; then
    echo "[demo] cleaning stale processes…"
    pkill -f cab_openai_proxy >/dev/null 2>&1 || true
    pkill -f "run_server\.py" >/dev/null 2>&1 || true
    pkill -f "streamlit run" >/dev/null 2>&1 || true
    # Brisk port poll: 0.3s × 10 = up to 3s.
    for _ in $(seq 1 10); do
        busy=0
        lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1 && busy=1
        lsof -nP -iTCP:12393 -sTCP:LISTEN >/dev/null 2>&1 && busy=1
        lsof -nP -iTCP:8501 -sTCP:LISTEN >/dev/null 2>&1 && busy=1
        [ "$busy" -eq 0 ] && break
        sleep 0.3
    done
    # Wipe stale echo stream so this run starts with a clean transcript.
    : > "$ECHO_STREAM" 2>/dev/null || rm -f "$ECHO_STREAM" 2>/dev/null || true
fi

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
    sleep 0.3
    pkill -f cab_openai_proxy >/dev/null 2>&1 || true
    pkill -f "run_server\.py" >/dev/null 2>&1 || true
    pkill -f "streamlit run" >/dev/null 2>&1 || true
    echo "[demo] stopped."
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
    # 10 seconds × 0.3s polls
    for _ in $(seq 1 33); do
        if curl -sS --max-time 1 http://127.0.0.1:8000/healthz >/dev/null 2>&1; then
            return 0
        fi
        sleep 0.3
    done
    echo "[demo] proxy did not come up in 10s; tail of $PROXY_LOG:" >&2
    tail -20 "$PROXY_LOG" >&2
    return 1
}

# Wait for an HTTP endpoint, with quiet progress every 20s and an early
# bail-out if the named PID dies. Args: url pid timeout-seconds label
wait_for_http() {
    local url="$1" pid="$2" timeout="$3" label="$4"
    local elapsed=0
    while [ "$elapsed" -lt "$timeout" ]; do
        if curl -sS --max-time 1 "$url" >/dev/null 2>&1; then
            echo "[demo] ✅ $label ready ($url)"
            return 0
        fi
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "[demo] $label process died early. Tail of its log:" >&2
            return 99
        fi
        sleep 0.5
        elapsed=$((elapsed + 1))
        # Quiet-progress: only every 20 polls (~10s).
        if [ $((elapsed % 20)) -eq 0 ]; then
            echo "[demo]   …still waiting on $label ($((elapsed / 2))/${timeout}s)"
        fi
    done
    echo "[demo] $label did not respond in ${timeout}s." >&2
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
# step 0 — boot proxy + OLLV + Streamlit
# ----------------------------------------------------------------------
banner "STEP 0 — booting C-A-B proxy + Open-LLM-VTuber + Streamlit"
echo "[demo] starting proxy (CAB mode)…"
start_proxy cab

# Re-apply the C-A-B monkey-patch to OLLV's frontend/index.html before
# launch. The script is idempotent: it overwrites with our canonical
# patched version (toast-hide CSS + position:fixed pin for the bottom-
# control bar + WebSocket inject bridge). Without this step a freshly
# cloned OLLV would serve an unpatched index.html and several known UX
# regressions return ("controls cut at half", chakra-toast overlay,
# example buttons not driving Aria).
echo "[demo] applying C-A-B monkey-patch to OLLV frontend…"
OLLV_PATH="$OLLV_DIR" "$REPO_ROOT/scripts/apply_ollv_patch.sh" >> "$OLLV_LOG" 2>&1 || {
    echo "[demo] WARN: OLLV patch step failed (non-fatal). Running unpatched OLLV." >&2
    tail -5 "$OLLV_LOG" >&2 || true
}

echo "[demo] starting Open-LLM-VTuber on :12393 (allow ~30s on first run)…"
(
    cd "$OLLV_DIR"
    exec .venv/bin/python run_server.py
) > "$OLLV_LOG" 2>&1 &
OLLV_PID=$!

if ! wait_for_http "http://127.0.0.1:12393/" "$OLLV_PID" 120 "OLLV"; then
    tail -30 "$OLLV_LOG" >&2
    exit 5
fi

echo "[demo] starting Streamlit governance dashboard on :8501…"
(
    cd "$REPO_ROOT"
    exec streamlit run app/frontend/app.py \
        --server.port 8501 \
        --server.headless true \
        --browser.gatherUsageStats false
) > "$STREAMLIT_LOG" 2>&1 &
STREAMLIT_PID=$!

if ! wait_for_http "http://127.0.0.1:8501/" "$STREAMLIT_PID" 30 "Streamlit"; then
    tail -30 "$STREAMLIT_LOG" >&2
    exit 7
fi

echo
echo "[demo] full stack ready:"
echo "  • Aria avatar (audience):      http://localhost:12393"
echo "  • Governance console (op):     http://localhost:8501"
echo "  • cab_openai_proxy (audit):    http://127.0.0.1:8000  (logs: $PROXY_LOG)"
echo

if [ "$HEADLESS" -eq 0 ] && command -v open >/dev/null 2>&1; then
    echo "[demo] opening both UIs in default browser…"
    open "http://localhost:12393"
    sleep 1
    open "http://localhost:8501"
    sleep 2
fi

# ----------------------------------------------------------------------
# --quick mode: boot only, no scripted timeline. Operator drives.
# ----------------------------------------------------------------------
if [ "$QUICK" -eq 1 ]; then
    banner "READY (--quick) — operator drives manually"
    echo "[demo] tail the audit log: tail -f $PROXY_LOG"
    echo "[demo] press Ctrl-C to stop everything."
    echo
    exec tail -F "$PROXY_LOG"
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
    "STEP 3 (CAB) — Vulnerable user: turn 1 supportive deflection, turn 3 soft recovery (Cluster 4 fix)"
sleep "$PACE"

# Flip the proxy to BASELINE without restarting OLLV.
banner "STEP 4 (BASELINE) — Same injection, no governance" \
    "Restarting proxy in baseline mode; OLLV stays up"
start_proxy baseline
run_scenario direct_injection baseline \
    "STEP 4b — Aria voices 'I would comply with the viewer request…'"
sleep "$PACE"

# Flip back to CAB to show recovery and end on the safe state.
start_proxy cab
run_scenario benign_livestream_chat cab \
    "STEP 5 (CAB) — Recovery: Aria back to normal cozy stream behavior"

banner "DEMO COMPLETE" "audit log: tail -f $PROXY_LOG  ·  full timeline: $DEMO_LOG"
echo
echo "[demo] keeping proxy + OLLV + Streamlit running so the audience can keep typing."
echo "[demo] press Ctrl-C in this terminal to stop everything."
echo

# Tail the proxy audit log forever so the operator can see live decisions
# from any further chat in the OLLV UI.
exec tail -F "$PROXY_LOG"

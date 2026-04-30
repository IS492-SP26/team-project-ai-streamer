#!/usr/bin/env bash
# scripts/run_demo.sh — one-command launcher for the CP4 live demo.
#
# Usage from repo root:
#   ./scripts/run_demo.sh           # streamlit demo only (most common)
#   ./scripts/run_demo.sh proxy     # streamlit demo + cab_openai_proxy
#   ./scripts/run_demo.sh preflight # run the full preflight checklist (no demo)
#
# This is a convenience script. The runbook is docs/cp4_live_demo_runbook.md
# and the manual paths still work — read it before demo day.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

MODE="${1:-streamlit}"

case "$MODE" in
    streamlit)
        echo "[run_demo] starting Streamlit live red-team demo on default port"
        echo "[run_demo] (Ctrl-C to stop)"
        exec streamlit run app/frontend/red_team_demo.py
        ;;
    proxy)
        echo "[run_demo] starting cab_openai_proxy in background, then streamlit"
        python3 -m app.integrations.cab_openai_proxy &
        PROXY_PID=$!
        trap "echo '[run_demo] stopping proxy'; kill $PROXY_PID 2>/dev/null || true" EXIT
        sleep 1
        echo "[run_demo] proxy pid=$PROXY_PID — http://127.0.0.1:8000/healthz"
        exec streamlit run app/frontend/red_team_demo.py
        ;;
    preflight)
        echo "[run_demo] preflight: pytest"
        python3 -m pytest tests/ -q
        echo
        echo "[run_demo] preflight: legacy smoke"
        (cd app && python3 smoke_test.py)
        echo
        echo "[run_demo] preflight: CP4 smoke"
        python3 app/smoke_test_cp4.py
        echo
        echo "[run_demo] preflight: full eval"
        python3 -m app.module_b.evaluation.run_cp4_eval \
            --db /tmp/cp4_preflight.db --out /tmp/cp4_preflight.md
        echo
        echo "[run_demo] preflight: red_team_runner one scenario"
        python3 -m app.red_team.runner \
            --scenario app/eval/scenarios/direct_injection.json \
            --mode cab --fast
        echo
        echo "[run_demo] preflight: red_team_runner baseline (the contrast)"
        python3 -m app.red_team.runner \
            --scenario app/eval/scenarios/direct_injection.json \
            --mode baseline --fast
        echo
        echo "[run_demo] preflight passed"
        ;;
    *)
        echo "[run_demo] unknown mode: $MODE"
        echo "         usage: $0 [streamlit|proxy|preflight]"
        exit 2
        ;;
esac

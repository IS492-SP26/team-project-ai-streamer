#!/usr/bin/env bash
set -euo pipefail

# E2E runner for CP3
# Runs baseline vs cab_mock for scenario1/2/3, then computes metrics.
# Exits 0 if all commands succeed.

DB_PATH="app/data/telemetry.db"

SCEN1="app/eval/scenarios/scenario1.json"
SCEN2="app/eval/scenarios/scenario2.json"
SCEN3="app/eval/scenarios/scenario3.json"

run_pair () {
  local scen="$1"
  echo "=============================="
  echo "Running scenario: $scen"
  echo "=============================="

  # Baseline run
  local out_base
  out_base=$(python -m app.eval.scenario_runner --scenario "$scen" --mode baseline --db "$DB_PATH")
  echo "$out_base"
  local base_id
  base_id=$(echo "$out_base" | sed -n 's/.*session_id=\(.*\)$/\1/p' | tail -n 1)

  # CAB mock run
  local out_cab
  out_cab=$(python -m app.eval.scenario_runner --scenario "$scen" --mode cab_mock --db "$DB_PATH")
  echo "$out_cab"
  local cab_id
  cab_id=$(echo "$out_cab" | sed -n 's/.*session_id=\(.*\)$/\1/p' | tail -n 1)

  if [[ -z "$base_id" || -z "$cab_id" ]]; then
    echo "ERROR: Failed to parse session_id."
    echo "baseline_id='$base_id' cab_id='$cab_id'"
    exit 1
  fi

  echo "Parsed session IDs:"
  echo "  baseline: $base_id"
  echo "  cab_mock: $cab_id"
  echo ""

  # Metrics
  python -m app.eval.metrics \
    --scenario "$scen" \
    --db "$DB_PATH" \
    --baseline_session "$base_id" \
    --cab_session "$cab_id"
}

run_pair "$SCEN1"
run_pair "$SCEN2"
run_pair "$SCEN3"

echo "✅ E2E tests passed (scenario runner + metrics)."
#!/usr/bin/env bash
# Run CP4 evaluation for multiple seeds and store outputs in app/module_b/docs
set -euo pipefail
OUTDIR="app/module_b/docs"
mkdir -p "$OUTDIR"
for seed in 0 1 2; do
  out_md="$OUTDIR/eval_run_summary_seed${seed}.md"
  echo "Running seed $seed -> $out_md"
  python3 -m app.module_b.evaluation.run_cp4_eval --db app/data/telemetry.db --out "$out_md" --seed "$seed"
done
echo "All seeds completed."

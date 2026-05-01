#!/usr/bin/env bash
# Apply the C-A-B demo's monkey-patch to a local Open-LLM-VTuber clone.
#
# Why this script exists:
#   The demo embeds OLLV's frontend at localhost:12393 in an iframe and
#   needs three behaviors that OLLV does not provide out of the box:
#     1) WebSocket interception so the parent Streamlit page can
#        inject CAB_INJECT_CHAT events into Aria's existing /client-ws
#        session (used by example buttons + red-team auto-play).
#     2) Hide chakra-toast notifications (they overlay the avatar).
#     3) Pin OLLV's bottom-control bar to the iframe's bottom edge via
#        position:fixed so it cannot be clipped by an undersized
#        iframe ("controls cut at half" complaint that recurred several
#        times during demo prep).
#
#   The patch lives in this repo as `scripts/ollv_index_html.patched.html`
#   (the full patched file). This script copies it over the OLLV clone's
#   `frontend/index.html`. Running again is idempotent.
#
# Usage:
#   ./scripts/apply_ollv_patch.sh                 # default OLLV path
#   OLLV_PATH=/path/to/Open-LLM-VTuber ./scripts/apply_ollv_patch.sh
#
# Prerequisite: clone Open-LLM-VTuber per docs/integrations/open_llm_vtuber_setup.md
# (default location: ~/Open-LLM-VTuber).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATCH_SOURCE="$REPO_ROOT/scripts/ollv_index_html.patched.html"
OLLV_PATH="${OLLV_PATH:-$HOME/Open-LLM-VTuber}"
TARGET="$OLLV_PATH/frontend/index.html"

if [[ ! -f "$PATCH_SOURCE" ]]; then
  echo "ERROR: patched template missing: $PATCH_SOURCE" >&2
  exit 1
fi

if [[ ! -d "$OLLV_PATH" ]]; then
  echo "ERROR: OLLV clone not found at $OLLV_PATH" >&2
  echo "       Set OLLV_PATH=/path/to/Open-LLM-VTuber and re-run." >&2
  exit 1
fi

if [[ ! -f "$TARGET" ]]; then
  echo "ERROR: $TARGET does not exist — is OLLV's frontend installed?" >&2
  echo "       See docs/integrations/open_llm_vtuber_setup.md" >&2
  exit 1
fi

# Quick check: is the patch already applied? Look for a sentinel string.
if grep -q "C-A-B demo CSS overrides" "$TARGET"; then
  echo "[patch] OLLV index.html already patched — verifying integrity..."
fi

# Always overwrite — the source-of-truth lives in this repo, not OLLV's.
# Any future edits to the patch should be made to scripts/ollv_index_html.patched.html
# and re-applied via this script.
cp "$PATCH_SOURCE" "$TARGET"
echo "[patch] copied $PATCH_SOURCE → $TARGET"

# Verify sentinel + position:fixed CSS made it through.
if grep -q "C-A-B demo CSS overrides" "$TARGET" && \
   grep -q "position: fixed" "$TARGET" && \
   grep -q "CAB_INJECT_CHAT" "$TARGET"; then
  echo "[patch] ✅ all three patches present (toast hide, control-bar pin, WS bridge)"
else
  echo "[patch] ⚠️  patch verification failed — check $TARGET" >&2
  exit 1
fi

# If OLLV is currently running, advise restart so it serves the new HTML.
if lsof -nP -iTCP:12393 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[patch] OLLV is currently running on :12393."
  echo "[patch] Restart it (e.g. via scripts/presentation_demo.sh) to serve"
  echo "[patch] the patched HTML. Browser-side iframe also needs reload."
fi

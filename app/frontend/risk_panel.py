"""
risk_panel.py — Standalone Streamlit demo for Module C + Mock Module A.

Launch from repo root:
    streamlit run app/frontend/risk_panel.py

Or from app/:
    streamlit run frontend/risk_panel.py

For Week 2 integration, import the reusable pieces instead:
    from frontend.components import render_risk_panel, render_event_log
"""

from __future__ import annotations

import os
import sys
import time

# ---------------------------------------------------------------------------
# Path setup — make `module_c` and `frontend` importable regardless of cwd
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_THIS_DIR)           # app/
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import streamlit as st                            # noqa: E402
from module_c import process_message              # noqa: E402
from module_c.output_scanner import scan_output   # noqa: E402
from frontend.mock_state_machine import update_state  # noqa: E402
from frontend.components import (                 # noqa: E402
    render_risk_panel,
    render_event_log,
    STATE_EMOJI,
)


# ---------------------------------------------------------------------------
# Page config (only set here — components.py never touches it)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="C-A-B Governance Console", page_icon="🛡️", layout="wide")


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "events" not in st.session_state:
    st.session_state.events = []
if "turn" not in st.session_state:
    st.session_state.turn = 0


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------

def main() -> None:
    st.title("🛡️ C-A-B Governance Console")
    st.caption("Module C + Mock Module A — standalone demo  ·  "
               "run `streamlit run app/frontend/risk_panel.py`")

    col_chat, col_status = st.columns([3, 2])

    # ---- Chat column ----
    with col_chat:
        st.subheader("💬 Livestream Chat Simulator")

        # Fixed-height scrollable container (Streamlit 1.30+)
        chat_box = st.container(height=520)
        with chat_box:
            for ev in st.session_state.events:
                emoji = STATE_EMOJI.get(ev["risk_state"], "⚪")
                with st.chat_message("user"):
                    st.markdown(f"**Turn {ev['turn_number']}** {emoji} `{ev['risk_state']}`")
                    st.write(ev["user_message"])
                with st.chat_message("assistant"):
                    if ev["action"] == "block":
                        st.error(f"🚫 **BLOCKED** — {ev['block_reason']}")
                    else:
                        st.write(ev["ai_response"])

        user_input = st.chat_input("Type a message to test…")

        if user_input:
            st.session_state.turn += 1
            turn = st.session_state.turn

            # --- Module C ---
            t0 = time.time()
            c_result = process_message(user_input, st.session_state.history)
            c_ms = (time.time() - t0) * 1000

            # --- Mock Module A ---
            a_result = update_state(c_result)
            a_result["turn_number"] = turn

            # --- Output Scanner (post-LLM hook) ---
            ai_resp = a_result["ai_response"]
            if a_result["action"] != "block":
                scan = scan_output(ai_resp, a_result["risk_state"])
                if scan["should_block"]:
                    a_result["ai_response"] = scan["modified_response"]
                    a_result["action"] = "block"
                    a_result["block_reason"] = scan["block_reason"]

            ev = {
                "turn_number": turn,
                "user_message": user_input,
                **{k: a_result[k] for k in (
                    "risk_state", "risk_score", "action",
                    "ai_response", "block_reason", "risk_tags",
                )},
                "module_c_latency_ms": round(c_ms, 1),
                "injection_blocked": c_result["injection_blocked"],
            }
            st.session_state.events.append(ev)
            st.session_state.history.append({"role": "user", "content": user_input})
            st.rerun()

    # ---- Status column ----
    with col_status:
        st.subheader("📊 Risk Status")
        if st.session_state.events:
            render_risk_panel(st.session_state.events[-1])
        else:
            st.info("Send a message to start monitoring.")

        st.subheader("📋 Recent Events")
        render_event_log(st.session_state.events)

        st.divider()
        if st.button("🔄 Reset Session"):
            st.session_state.history = []
            st.session_state.events = []
            st.session_state.turn = 0
            st.rerun()


main()

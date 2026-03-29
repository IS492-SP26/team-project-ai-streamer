"""
risk_panel.py — Standalone Streamlit demo for Module C + Mock Module A.

Supports dark/light mode toggle via sidebar.

Launch from repo root:
    streamlit run app/frontend/risk_panel.py

For Week 2 integration, import the reusable pieces instead:
    from frontend.components import render_risk_panel, render_event_log
    from frontend.theme import get_theme, inject_theme_css, render_theme_toggle
"""

from __future__ import annotations

import os
import sys
import time

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR = os.path.dirname(_THIS_DIR)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import streamlit as st                            # noqa: E402
from module_c import process_message              # noqa: E402
from module_c.output_scanner import scan_output   # noqa: E402
from frontend.mock_state_machine import update_state  # noqa: E402
from frontend.components import (                 # noqa: E402
    render_risk_panel,
    render_event_log,
)
from frontend.theme import (                      # noqa: E402
    get_theme,
    inject_theme_css,
    render_theme_toggle,
    STATE_EMOJI,
)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="C-A-B Governance Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme init (must be before any rendering)
# ---------------------------------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

theme = get_theme()
inject_theme_css(theme)


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
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    render_theme_toggle()

    st.divider()
    st.markdown("### Session")
    st.caption(f"Turns: {st.session_state.turn}")
    if st.session_state.events:
        latest = st.session_state.events[-1]
        st.caption(f"State: {STATE_EMOJI.get(latest['risk_state'], '')} {latest['risk_state']}")
        st.caption(f"Score: {latest['risk_score']:.2f}")

    st.divider()
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.history = []
        st.session_state.events = []
        st.session_state.turn = 0
        st.rerun()

    st.divider()
    st.markdown("### About")
    st.caption(
        "C-A-B Governance Pipeline\n\n"
        "Module C: Message Filtering\n"
        "Module A: Mock State Machine\n"
        "Output Scanner: Pre-delivery check"
    )


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------

def main() -> None:
    st.title("🛡️ C-A-B Governance Console")
    st.caption("Module C + Mock Module A — standalone demo")

    col_chat, col_status = st.columns([3, 2])

    # ---- Chat column ----
    with col_chat:
        st.subheader("💬 Livestream Chat Simulator")

        chat_box = st.container(height=520)
        with chat_box:
            for ev in st.session_state.events:
                emoji = STATE_EMOJI.get(ev["risk_state"], "⚪")
                state_color = theme["state_colors"].get(ev["risk_state"], "#666")

                with st.chat_message("user"):
                    st.markdown(
                        f'**Turn {ev["turn_number"]}** '
                        f'<span style="color:{state_color};font-weight:bold;">'
                        f'{emoji} {ev["risk_state"]}</span>',
                        unsafe_allow_html=True,
                    )
                    st.write(ev["user_message"])

                with st.chat_message("assistant"):
                    if ev["action"] == "block":
                        st.markdown(
                            f'<div class="cab-blocked">'
                            f'🚫 <b>BLOCKED</b> — {ev["block_reason"]}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.write(ev["ai_response"])

        user_input = st.chat_input("Type a message to test…")

        if user_input:
            st.session_state.turn += 1
            turn = st.session_state.turn

            t0 = time.time()
            c_result = process_message(user_input, st.session_state.history)
            c_ms = (time.time() - t0) * 1000

            a_result = update_state(c_result)
            a_result["turn_number"] = turn

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
            render_risk_panel(st.session_state.events[-1], theme)
        else:
            st.info("Send a message to start monitoring.")

        st.subheader("📋 Recent Events")
        render_event_log(st.session_state.events, theme)


main()

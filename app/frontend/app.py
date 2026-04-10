"""
Streamlit UI — AI VTuber livestream chat with C-A-B governance pipeline.
Run from `app`: streamlit run frontend/app.py
"""

from __future__ import annotations

import os
import sys

import streamlit as st

# Ensure `app` is importable when Streamlit sets cwd to frontend/
_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

from frontend.components import render_event_log, render_risk_panel
from frontend.theme import get_theme, inject_theme_css
from main import run_pipeline

STREAM_TITLE = "Aria // Code & Rhythm ✨"


def _init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pipeline_events" not in st.session_state:
        st.session_state.pipeline_events = []
    if "risk_score" not in st.session_state:
        st.session_state.risk_score = 0.0
    if "risk_state" not in st.session_state:
        st.session_state.risk_state = "Safe"
    if "turn_number" not in st.session_state:
        st.session_state.turn_number = 0
    if "last_module_c_output" not in st.session_state:
        st.session_state.last_module_c_output = {
            "risk_tags": [],
            "injection_blocked": False,
        }


def _risk_panel_data() -> dict:
    c = st.session_state.last_module_c_output or {}
    tags = c.get("risk_tags") or []
    action = st.session_state.get("last_action", "pass")
    block_reason = ""
    if action == "block":
        block_reason = st.session_state.get("last_policy_reason", "")
    return {
        "risk_state": st.session_state.risk_state,
        "risk_score": st.session_state.risk_score,
        "action": action,
        "turn_number": st.session_state.turn_number,
        "risk_tags": tags,
        "block_reason": block_reason,
        "injection_blocked": bool(c.get("injection_blocked")),
        "module_c_latency_ms": st.session_state.get("last_module_c_latency_ms"),
    }


def main() -> None:
    st.set_page_config(
        page_title="Aria Live",
        page_icon="🐱",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_session()

    theme = get_theme()
    inject_theme_css(theme)

    with st.sidebar:
        st.markdown("### Governance")
        render_risk_panel(_risk_panel_data(), theme)
        st.markdown("---")
        st.markdown("### Pipeline log")
        render_event_log(st.session_state.pipeline_events, theme)

    # Header
    h1, h2 = st.columns([1, 4])
    with h1:
        st.markdown(
            '<span style="background:#ef4444;color:white;padding:6px 12px;'
            'border-radius:6px;font-weight:700;">🔴 LIVE</span>',
            unsafe_allow_html=True,
        )
    with h2:
        st.title(STREAM_TITLE)
        st.caption("C-A-B pipeline · Module C → Module A → GitHub Models · danmaku chat")

    for m in st.session_state.messages:
        role = m["role"]
        content = m["content"]
        if role == "assistant":
            with st.chat_message("assistant", avatar="🐱"):
                st.markdown(content)
        else:
            with st.chat_message("user"):
                st.markdown(content)

    prompt = st.chat_input("danmaku / Chat")
    if prompt:
        with st.spinner("Pipeline & LLM…"):
            result = run_pipeline(prompt, st.session_state)

        c_out = result["module_c_output"]
        st.session_state.last_module_c_output = c_out

        ev = {
            "user_message": prompt,
            "risk_state": result["risk_state"],
            "risk_score": result["risk_score"],
            "action": result["action"],
            "turn_number": result["turn_number"],
            "risk_tags": c_out.get("risk_tags", []),
            "block_reason": st.session_state.get("last_policy_reason", "")
            if result["action"] == "block"
            else "",
        }
        st.session_state.pipeline_events.append(ev)

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append(
            {"role": "assistant", "content": result["ai_response"]},
        )
        st.rerun()


if __name__ == "__main__":
    main()

"""
components.py — Reusable Streamlit components for C-A-B governance UI.

Import and call these from any Streamlit page:

    from frontend.components import render_risk_panel, render_event_log

    render_risk_panel(state_data)
    render_event_log(events)

No page config, no session state, no side effects on import.
"""

from __future__ import annotations

from typing import Dict, List

import streamlit as st


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATE_COLORS = {
    "Safe": "#22c55e",
    "Suspicious": "#eab308",
    "Escalating": "#f97316",
    "Restricted": "#ef4444",
}

STATE_EMOJI = {
    "Safe": "🟢",
    "Suspicious": "🟡",
    "Escalating": "🟠",
    "Restricted": "🔴",
}


# ---------------------------------------------------------------------------
# render_risk_panel
# ---------------------------------------------------------------------------

def render_risk_panel(state_data: Dict) -> None:
    """
    Display current risk status.

    Args:
        state_data: Module A → Frontend dict::

            {
                "risk_state": str,     # Safe / Suspicious / Escalating / Restricted
                "risk_score": float,   # 0.0–1.0
                "action": str,         # pass / scan / block
                "ai_response": str,
                "block_reason": str,
                "risk_tags": list,
                "turn_number": int,
                # optional extras accepted but not required:
                "injection_blocked": bool,
                "module_c_latency_ms": float,
            }
    """
    state = state_data.get("risk_state", "Safe")
    score = state_data.get("risk_score", 0.0)
    color = STATE_COLORS.get(state, "#666")
    emoji = STATE_EMOJI.get(state, "⚪")

    # State pill
    st.markdown(
        f'<div style="background:{color};color:#fff;padding:12px 20px;'
        f'border-radius:8px;font-size:20px;font-weight:bold;text-align:center;'
        f'margin-bottom:12px;">'
        f'{emoji} {state} — Score: {score:.2f}'
        f'</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Action", state_data.get("action", "pass").upper())
    with c2:
        st.metric("Turn", state_data.get("turn_number", 0))

    tags = state_data.get("risk_tags", [])
    if tags:
        st.markdown("**Risk Tags:**")
        for t in tags:
            st.code(t)

    reason = state_data.get("block_reason", "")
    if reason:
        st.warning(f"**Reason:** {reason}")

    if state_data.get("injection_blocked"):
        st.error("⚡ **Injection Fast Path** — blocked before AI call")

    latency = state_data.get("module_c_latency_ms")
    if latency is not None:
        st.caption(f"Module C latency: {latency:.1f} ms")


# ---------------------------------------------------------------------------
# render_event_log
# ---------------------------------------------------------------------------

def render_event_log(events: List[Dict], max_display: int = 10) -> None:
    """
    Scrollable list of recent risk events (newest first).

    Each *event* dict should contain at least:
        turn_number, user_message, risk_state, risk_score,
        action, risk_tags, block_reason
    """
    if not events:
        st.caption("No events yet.")
        return

    for ev in reversed(events[-max_display:]):
        state = ev.get("risk_state", "Safe")
        emoji = STATE_EMOJI.get(state, "⚪")
        msg = ev.get("user_message", "")
        preview = (msg[:50] + "…") if len(msg) > 50 else msg
        turn = ev.get("turn_number", "?")

        with st.expander(f"Turn {turn} {emoji} {state} — {preview}"):
            st.write(f"**Score:** {ev.get('risk_score', 0):.2f}")
            st.write(f"**Action:** {ev.get('action', 'pass')}")
            st.write(f"**Tags:** {', '.join(ev.get('risk_tags', [])) or '—'}")
            if ev.get("block_reason"):
                st.write(f"**Reason:** {ev['block_reason']}")
            st.write(f"**Message:** {msg}")

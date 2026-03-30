"""
components.py — Reusable Streamlit components for C-A-B governance UI.

Supports dark/light theme via the theme system:

    from frontend.components import render_risk_panel, render_event_log
    from frontend.theme import get_theme, inject_theme_css

    theme = get_theme()
    inject_theme_css(theme)
    render_risk_panel(state_data, theme)
    render_event_log(events, theme)

No page config, no session state, no side effects on import.
"""

from __future__ import annotations

import html
from typing import Dict, List, Optional

import streamlit as st

from frontend.theme import LIGHT_THEME, STATE_EMOJI


# ---------------------------------------------------------------------------
# render_risk_panel
# ---------------------------------------------------------------------------

def render_risk_panel(state_data: Dict, theme: Optional[Dict] = None) -> None:
    """
    Display current risk status with theme support.

    Args:
        state_data: Module A → Frontend dict
        theme: Theme dict from get_theme(). Falls back to LIGHT_THEME.
    """
    if theme is None:
        theme = LIGHT_THEME

    state = state_data.get("risk_state", "Safe")
    score = state_data.get("risk_score", 0.0)
    color = theme["state_colors"].get(state, "#666")
    emoji = STATE_EMOJI.get(state, "⚪")

    # State pill — uses theme-aware class
    st.markdown(
        f'<div class="cab-state-pill" style="background:{color};">'
        f'{emoji} {state} — Score: {score:.2f}'
        f'</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Action", state_data.get("action", "pass").upper())
    with c2:
        st.metric("Turn", state_data.get("turn_number", 0))

    # Risk tags — themed
    tags = state_data.get("risk_tags", [])
    if tags:
        st.markdown("**Risk Tags:**")
        tag_html = " ".join(f'<span class="cab-tag">{t}</span>' for t in tags)
        st.markdown(tag_html, unsafe_allow_html=True)

    # Block reason
    reason = state_data.get("block_reason", "")
    if reason:
        st.markdown(
            f'<div class="cab-blocked">{html.escape(reason)}</div>',
            unsafe_allow_html=True,
        )

    # Injection fast path
    if state_data.get("injection_blocked"):
        st.error("⚡ **Injection Fast Path** — blocked before AI call")

    # Latency
    latency = state_data.get("module_c_latency_ms")
    if latency is not None:
        st.markdown(
            f'<span class="cab-latency">Module C latency: {latency:.1f} ms</span>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# render_event_log
# ---------------------------------------------------------------------------

def render_event_log(
    events: List[Dict],
    theme: Optional[Dict] = None,
    max_display: int = 10,
) -> None:
    """
    Scrollable list of recent risk events (newest first).

    Args:
        events: List of event dicts (newest appended last).
        theme: Theme dict from get_theme().
        max_display: Max events to show.
    """
    if theme is None:
        theme = LIGHT_THEME

    if not events:
        st.caption("No events yet.")
        return

    for ev in reversed(events[-max_display:]):
        state = ev.get("risk_state", "Safe")
        emoji = STATE_EMOJI.get(state, "⚪")
        state_color = theme["state_colors"].get(state, "#666")
        msg = ev.get("user_message", "")
        preview = (msg[:50] + "…") if len(msg) > 50 else msg
        turn = ev.get("turn_number", "?")

        with st.expander(f"Turn {turn} {emoji} {state} — {preview}"):
            col_s, col_a = st.columns(2)
            with col_s:
                st.markdown(
                    f'<span style="color:{state_color};font-weight:bold;">'
                    f'Score: {ev.get("risk_score", 0):.2f}</span>',
                    unsafe_allow_html=True,
                )
            with col_a:
                st.write(f"**Action:** {ev.get('action', 'pass')}")

            tags = ev.get("risk_tags", [])
            if tags:
                tag_html = " ".join(f'<span class="cab-tag">{t}</span>' for t in tags)
                st.markdown(tag_html, unsafe_allow_html=True)

            if ev.get("block_reason"):
                st.markdown(
                    f'<div class="cab-blocked">{html.escape(ev["block_reason"])}</div>',
                    unsafe_allow_html=True,
                )

            st.caption(f"Message: {msg}")

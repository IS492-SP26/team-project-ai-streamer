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
        f"{emoji} {state} — Score: {score:.2f}"
        f"</div>",
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

    # Multi-layer breakdown
    layer_details = state_data.get("layer_details")
    if layer_details:
        render_layer_breakdown(layer_details, theme)


# ---------------------------------------------------------------------------
# render_layer_breakdown
# ---------------------------------------------------------------------------

_LAYER_DISPLAY = [
    ("injection_filter", "Injection Filter", "⚡"),
    ("fiction_detector", "Fiction Detector", "📖"),
    ("content_tagger", "Content Tagger", "🏷️"),
    ("semantic_analyzer", "Semantic Analyzer", "🧠"),
    ("llm_guard", "LLM Guard (L2)", "🤖"),
]

_SEVERITY_COLOR = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}


def render_layer_breakdown(layer_details: Dict, theme: Optional[Dict] = None) -> None:
    if theme is None:
        theme = LIGHT_THEME

    st.markdown("**Multi-Layer Interception:**")

    for key, label, icon in _LAYER_DISPLAY:
        layer = layer_details.get(key)
        if not layer:
            continue

        fired = layer.get("fired", False)
        sev = layer.get("severity", "low")

        if key == "llm_guard":
            if not layer.get("enabled", False):
                status_html = (
                    f'<span style="color:{theme["text_secondary"]};">— disabled</span>'
                )
            elif fired:
                verdict = layer.get("verdict", "?")
                status_html = (
                    f'<span style="color:#ef4444;font-weight:bold;">🔴 {verdict}</span>'
                )
            else:
                status_html = f'<span style="color:{theme["text_secondary"]};">— not needed</span>'
        elif fired:
            color = _SEVERITY_COLOR.get(sev, "#666")
            status_html = (
                f'<span style="color:{color};font-weight:bold;">● {sev.upper()}</span>'
            )
        else:
            status_html = f'<span style="color:#22c55e;">✓ clear</span>'

        st.markdown(
            f"{icon} **{label}** {status_html}",
            unsafe_allow_html=True,
        )

        if fired and key == "semantic_analyzer":
            conf = layer.get("confidence", 0)
            signals = layer.get("signals", [])
            if signals:
                sig_html = ", ".join(f"`{s}`" for s in signals)
                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;Confidence: **{conf:.2f}** — Signals: {sig_html}"
                )
            if layer.get("needs_llm_review"):
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;→ *Flagged for LLM review*")

        if fired and key == "injection_filter":
            patterns = layer.get("patterns", [])
            if patterns:
                pat_str = ", ".join(f"`{p}`" for p in patterns[:3])
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;Patterns: {pat_str}")

        if key == "fiction_detector":
            score = layer.get("fiction_score", 0.0)
            reassurance = layer.get("reassurance_count", 0)
            if score > 0 or fired:
                max_score = 5.0  # THRESHOLD_HIGH from fiction_detector
                pct = min(score / max_score, 1.0)
                bar_color = (
                    "#ef4444" if pct >= 1.0 else "#f59e0b" if pct >= 0.5 else "#22c55e"
                )
                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;Fiction Score: **{score:.1f}**/5.0"
                    f" — Reassurances: **{reassurance}**"
                )
                st.markdown(
                    f'&nbsp;&nbsp;&nbsp;&nbsp;<div style="background:#333;border-radius:4px;height:8px;width:200px;display:inline-block;">'
                    f'<div style="background:{bar_color};border-radius:4px;height:8px;width:{pct * 200:.0f}px;"></div>'
                    f"</div>",
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
                    f"Score: {ev.get('risk_score', 0):.2f}</span>",
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

            ld = ev.get("layer_details", {})
            fic = ld.get("fiction_detector", {})
            fic_score = fic.get("fiction_score", 0.0)
            if fic_score > 0:
                pct = min(fic_score / 5.0, 1.0)
                bar_color = (
                    "#ef4444" if pct >= 1.0 else "#f59e0b" if pct >= 0.5 else "#22c55e"
                )
                st.markdown(
                    f"📖 Fiction score: **{fic_score:.1f}**/5.0"
                    f' <div style="background:#333;border-radius:4px;height:6px;width:120px;display:inline-block;">'
                    f'<div style="background:{bar_color};border-radius:4px;height:6px;width:{pct * 120:.0f}px;"></div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.caption(f"Message: {msg}")

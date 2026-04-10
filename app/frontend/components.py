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
    _STATE_CSS_VAR = {
        "Safe": "var(--cab-state-safe)",
        "Suspicious": "var(--cab-state-suspicious)",
        "Escalating": "var(--cab-state-escalating)",
        "Restricted": "var(--cab-state-restricted)",
        "Off": "var(--cab-state-off)",
    }
    color = _STATE_CSS_VAR.get(state, "#666")
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
                    '<span style="color:var(--cab-text-secondary);">— disabled</span>'
                )
            elif fired:
                verdict = layer.get("verdict", "?")
                status_html = (
                    f'<span style="color:#ef4444;font-weight:bold;">🔴 {verdict}</span>'
                )
            else:
                status_html = (
                    '<span style="color:var(--cab-text-secondary);">— not needed</span>'
                )
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
        _EVT_STATE_CSS = {
            "Safe": "var(--cab-state-safe)",
            "Suspicious": "var(--cab-state-suspicious)",
            "Escalating": "var(--cab-state-escalating)",
            "Restricted": "var(--cab-state-restricted)",
            "Off": "var(--cab-state-off)",
        }
        state_color = _EVT_STATE_CSS.get(state, "#666")
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


# ---------------------------------------------------------------------------
# render_pipeline_animation
# ---------------------------------------------------------------------------

_PIPELINE_LAYERS = [
    ("injection_filter", "Injection Filter", "⚡"),
    ("fiction_detector", "Fiction Detector", "📖"),
    ("content_tagger", "Content Tagger", "🏷️"),
    ("semantic_analyzer", "Semantic Analyzer", "🧠"),
    ("llm_guard", "LLM Guard (L2)", "🤖"),
]


def render_pipeline_animation(
    layer_details: Dict, theme: Optional[Dict] = None
) -> None:
    """Render compact pipeline showing all 5 layers with inline details in a single HTML block."""
    if theme is None:
        theme = LIGHT_THEME

    rows_html = []
    for i, (key, label, icon) in enumerate(_PIPELINE_LAYERS):
        layer = layer_details.get(key, {})
        fired = layer.get("fired", False)

        if key == "llm_guard" and not layer.get("enabled", False):
            status = "SKIP"
            color = "var(--cab-text-secondary)"
            symbol = "⏭️"
        elif fired:
            sev = layer.get("severity", "low")
            status = f"CAUGHT ({sev.upper()})"
            color = _SEVERITY_COLOR.get(sev, "#f59e0b")
            symbol = "✗"
        else:
            status = "PASS"
            color = "#22c55e"
            symbol = "✓"

        detail_parts = []
        if fired and key == "injection_filter":
            patterns = layer.get("patterns", [])
            if patterns:
                detail_parts.append("Patterns: " + ", ".join(patterns[:3]))
        if key == "fiction_detector":
            score = layer.get("fiction_score", 0.0)
            if score > 0 or fired:
                pct = min(score / 5.0, 1.0)
                bar_c = (
                    "#ef4444" if pct >= 1.0 else "#f59e0b" if pct >= 0.5 else "#22c55e"
                )
                bar_html = (
                    f'<span style="display:inline-block;background:#333;border-radius:3px;'
                    f'height:6px;width:60px;vertical-align:middle;">'
                    f'<span style="display:block;background:{bar_c};border-radius:3px;'
                    f'height:6px;width:{pct * 60:.0f}px;"></span></span>'
                )
                detail_parts.append(f"Score {score:.1f}/5.0 {bar_html}")
        if fired and key == "content_tagger":
            tags = layer.get("tags", [])
            if tags:
                detail_parts.append(", ".join(tags[:3]))
        if fired and key == "semantic_analyzer":
            signals = layer.get("signals", [])
            conf = layer.get("confidence", 0)
            if signals:
                detail_parts.append(f"Conf {conf:.0%}: " + ", ".join(signals[:3]))
            if layer.get("needs_llm_review"):
                detail_parts.append("→ LLM review")
        if key == "llm_guard" and layer.get("enabled", False):
            verdict = layer.get("verdict")
            reason = layer.get("reason")
            if fired and verdict:
                detail_parts.append(verdict)
            if reason:
                detail_parts.append(reason[:50])

        detail_html = (
            '<span style="color:var(--cab-text-secondary);font-size:11px;margin-left:8px;">'
            f"{' · '.join(detail_parts)}</span>"
            if detail_parts
            else ""
        )

        bg = "var(--cab-bg-card)"
        rows_html.append(
            f'<div style="display:flex;align-items:center;gap:6px;'
            f"padding:4px 10px;margin:2px 0;border-radius:6px;"
            f'background:{bg};border-left:3px solid {color};font-size:13px;">'
            f"<span>{icon}</span>"
            f'<span style="font-weight:600;color:var(--cab-text-primary);min-width:110px;">{label}</span>'
            f'<span style="color:{color};font-weight:700;font-size:12px;min-width:95px;">{symbol} {status}</span>'
            f"{detail_html}"
            f"</div>"
        )

        if i < len(_PIPELINE_LAYERS) - 1:
            arrow_color = (
                color if fired and key != "llm_guard" else "var(--cab-text-secondary)"
            )
            rows_html.append(
                f'<div style="text-align:left;color:{arrow_color};font-size:11px;'
                f'margin:0 0 0 16px;line-height:1;">↓</div>'
            )

    st.markdown("#### Pipeline Flow")
    st.markdown("\n".join(rows_html), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# render_stats_dashboard
# ---------------------------------------------------------------------------


def render_stats_dashboard(stats: Dict, theme: Optional[Dict] = None) -> None:
    """Render attack statistics as a compact single-row metrics bar."""
    if theme is None:
        theme = LIGHT_THEME

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Messages", stats.get("total", 0))
    with c2:
        st.metric("Blocked", stats.get("blocked", 0))
    with c3:
        st.metric("Passed", stats.get("passed", 0))
    with c4:
        rate = stats.get("block_rate", 0.0)
        st.metric("Block Rate", f"{rate:.0f}%")
    with c5:
        avg_lat = stats.get("avg_latency_ms", 0.0)
        st.metric("Latency", f"{avg_lat:.1f}ms")
    with c6:
        harmful = stats.get("harmful_caught", 0)
        st.metric("Threats", harmful)

"""
components.py — Reusable Streamlit components for the C-A-B "Bridge"
governance console.

Public surface (kept stable so risk_panel.py and tests don't break):

    render_risk_panel(state_data, theme)
    render_layer_breakdown(layer_details, theme)
    render_event_log(events, theme, max_display=10)
    render_pipeline_animation(layer_details, theme)
    render_stats_dashboard(stats, theme)

New helpers added by the redesign (theme-aware via CSS vars):

    render_top_bar(mode, stats, *, session_id="")
    render_verdict_ribbon(event)
    render_empty_panel(message, *, dashed=True)
"""

from __future__ import annotations

import html as _html
from typing import Dict, List, Optional

import streamlit as st

from frontend.theme import LIGHT_THEME, STATE_EMOJI


# ---------------------------------------------------------------------------
# Shared mappings
# ---------------------------------------------------------------------------

_STATE_CSS_VAR = {
    "Safe":       "var(--cab-state-safe)",
    "Suspicious": "var(--cab-state-suspicious)",
    "Escalating": "var(--cab-state-escalating)",
    "Restricted": "var(--cab-state-restricted)",
    "Off":        "var(--cab-state-off)",
}
_ACTION_CSS_VAR = {
    "allow":      "var(--cab-state-safe)",
    "scan":       "var(--cab-state-suspicious)",
    "mediate":    "var(--cab-state-escalating)",
    "block":      "var(--cab-state-restricted)",
    "restricted": "var(--cab-state-restricted)",
}

_SEVERITY_COLOR = {
    "high":   "var(--cab-state-restricted)",
    "medium": "var(--cab-state-suspicious)",
    "low":    "var(--cab-state-safe)",
}

_PIPELINE_LAYERS = [
    ("injection_filter",  "Injection filter",  "⚡"),
    ("fiction_detector",  "Fiction detector",  "📖"),
    ("content_tagger",    "Content tagger",    "🏷"),
    ("semantic_analyzer", "Semantic analyzer", "🧠"),
    ("llm_guard",         "LLM guard (L2)",    "🤖"),
]


# ---------------------------------------------------------------------------
# Top status bar — replaces the previous header strip + stats pill + mode
# banner with a single elevated row.
# ---------------------------------------------------------------------------


def render_top_bar(mode: str, stats: Dict, *, session_id: str = "") -> None:
    """Render the bridge's top status bar.

    `mode` is "cab" or "baseline". `stats` is the same dict
    `_render_compact_stats_strip` used to consume.
    """
    if mode == "cab":
        mode_label = "C·A·B PIPELINE"
        mode_sub = "structured · stateful · scanned"
    else:
        mode_label = "BASELINE"
        mode_sub = "raw model · no governance"

    sid = (session_id[:8] + "…") if session_id else ""

    items = [
        ("Messages",   str(stats.get("total", 0)),                 ""),
        ("Blocked",    str(stats.get("blocked", 0)),               "accent"),
        ("Passed",     str(stats.get("passed", 0)),                "ok"),
        ("Block rate", f"{stats.get('block_rate', 0.0):.0f}%",     ""),
        ("Latency",    f"{stats.get('avg_latency_ms', 0.0):.0f}ms",""),
        ("Threats",    str(stats.get("harmful_caught", 0)),        "accent"),
    ]
    stats_html = "".join(
        f'<div class="cab-stat{(" cab-stat--" + cls) if cls else ""}">'
        f'<span class="cab-stat-label">{label}</span>'
        f'<span class="cab-stat-value">{value}</span>'
        f"</div>"
        for label, value, cls in items
    )

    sub_line = (
        f'<span style="opacity:0.55;">session</span> '
        f'<span style="font-family:var(--cab-font-mono);'
        f'color:var(--cab-text-secondary);">{_html.escape(sid)}</span>'
        if sid else ""
    )

    st.markdown(
        '<div class="cab-topbar">'
        '<div class="cab-brand">'
        '<div class="cab-brand-mark"></div>'
        '<div>'
        '<div class="cab-brand-title">C·A·B Governance Console</div>'
        f'<div class="cab-brand-sub">Bridge · live broadcast safety {sub_line}</div>'
        '</div>'
        '</div>'
        '<div class="cab-live"><span class="cab-live-dot"></span>LIVE</div>'
        f'<div class="cab-mode-chip" data-mode="{mode}">'
        f'<span>{mode_label}</span>'
        f'<span class="cab-mode-chip-sub">{mode_sub}</span>'
        '</div>'
        f'<div class="cab-stats">{stats_html}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Verdict ribbon — sits docked above the Aria iframe.
# ---------------------------------------------------------------------------


def render_verdict_ribbon(event: Optional[Dict]) -> None:
    """Compact ribbon with action · state · score · tags. ~58 px tall."""
    if not event:
        st.markdown(
            '<div class="cab-ribbon" data-state="Off">'
            '<span class="cab-ribbon-action" '
            'style="background:var(--cab-state-off);">IDLE</span>'
            '<span class="cab-ribbon-state">Awaiting verdict</span>'
            '<span class="cab-ribbon-score">— Send Aria a message or '
            'fire a sidebar example.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    state = event.get("risk_state", "Safe")
    action = event.get("action", "allow")
    state_color = _STATE_CSS_VAR.get(state, "var(--cab-state-off)")
    action_color = _ACTION_CSS_VAR.get(action, "var(--cab-state-off)")
    tags = event.get("risk_tags") or []

    chips: List[str] = []
    if event.get("injection_blocked"):
        chips.append('<span class="cab-chip cab-chip--injection">INJECTION</span>')
    if event.get("wellbeing_fired"):
        chips.append('<span class="cab-chip cab-chip--wellbeing">WELLBEING</span>')
    chips += [
        f'<span class="cab-chip">{_html.escape(str(t))}</span>'
        for t in tags
    ]

    st.markdown(
        f'<div class="cab-ribbon" data-state="{state}" '
        f'style="border-left-color:{state_color};">'
        f'<span class="cab-ribbon-action" style="background:{action_color};">'
        f'{action.upper()}</span>'
        f'<span class="cab-ribbon-state">{state}</span>'
        f'<span class="cab-ribbon-score">score '
        f'{event.get("risk_score", 0):.2f}</span>'
        f'{"".join(chips)}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Empty-state panel
# ---------------------------------------------------------------------------


def render_empty_panel(message: str, *, dashed: bool = True) -> None:
    cls = "cab-panel-empty" if dashed else "cab-panel"
    st.markdown(
        f'<div class="{cls}">{_html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# render_risk_panel — kept for risk_panel.py / external callers
# ---------------------------------------------------------------------------


def render_risk_panel(state_data: Dict, theme: Optional[Dict] = None) -> None:
    if theme is None:
        theme = LIGHT_THEME

    state = state_data.get("risk_state", "Safe")
    score = state_data.get("risk_score", 0.0)
    color = _STATE_CSS_VAR.get(state, "#666")
    emoji = STATE_EMOJI.get(state, "○")

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

    tags = state_data.get("risk_tags", [])
    if tags:
        st.markdown("**Risk Tags:**")
        tag_html = " ".join(f'<span class="cab-tag">{t}</span>' for t in tags)
        st.markdown(tag_html, unsafe_allow_html=True)

    reason = state_data.get("block_reason", "")
    if reason:
        st.markdown(
            f'<div class="cab-blocked">{_html.escape(reason)}</div>',
            unsafe_allow_html=True,
        )

    if state_data.get("injection_blocked"):
        st.error("⚡ **Injection Fast Path** — blocked before AI call")

    latency = state_data.get("module_c_latency_ms")
    if latency is not None:
        st.markdown(
            f'<span class="cab-latency">Module C latency: {latency:.1f} ms</span>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# render_layer_breakdown — kept for compatibility
# ---------------------------------------------------------------------------

_LAYER_DISPLAY = [
    ("injection_filter",  "Injection Filter",  "⚡"),
    ("fiction_detector",  "Fiction Detector",  "📖"),
    ("content_tagger",    "Content Tagger",    "🏷️"),
    ("semantic_analyzer", "Semantic Analyzer", "🧠"),
    ("llm_guard",         "LLM Guard (L2)",    "🤖"),
]


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
                    f'<span style="color:var(--cab-state-restricted);'
                    f'font-weight:bold;">● {verdict}</span>'
                )
            else:
                status_html = (
                    '<span style="color:var(--cab-text-secondary);">— not needed</span>'
                )
        elif fired:
            color = _SEVERITY_COLOR.get(sev, "var(--cab-text-secondary)")
            status_html = (
                f'<span style="color:{color};font-weight:bold;">● {sev.upper()}</span>'
            )
        else:
            status_html = '<span style="color:var(--cab-state-safe);">✓ clear</span>'

        st.markdown(f"{icon} **{label}** {status_html}", unsafe_allow_html=True)

        if fired and key == "semantic_analyzer":
            conf = layer.get("confidence", 0)
            signals = layer.get("signals", [])
            if signals:
                sig_html = ", ".join(f"`{s}`" for s in signals)
                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;Confidence: **{conf:.2f}** — "
                    f"Signals: {sig_html}"
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
                pct = min(score / 5.0, 1.0)
                bar_color = (
                    "var(--cab-state-restricted)" if pct >= 1.0
                    else "var(--cab-state-suspicious)" if pct >= 0.5
                    else "var(--cab-state-safe)"
                )
                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;Fiction Score: **{score:.1f}**/5.0"
                    f" — Reassurances: **{reassurance}**"
                )
                st.markdown(
                    f'&nbsp;&nbsp;&nbsp;&nbsp;<div style="background:'
                    f'var(--cab-hairline);border-radius:4px;height:8px;'
                    f'width:200px;display:inline-block;">'
                    f'<div style="background:{bar_color};border-radius:4px;'
                    f'height:8px;width:{pct * 200:.0f}px;"></div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ---------------------------------------------------------------------------
# render_event_log — broadcast log, list of cards (no native expanders)
# ---------------------------------------------------------------------------


def render_event_log(
    events: List[Dict],
    theme: Optional[Dict] = None,
    max_display: int = 10,
) -> None:
    if theme is None:
        theme = LIGHT_THEME

    if not events:
        render_empty_panel("No events yet — fire a scenario or example to see "
                           "the governance log fill.")
        return

    rows: List[str] = []
    for ev in reversed(events[-max_display:]):
        state = ev.get("risk_state", "Safe")
        state_color = _STATE_CSS_VAR.get(state, "var(--cab-text-secondary)")
        action = ev.get("action", "allow")
        action_color = _ACTION_CSS_VAR.get(action, "var(--cab-state-off)")
        msg = ev.get("user_message", "")
        if len(msg) > 180:
            msg = msg[:180] + "…"
        turn = ev.get("turn_number", "?")
        score = ev.get("risk_score", 0.0)
        tags = ev.get("risk_tags") or []

        chips_html = "".join(
            f'<span class="cab-chip">{_html.escape(str(t))}</span>'
            for t in tags
        )
        if ev.get("wellbeing_fired"):
            chips_html += '<span class="cab-chip cab-chip--wellbeing">WELLBEING</span>'
        if ev.get("injection_blocked"):
            chips_html += '<span class="cab-chip cab-chip--injection">INJECTION</span>'

        block_html = ""
        reason = ev.get("block_reason") or ""
        if action in ("block", "restricted") and reason:
            block_html = (
                f'<div class="cab-event-block">⛔ {_html.escape(reason[:200])}</div>'
            )

        rows.append(
            f'<div class="cab-event" data-state="{state}">'
            f'<div class="cab-event-turn">T{turn}</div>'
            f'<div class="cab-event-body">'
            f'<div class="cab-event-head">'
            f'<span class="cab-ribbon-action" style="background:{action_color};">'
            f'{action.upper()}</span>'
            f'<span class="cab-event-state" style="color:{state_color};">'
            f'{state}</span>'
            f'<span class="cab-ribbon-score">score {score:.2f}</span>'
            f'{chips_html}'
            f'</div>'
            f'<div class="cab-event-msg">{_html.escape(msg)}</div>'
            f'{block_html}'
            f'</div></div>'
        )

    st.markdown("\n".join(rows), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# render_pipeline_animation — compact card, hairline rows, no arrows
# ---------------------------------------------------------------------------


def render_pipeline_animation(
    layer_details: Dict, theme: Optional[Dict] = None
) -> None:
    if theme is None:
        theme = LIGHT_THEME

    rows: List[str] = []
    for key, label, icon in _PIPELINE_LAYERS:
        layer = layer_details.get(key, {}) or {}
        fired = bool(layer.get("fired", False))

        if key == "llm_guard" and not layer.get("enabled", False):
            status_text  = "SKIP"
            status_class = "skip"
        elif fired:
            sev = layer.get("severity", "low")
            status_text  = sev.upper()
            status_class = {"high": "high", "medium": "med", "low": "low"}.get(sev, "med")
        else:
            status_text  = "PASS"
            status_class = "pass"

        # Detail caption (mono, right-aligned, ellipsised by CSS)
        detail_parts: List[str] = []
        if fired and key == "injection_filter":
            patterns = layer.get("patterns") or []
            if patterns:
                detail_parts.append(", ".join(patterns[:3]))
        if key == "fiction_detector":
            score = float(layer.get("fiction_score", 0.0) or 0.0)
            if score > 0 or fired:
                detail_parts.append(f"score {score:.1f}/5.0")
        if fired and key == "content_tagger":
            tags = layer.get("tags") or []
            if tags:
                detail_parts.append(", ".join(tags[:3]))
        if fired and key == "semantic_analyzer":
            signals = layer.get("signals") or []
            conf = float(layer.get("confidence", 0) or 0)
            if signals:
                detail_parts.append(f"conf {conf:.0%}: " + ", ".join(signals[:2]))
            if layer.get("needs_llm_review"):
                detail_parts.append("→ LLM review")
        if key == "llm_guard" and layer.get("enabled", False):
            verdict = layer.get("verdict")
            reason = layer.get("reason") or ""
            if fired and verdict:
                detail_parts.append(str(verdict))
            if reason:
                detail_parts.append(reason[:60])

        detail_html = (
            f'<span class="cab-pipeline-detail">{_html.escape(" · ".join(detail_parts))}</span>'
            if detail_parts else ""
        )

        rows.append(
            f'<div class="cab-pipeline-row">'
            f'<span class="cab-pipeline-icon">{icon}</span>'
            f'<span class="cab-pipeline-name">{label}</span>'
            f'<span class="cab-pipeline-status cab-pipeline-status--{status_class}">'
            f'{status_text}</span>'
            f'{detail_html}'
            f'</div>'
        )

    st.markdown(
        '<div class="cab-pipeline">' + "".join(rows) + "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# render_stats_dashboard — kept for risk_panel.py
# ---------------------------------------------------------------------------


def render_stats_dashboard(stats: Dict, theme: Optional[Dict] = None) -> None:
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
        st.metric("Block Rate", f"{stats.get('block_rate', 0.0):.0f}%")
    with c5:
        st.metric("Latency", f"{stats.get('avg_latency_ms', 0.0):.1f}ms")
    with c6:
        st.metric("Threats", stats.get("harmful_caught", 0))

"""Streamlit live red-team demo page (CP4 demo replacement).

Run from repo root:
    streamlit run app/frontend/red_team_demo.py

Layout:
- Top banner: prominent BASELINE / CAB mode toggle (the whole point of the demo).
- Main: simulated livestream chat — adversarial messages from `red_team.runner`
  appear at human typing pace, with Aria's response shown alongside.
- Right sidebar: governance panel showing risk_state / risk_score / action
  / module_c_tags / wellbeing_detector flag.
- Auto-advance via streamlit-autorefresh; manual "next turn" also works.

This file is independent of `app.py` — it does not modify the main chat
demo, and it pulls scenarios + pipeline directly from the repo.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

_APP_ROOT = Path(__file__).resolve().parents[1]
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from red_team.runner import (  # noqa: E402
    DEFAULT_MIN_PACE,
    TurnEvent,
    iter_scenario,
    list_scenario_paths,
    load_scenario,
)

try:
    from streamlit_autorefresh import st_autorefresh  # type: ignore
except ImportError:  # pragma: no cover
    st_autorefresh = None  # type: ignore


PAGE_TITLE = "C-A-B · Live Red-Team Demo"
DEFAULT_PACE_SECONDS = 6


# ---------------------------------------------------------------------------
# session_state initialization
# ---------------------------------------------------------------------------


def _init_state() -> None:
    if "rt_mode" not in st.session_state:
        st.session_state.rt_mode = "cab"
    if "rt_scenario_path" not in st.session_state:
        paths = list_scenario_paths()
        st.session_state.rt_scenario_path = str(paths[0]) if paths else ""
    if "rt_events" not in st.session_state:
        # List[Dict] — serialized TurnEvent dicts for rendering
        st.session_state.rt_events = []
    if "rt_iterator" not in st.session_state:
        st.session_state.rt_iterator = None
    if "rt_playing" not in st.session_state:
        st.session_state.rt_playing = False
    if "rt_pace" not in st.session_state:
        st.session_state.rt_pace = DEFAULT_PACE_SECONDS
    if "rt_session_label" not in st.session_state:
        st.session_state.rt_session_label = ""
    if "rt_scenario_done" not in st.session_state:
        st.session_state.rt_scenario_done = False


def _reset_run() -> None:
    st.session_state.rt_events = []
    st.session_state.rt_iterator = None
    st.session_state.rt_playing = False
    st.session_state.rt_session_label = ""
    st.session_state.rt_scenario_done = False


def _start_run() -> None:
    """Build a fresh iterator for the selected scenario+mode and arm play."""
    _reset_run()
    path = Path(st.session_state.rt_scenario_path)
    if not path.exists():
        st.error(f"Scenario not found: {path}")
        return
    # do_sleep=False: UI controls pacing via st_autorefresh.
    iterator = iter_scenario(
        path,
        mode=st.session_state.rt_mode,
        pace_min=DEFAULT_MIN_PACE,
        pace_max=DEFAULT_MIN_PACE,  # deterministic when UI controls timing
        seed=0,
        do_sleep=False,
    )
    st.session_state.rt_iterator = iterator
    st.session_state.rt_playing = True
    scenario = load_scenario(path)
    st.session_state.rt_session_label = (
        f"{scenario['scenario_id']} · {st.session_state.rt_mode.upper()}"
    )


def _advance_one() -> None:
    iterator = st.session_state.rt_iterator
    if iterator is None:
        return
    try:
        event: TurnEvent = next(iterator)
    except StopIteration:
        st.session_state.rt_playing = False
        st.session_state.rt_scenario_done = True
        st.session_state.rt_iterator = None
        return
    st.session_state.rt_events.append(_event_to_dict(event))


def _event_to_dict(event: TurnEvent) -> Dict[str, Any]:
    trace = event.trace
    wellbeing = trace.get("wellbeing_detector") or {}
    return {
        "turn_number": event.turn_number,
        "user_id": event.user_id,
        "user_message": event.user_message,
        "is_attack_turn": event.is_attack_turn,
        "expected_behavior": event.expected_behavior,
        "expected_tags": event.expected_tags,
        "mode": event.mode,
        "action": trace.get("action", "allow"),
        "risk_state": trace.get("risk_state", "Safe"),
        "risk_score": float(trace.get("risk_score", 0.0)),
        "module_c_tags": trace.get("module_c_tags") or [],
        "injection_blocked": bool(trace.get("injection_blocked", False)),
        "block_reason": trace.get("block_reason", ""),
        "ai_response_final": trace.get("ai_response_final", ""),
        "wellbeing_fired": bool(wellbeing.get("fired", False)),
    }


# ---------------------------------------------------------------------------
# rendering helpers
# ---------------------------------------------------------------------------


_ACTION_COLORS = {
    "allow": "#10b981",  # green
    "scan": "#0ea5e9",   # blue
    "mediate": "#eab308",  # yellow
    "block": "#ef4444",   # red
    "restricted": "#ef4444",
}
_STATE_COLORS = {
    "Safe": "#10b981",
    "Suspicious": "#0ea5e9",
    "Escalating": "#eab308",
    "Restricted": "#ef4444",
}


def _badge(text: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:white;padding:3px 10px;'
        f'border-radius:6px;font-weight:700;font-size:0.85rem;">{text}</span>'
    )


def _mode_banner() -> None:
    mode = st.session_state.rt_mode
    if mode == "cab":
        bg = "#0f766e"
        title = "🛡️  C-A-B PIPELINE — ON"
        sub = "Module C tagging · Module A risk FSM · pre-generation policy · output scan"
    else:
        bg = "#7f1d1d"
        title = "⚠️  BASELINE — NO GOVERNANCE"
        sub = "raw deterministic mock · no instruction isolation · no risk tracking"
    st.markdown(
        f'<div style="background:{bg};color:white;padding:14px 22px;'
        f'border-radius:10px;margin-bottom:14px;">'
        f'<div style="font-size:1.4rem;font-weight:800;">{title}</div>'
        f'<div style="font-size:0.95rem;opacity:0.9;margin-top:4px;">{sub}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def _render_chat(events: List[Dict[str, Any]]) -> None:
    if not events:
        st.markdown(
            '<div style="opacity:0.55;font-style:italic;padding:20px 0;">'
            "Press ▶ Play to start the simulated livestream chat."
            "</div>",
            unsafe_allow_html=True,
        )
        return
    for ev in events:
        attack_marker = "🎯" if ev["is_attack_turn"] else "💬"
        action_color = _ACTION_COLORS.get(ev["action"], "#6b7280")
        # Viewer message
        with st.chat_message("user", avatar=attack_marker):
            st.markdown(
                f"**{ev['user_id']}** &nbsp; T{ev['turn_number']}",
                unsafe_allow_html=True,
            )
            st.markdown(f"{ev['user_message']}")
            badges_html = (
                _badge(ev["action"].upper(), action_color)
                + " &nbsp; "
                + _badge(ev["risk_state"], _STATE_COLORS.get(ev["risk_state"], "#6b7280"))
                + f" &nbsp; <span style='opacity:0.7;'>score {ev['risk_score']:.2f}</span>"
            )
            if ev["module_c_tags"]:
                tags_str = ", ".join(ev["module_c_tags"])
                badges_html += f" &nbsp; <code style='font-size:0.8rem;'>{tags_str}</code>"
            if ev["wellbeing_fired"]:
                badges_html += " &nbsp; " + _badge("WELLBEING", "#a855f7")
            st.markdown(badges_html, unsafe_allow_html=True)
        # AI response
        with st.chat_message("assistant", avatar="🐱"):
            st.markdown(ev["ai_response_final"] or "_(no response)_")
            if ev["block_reason"]:
                st.caption(f"🛡️ {ev['block_reason'][:160]}")


def _render_panel(events: List[Dict[str, Any]]) -> None:
    st.markdown("### Governance panel")
    if not events:
        st.markdown("_no turns yet_")
        return
    last = events[-1]
    st.markdown(
        f"**Turn:** {last['turn_number']}  ·  **Mode:** `{last['mode']}`",
        unsafe_allow_html=True,
    )
    st.markdown(
        _badge(last["action"].upper(), _ACTION_COLORS.get(last["action"], "#6b7280"))
        + " &nbsp; "
        + _badge(last["risk_state"], _STATE_COLORS.get(last["risk_state"], "#6b7280")),
        unsafe_allow_html=True,
    )
    st.metric("risk_score", f"{last['risk_score']:.2f}")
    st.markdown(
        f"**Tags:** `{', '.join(last['module_c_tags']) or '—'}`",
        unsafe_allow_html=True,
    )
    if last["injection_blocked"]:
        st.markdown(_badge("INJECTION_BLOCKED", "#ef4444"), unsafe_allow_html=True)
    if last["wellbeing_fired"]:
        st.markdown(_badge("WELLBEING_FIRED", "#a855f7"), unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Run summary")
    counts = {"allow": 0, "scan": 0, "mediate": 0, "block": 0, "restricted": 0}
    for ev in events:
        counts[ev["action"]] = counts.get(ev["action"], 0) + 1
    st.markdown(
        " · ".join(f"**{k}**: {v}" for k, v in counts.items() if v),
        unsafe_allow_html=True,
    )
    st.caption(
        f"{len(events)} turn(s) processed in this run. Session: "
        f"`{st.session_state.rt_session_label or '(none)'}`"
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_state()

    st.title(PAGE_TITLE)
    st.caption(
        "Adversarial scenarios from `app/eval/scenarios/` are replayed at "
        "human typing pace. Toggle the mode below to see the C-A-B pipeline "
        "engage versus a no-governance baseline."
    )

    # ---------- top controls ----------
    paths = list_scenario_paths()
    path_labels = {str(p): p.stem for p in paths}
    if not paths:
        st.error("No CP4 scenarios found in app/eval/scenarios/.")
        return

    cols = st.columns([1.4, 1, 1, 0.8, 0.8, 0.8])
    with cols[0]:
        chosen_path = st.selectbox(
            "Scenario",
            options=list(path_labels.keys()),
            format_func=lambda p: path_labels[p],
            index=list(path_labels.keys()).index(st.session_state.rt_scenario_path)
            if st.session_state.rt_scenario_path in path_labels
            else 0,
            key="rt_scenario_select",
        )
        if chosen_path != st.session_state.rt_scenario_path:
            st.session_state.rt_scenario_path = chosen_path
            _reset_run()
    with cols[1]:
        new_mode = st.radio(
            "Pipeline mode",
            options=["cab", "baseline"],
            index=0 if st.session_state.rt_mode == "cab" else 1,
            horizontal=True,
            key="rt_mode_radio",
        )
        if new_mode != st.session_state.rt_mode:
            st.session_state.rt_mode = new_mode
            _reset_run()
    with cols[2]:
        st.session_state.rt_pace = st.slider(
            "Pace (sec/turn)",
            min_value=2,
            max_value=15,
            value=int(st.session_state.rt_pace),
        )
    with cols[3]:
        if st.button("▶ Play", use_container_width=True, type="primary"):
            _start_run()
    with cols[4]:
        if st.button("⏸ Pause", use_container_width=True, disabled=not st.session_state.rt_playing):
            st.session_state.rt_playing = False
    with cols[5]:
        if st.button("⏭ Step", use_container_width=True):
            if st.session_state.rt_iterator is None and not st.session_state.rt_scenario_done:
                _start_run()
                st.session_state.rt_playing = False
            _advance_one()

    # ---------- mode banner ----------
    _mode_banner()

    # ---------- auto-advance tick ----------
    if st.session_state.rt_playing and st_autorefresh is not None:
        st_autorefresh(
            interval=int(st.session_state.rt_pace * 1000),
            key="rt_autorefresh",
        )
        _advance_one()
        if st.session_state.rt_scenario_done:
            # final autorefresh tick consumed the StopIteration
            pass
    elif st.session_state.rt_playing and st_autorefresh is None:
        st.warning(
            "streamlit-autorefresh is not installed — auto-advance disabled. "
            "Run: `pip install streamlit-autorefresh`. Use ⏭ Step for manual."
        )

    # ---------- main layout: chat (left) + panel (right) ----------
    chat_col, panel_col = st.columns([2.2, 1])
    with chat_col:
        _render_chat(st.session_state.rt_events)
    with panel_col:
        _render_panel(st.session_state.rt_events)

    if st.session_state.rt_scenario_done:
        st.success(
            f"Scenario complete — {len(st.session_state.rt_events)} turns. "
            "Toggle Pipeline mode and press ▶ Play to compare."
        )


if __name__ == "__main__":
    main()

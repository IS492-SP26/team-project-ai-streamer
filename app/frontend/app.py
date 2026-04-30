"""Streamlit UI — AI VTuber livestream chat with C-A-B governance pipeline.

Single integrated demo surface. Run from `app`:
    streamlit run frontend/app.py
or from repo root:
    streamlit run app/frontend/app.py

Features (all in one page):
- Manual chat input (existing CP3 demo behavior).
- Auto-played adversarial scenarios from `app/eval/scenarios/` driven by
  `app.red_team.runner`; ▶ Play / ⏸ Pause / ⏭ Step controls in sidebar.
- Persistent BASELINE / CAB pipeline-mode toggle visible at the top of the
  page; flipping it forces a session reset so audience sees clean contrast.
- Governance panel showing the most recent risk_state, score, action, tags,
  injection_blocked, and wellbeing_fired badges.
- Pipeline log of all events (manual + auto-played) for the current session.

The OBS demo captures this entire page full-screen — no separate red-team
demo file. Open-LLM-VTuber (optional, via cab_openai_proxy) sits beside it
for the avatar.
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

# Ensure `app/` is importable when Streamlit sets cwd to frontend/
_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

from frontend.theme import get_theme, inject_theme_css  # noqa: E402
from main import run_pipeline  # noqa: E402
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


STREAM_TITLE = "Aria // Code & Rhythm ✨"
DEFAULT_PACE_SECONDS = 6


# ---------------------------------------------------------------------------
# session state
# ---------------------------------------------------------------------------


def _init_session() -> None:
    """Initialize all session_state keys used by the integrated demo.

    Distinct keys:
    - identity: session_id, user_id (CP4 telemetry, issue #15).
    - chat: messages (list of {role, content, action, risk_state, ...}).
    - pipeline state: risk_score, risk_state, turn_number, last_action,
      last_policy_reason, last_module_c_output, last_module_c_latency_ms.
    - mode: pipeline_mode in {"cab", "baseline"} — flipped by the top toggle.
    - red-team: rt_iterator, rt_playing, rt_scenario_path, rt_pace,
      rt_scenario_done, rt_session_label.
    - log: pipeline_events (list of compact event dicts for sidebar log).
    """
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
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
    if "pipeline_mode" not in st.session_state:
        st.session_state.pipeline_mode = "cab"
    if "last_module_c_output" not in st.session_state:
        st.session_state.last_module_c_output = {
            "risk_tags": [],
            "injection_blocked": False,
        }
    # Red-team state
    if "rt_iterator" not in st.session_state:
        st.session_state.rt_iterator = None
    if "rt_playing" not in st.session_state:
        st.session_state.rt_playing = False
    if "rt_scenario_path" not in st.session_state:
        paths = list_scenario_paths()
        st.session_state.rt_scenario_path = str(paths[0]) if paths else ""
    if "rt_pace" not in st.session_state:
        st.session_state.rt_pace = DEFAULT_PACE_SECONDS
    if "rt_scenario_done" not in st.session_state:
        st.session_state.rt_scenario_done = False
    if "rt_session_label" not in st.session_state:
        st.session_state.rt_session_label = ""
    if "rt_last_event_meta" not in st.session_state:
        st.session_state.rt_last_event_meta = {}


def _reset_chat_state() -> None:
    """Forget all messages / risk state / red-team progress.

    Triggered when the user flips the pipeline mode (so the audience sees
    a clean contrast on the same scenario) or hits the "reset" button.
    """
    st.session_state.messages = []
    st.session_state.pipeline_events = []
    st.session_state.risk_score = 0.0
    st.session_state.risk_state = "Safe"
    st.session_state.turn_number = 0
    st.session_state.last_module_c_output = {
        "risk_tags": [],
        "injection_blocked": False,
    }
    st.session_state.rt_iterator = None
    st.session_state.rt_playing = False
    st.session_state.rt_scenario_done = False
    st.session_state.rt_session_label = ""
    st.session_state.rt_last_event_meta = {}
    # Issue a fresh session_id so telemetry rows from the new run don't
    # collide with the old one.
    st.session_state.session_id = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# rendering helpers
# ---------------------------------------------------------------------------


_ACTION_COLORS = {
    "allow": "#10b981",
    "scan": "#0ea5e9",
    "mediate": "#eab308",
    "block": "#ef4444",
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
    """Big colored banner across the top of the page so OBS captures the
    current pipeline mode unambiguously. Teal=on, dark red=off."""
    if st.session_state.pipeline_mode == "cab":
        bg = "#0f766e"
        title = "🛡️  C-A-B PIPELINE — ON"
        sub = (
            "Module C parallel detectors · wellbeing pre-filter · "
            "Module A risk FSM · CP4 policy override · output scanner"
        )
    else:
        bg = "#7f1d1d"
        title = "⚠️  BASELINE — NO GOVERNANCE"
        sub = (
            "raw model · no instruction isolation · no risk tracking · "
            "no output scan"
        )
    st.markdown(
        f'<div style="background:{bg};color:white;padding:14px 22px;'
        f'border-radius:10px;margin-bottom:14px;">'
        f'<div style="font-size:1.5rem;font-weight:800;">{title}</div>'
        f'<div style="font-size:0.95rem;opacity:0.9;margin-top:4px;">{sub}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def _render_chat_message(message: Dict[str, Any]) -> None:
    role = message.get("role", "user")
    content = message.get("content", "")
    if role == "assistant":
        with st.chat_message("assistant", avatar="🐱"):
            st.markdown(content)
            block_reason = message.get("block_reason")
            if block_reason:
                st.caption(f"🛡️ {block_reason[:180]}")
        return

    avatar = "🎯" if message.get("is_attack_turn") else "💬"
    with st.chat_message("user", avatar=avatar):
        sender = message.get("user_id") or "viewer"
        st.markdown(f"**{sender}**")
        st.markdown(content)
        action = message.get("action")
        risk_state = message.get("risk_state")
        if action:
            badges = _badge(
                action.upper(), _ACTION_COLORS.get(action, "#6b7280")
            )
            if risk_state:
                badges += " &nbsp; " + _badge(
                    risk_state, _STATE_COLORS.get(risk_state, "#6b7280")
                )
            score = message.get("risk_score")
            if score is not None:
                badges += (
                    f" &nbsp; <span style='opacity:0.7;'>score "
                    f"{float(score):.2f}</span>"
                )
            tags = message.get("module_c_tags") or []
            if tags:
                tags_str = ", ".join(tags)
                badges += (
                    f" &nbsp; <code style='font-size:0.8rem;'>{tags_str}</code>"
                )
            if message.get("wellbeing_fired"):
                badges += " &nbsp; " + _badge("WELLBEING", "#a855f7")
            st.markdown(badges, unsafe_allow_html=True)


def _render_governance_panel() -> None:
    st.markdown("### Governance")
    score = float(st.session_state.risk_score)
    state = str(st.session_state.risk_state)
    action = str(st.session_state.get("last_action", "allow") or "allow")
    last_c = st.session_state.last_module_c_output or {}
    tags = list(last_c.get("risk_tags") or [])

    badges = (
        _badge(action.upper(), _ACTION_COLORS.get(action, "#6b7280"))
        + " &nbsp; "
        + _badge(state, _STATE_COLORS.get(state, "#6b7280"))
    )
    st.markdown(badges, unsafe_allow_html=True)
    st.metric("risk_score", f"{score:.2f}")
    st.markdown(
        f"**Tags:** `{', '.join(tags) or '—'}`",
        unsafe_allow_html=True,
    )
    if last_c.get("injection_blocked"):
        st.markdown(_badge("INJECTION_BLOCKED", "#ef4444"), unsafe_allow_html=True)
    if st.session_state.rt_last_event_meta.get("wellbeing_fired"):
        st.markdown(_badge("WELLBEING_FIRED", "#a855f7"), unsafe_allow_html=True)
    policy_reason = st.session_state.get("last_policy_reason")
    if policy_reason and action != "allow":
        st.caption(policy_reason[:180])


def _render_event_log() -> None:
    events = st.session_state.pipeline_events
    st.markdown("### Pipeline log")
    if not events:
        st.markdown("_no events yet_")
        return
    # Show most recent 10 inline; rest collapsed in expander.
    recent = events[-10:]
    for ev in reversed(recent):
        action = ev.get("action", "")
        state = ev.get("risk_state", "")
        msg_preview = (ev.get("user_message") or "")[:70]
        st.markdown(
            (
                f"`T{ev.get('turn_number','?'):>2}` "
                + _badge(action.upper(), _ACTION_COLORS.get(action, "#6b7280"))
                + " &nbsp; "
                + _badge(state, _STATE_COLORS.get(state, "#6b7280"))
                + f" &nbsp; <span style='opacity:0.75;'>{msg_preview}</span>"
            ),
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# turn handling — manual + auto
# ---------------------------------------------------------------------------


def _record_turn_into_history(
    user_message: str,
    user_id: str,
    is_attack: bool,
    result: Dict[str, Any],
) -> None:
    """Append a user turn + assistant turn to messages and pipeline_events.

    `result` is the dict returned by main.run_pipeline. The user-side message
    carries the action / risk badges so the rendering can show them inline.
    """
    user_record: Dict[str, Any] = {
        "role": "user",
        "content": user_message,
        "user_id": user_id,
        "is_attack_turn": bool(is_attack),
        "action": result.get("action"),
        "risk_state": result.get("risk_state"),
        "risk_score": result.get("risk_score"),
        "module_c_tags": result.get("module_c_tags") or [],
        "wellbeing_fired": bool(result.get("wellbeing_fired", False)),
    }
    assistant_record: Dict[str, Any] = {
        "role": "assistant",
        "content": result.get("ai_response_final", ""),
        "block_reason": result.get("block_reason", ""),
    }
    st.session_state.messages.append(user_record)
    st.session_state.messages.append(assistant_record)

    st.session_state.last_module_c_output = result.get("module_c_output", {}) or {}
    st.session_state.rt_last_event_meta = {
        "wellbeing_fired": bool(result.get("wellbeing_fired", False)),
    }

    st.session_state.pipeline_events.append(
        {
            "turn_number": result.get("turn_number"),
            "user_message": user_message,
            "user_id": user_id,
            "action": result.get("action"),
            "risk_state": result.get("risk_state"),
            "risk_score": result.get("risk_score"),
            "module_c_tags": result.get("module_c_tags") or [],
            "is_attack_turn": is_attack,
            "wellbeing_fired": bool(result.get("wellbeing_fired", False)),
            "block_reason": result.get("block_reason", ""),
        }
    )


def _handle_manual_message(prompt: str) -> None:
    with st.spinner("Pipeline & LLM…"):
        result = run_pipeline(prompt, st.session_state)
    _record_turn_into_history(
        user_message=prompt,
        user_id=str(st.session_state.user_id)[:8],
        is_attack=False,
        result=result,
    )


def _start_red_team_run() -> None:
    """Build a fresh iterator for the chosen scenario+mode and arm play."""
    path_str = st.session_state.rt_scenario_path
    if not path_str:
        st.error("No scenario selected.")
        return
    path = Path(path_str)
    if not path.exists():
        st.error(f"Scenario not found: {path}")
        return
    # Reset chat so the re-run starts from a clean Safe state at score 0.
    _reset_chat_state()
    # do_sleep=False so the UI controls pacing via st_autorefresh.
    iterator = iter_scenario(
        path,
        mode=st.session_state.pipeline_mode,
        pace_min=DEFAULT_MIN_PACE,
        pace_max=DEFAULT_MIN_PACE,
        seed=0,
        do_sleep=False,
    )
    st.session_state.rt_iterator = iterator
    st.session_state.rt_playing = True
    st.session_state.rt_scenario_done = False
    scenario = load_scenario(path)
    st.session_state.rt_session_label = (
        f"{scenario['scenario_id']} · "
        f"{st.session_state.pipeline_mode.upper()}"
    )


def _advance_red_team_one() -> None:
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

    trace = event.trace
    # Keep session-level risk in sync with the iterator's view of it so
    # the governance panel reflects the current scenario state.
    st.session_state.risk_score = float(trace.get("risk_score", 0.0))
    st.session_state.risk_state = str(trace.get("risk_state", "Safe"))
    st.session_state.turn_number = int(trace.get("turn_number", 0))
    st.session_state.last_action = str(trace.get("action", "allow"))
    st.session_state.last_policy_reason = str(trace.get("policy_reason", ""))

    # Build a result-shaped dict the chat rendering can consume.
    result = {
        "ai_response_final": trace.get("ai_response_final", ""),
        "action": trace.get("action"),
        "risk_state": trace.get("risk_state"),
        "risk_score": trace.get("risk_score"),
        "module_c_tags": trace.get("module_c_tags") or [],
        "module_c_output": trace.get("module_c_output", {}),
        "block_reason": trace.get("block_reason", ""),
        "turn_number": trace.get("turn_number"),
        "wellbeing_fired": (
            (trace.get("wellbeing_detector") or {}).get("fired", False)
        ),
    }
    _record_turn_into_history(
        user_message=event.user_message,
        user_id=event.user_id,
        is_attack=event.is_attack_turn,
        result=result,
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="Aria Live · C-A-B",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_session()

    theme = get_theme()
    inject_theme_css(theme)

    # ------------------- sidebar -------------------
    with st.sidebar:
        st.markdown("### Pipeline mode")
        new_mode = st.radio(
            "",
            options=["cab", "baseline"],
            index=0 if st.session_state.pipeline_mode == "cab" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="sidebar_pipeline_mode_radio",
        )
        if new_mode != st.session_state.pipeline_mode:
            st.session_state.pipeline_mode = new_mode
            _reset_chat_state()

        st.markdown("---")
        _render_governance_panel()

        st.markdown("---")
        st.markdown("### Red-team auto-play")
        paths = list_scenario_paths()
        if not paths:
            st.warning("No CP4 scenarios found.")
        else:
            path_labels = {str(p): p.stem for p in paths}
            current = (
                st.session_state.rt_scenario_path
                if st.session_state.rt_scenario_path in path_labels
                else list(path_labels.keys())[0]
            )
            chosen = st.selectbox(
                "Scenario",
                options=list(path_labels.keys()),
                format_func=lambda p: path_labels[p],
                index=list(path_labels.keys()).index(current),
                key="sidebar_scenario_select",
            )
            if chosen != st.session_state.rt_scenario_path:
                st.session_state.rt_scenario_path = chosen
                # Don't auto-reset; user might just be browsing.
            st.session_state.rt_pace = st.slider(
                "Pace (sec/turn)",
                min_value=2,
                max_value=15,
                value=int(st.session_state.rt_pace),
                key="sidebar_pace_slider",
            )
            cols = st.columns(3)
            with cols[0]:
                if st.button(
                    "▶ Play",
                    type="primary",
                    use_container_width=True,
                    key="sidebar_play",
                ):
                    _start_red_team_run()
            with cols[1]:
                if st.button(
                    "⏸ Pause",
                    use_container_width=True,
                    disabled=not st.session_state.rt_playing,
                    key="sidebar_pause",
                ):
                    st.session_state.rt_playing = False
            with cols[2]:
                if st.button(
                    "⏭ Step",
                    use_container_width=True,
                    key="sidebar_step",
                ):
                    if (
                        st.session_state.rt_iterator is None
                        and not st.session_state.rt_scenario_done
                    ):
                        _start_red_team_run()
                        st.session_state.rt_playing = False
                    _advance_red_team_one()
            if st.session_state.rt_session_label:
                st.caption(f"Run: `{st.session_state.rt_session_label}`")

        st.markdown("---")
        if st.button(
            "🔄 Reset session",
            use_container_width=True,
            key="sidebar_reset",
        ):
            _reset_chat_state()

        st.markdown("---")
        _render_event_log()

        st.markdown("---")
        st.caption(
            f"session `{st.session_state.session_id[:8]}` · "
            f"user `{st.session_state.user_id[:8]}`"
        )

    # ------------------- main panel -------------------
    h1, h2 = st.columns([1, 4])
    with h1:
        st.markdown(
            '<span style="background:#ef4444;color:white;padding:6px 12px;'
            'border-radius:6px;font-weight:700;">🔴 LIVE</span>',
            unsafe_allow_html=True,
        )
    with h2:
        st.title(STREAM_TITLE)
        st.caption(
            "Manual chat is on the bottom; red-team scenarios auto-play "
            "from the sidebar. Toggle Pipeline mode (sidebar top) to "
            "see C-A-B engage versus a no-governance baseline."
        )

    _mode_banner()

    # Chat history (manual + auto-played turns interleaved chronologically)
    for m in st.session_state.messages:
        _render_chat_message(m)

    # Auto-advance tick. Only fires when ▶ Play is active.
    if st.session_state.rt_playing and st_autorefresh is not None:
        st_autorefresh(
            interval=int(st.session_state.rt_pace * 1000),
            key="rt_autorefresh_main",
        )
        _advance_red_team_one()
    elif st.session_state.rt_playing and st_autorefresh is None:
        st.warning(
            "streamlit-autorefresh not installed — auto-advance disabled. "
            "Use ⏭ Step in the sidebar for manual stepping."
        )

    if st.session_state.rt_scenario_done:
        st.success(
            f"Scenario complete — {st.session_state.turn_number} turns "
            "processed. Flip Pipeline mode or pick another scenario, then "
            "press ▶ Play to compare."
        )

    # Manual chat input — works in both modes; the routing inside
    # main.run_pipeline picks the right branch based on pipeline_mode.
    prompt = st.chat_input("danmaku / Chat (or use ▶ Play in the sidebar)")
    if prompt:
        _handle_manual_message(prompt)
        st.rerun()


if __name__ == "__main__":
    main()

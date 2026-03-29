"""
theme.py — Dark/Light theme system for C-A-B governance UI.

Usage:
    from frontend.theme import get_theme, inject_theme_css

    theme = get_theme()              # reads st.session_state.dark_mode
    inject_theme_css(theme)          # injects CSS into the page
    theme["state_colors"]["Safe"]    # use in components
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import streamlit as st


# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------

LIGHT_THEME: Dict = {
    "name": "light",
    "bg_primary": "#ffffff",
    "bg_secondary": "#f8f9fa",
    "bg_card": "#ffffff",
    "text_primary": "#1a1a2e",
    "text_secondary": "#6c757d",
    "border": "#e0e0e0",
    "state_colors": {
        "Safe": "#22c55e",
        "Suspicious": "#eab308",
        "Escalating": "#f97316",
        "Restricted": "#ef4444",
    },
    "state_text": "#ffffff",
    "tag_bg": "#f0f0f0",
    "tag_text": "#333333",
    "chat_user_bg": "#e8f4fd",
    "chat_bot_bg": "#f0f0f0",
    "blocked_bg": "#fef2f2",
    "blocked_border": "#ef4444",
    "expander_bg": "#f8f9fa",
}

DARK_THEME: Dict = {
    "name": "dark",
    "bg_primary": "#0e1117",
    "bg_secondary": "#1a1d23",
    "bg_card": "#1e2128",
    "text_primary": "#e6e6e6",
    "text_secondary": "#8b949e",
    "border": "#30363d",
    "state_colors": {
        "Safe": "#2ea043",
        "Suspicious": "#d29922",
        "Escalating": "#e3743b",
        "Restricted": "#f85149",
    },
    "state_text": "#ffffff",
    "tag_bg": "#21262d",
    "tag_text": "#c9d1d9",
    "chat_user_bg": "#161b22",
    "chat_bot_bg": "#1a1d23",
    "blocked_bg": "#2d1215",
    "blocked_border": "#f85149",
    "expander_bg": "#161b22",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

STATE_EMOJI = {
    "Safe": "🟢",
    "Suspicious": "🟡",
    "Escalating": "🟠",
    "Restricted": "🔴",
}


def get_theme() -> Dict:
    """Return current theme based on session state."""
    if st.session_state.get("dark_mode", True):
        return DARK_THEME
    return LIGHT_THEME


def inject_theme_css(theme: Dict) -> None:
    """Inject CSS custom properties and overrides for the active theme."""
    t = theme
    css = f"""
    <style>
    /* ---- Streamlit root overrides ---- */
    .stApp {{
        background-color: {t["bg_primary"]};
        color: {t["text_primary"]};
    }}
    [data-testid="stSidebar"] {{
        background-color: {t["bg_secondary"]};
    }}
    [data-testid="stHeader"] {{
        background-color: {t["bg_primary"]};
    }}
    /* Chat message containers */
    [data-testid="stChatMessage"] {{
        background-color: {t["bg_card"]};
        border: 1px solid {t["border"]};
    }}
    /* Metric labels */
    [data-testid="stMetricValue"] {{
        color: {t["text_primary"]};
    }}
    /* Expanders */
    [data-testid="stExpander"] {{
        background-color: {t["bg_card"]};
        border-color: {t["border"]};
    }}
    /* ---- C-A-B theme overrides ---- */
    .cab-state-pill {{
        padding: 14px 24px;
        border-radius: 10px;
        font-size: 22px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 16px;
        color: {t["state_text"]};
        letter-spacing: 0.5px;
    }}
    .cab-card {{
        background: {t["bg_card"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }}
    .cab-tag {{
        display: inline-block;
        background: {t["tag_bg"]};
        color: {t["tag_text"]};
        padding: 4px 12px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 13px;
        margin: 2px 4px 2px 0;
    }}
    .cab-blocked {{
        background: {t["blocked_bg"]};
        border-left: 4px solid {t["blocked_border"]};
        padding: 10px 14px;
        border-radius: 4px;
        margin: 4px 0;
    }}
    .cab-latency {{
        color: {t["text_secondary"]};
        font-size: 12px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_theme_toggle() -> None:
    """Render a dark/light mode toggle in the sidebar."""
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    with st.sidebar:
        st.markdown("### Theme")
        dark = st.toggle(
            "🌙 Dark Mode",
            value=st.session_state.dark_mode,
            key="dark_mode_toggle",
        )
        if dark != st.session_state.dark_mode:
            st.session_state.dark_mode = dark
            st.rerun()

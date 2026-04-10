"""
theme.py — Dark/Light theme system for C-A-B governance UI.

Usage:
    from frontend.theme import get_theme, inject_theme_css

    theme = get_theme()              # syncs with Streamlit native theme
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
        "Off": "#6b7280",
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
        "Off": "#484f58",
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
    "Off": "⚪",
}


def _is_dark_mode() -> bool:
    """Detect whether Streamlit's native theme is dark.

    Checks ``st.get_option("theme.base")`` which reflects the user's
    choice in the hamburger menu (System / Light / Dark).  Falls back
    to *dark* when no explicit setting exists.
    """
    try:
        base = st.get_option("theme.base")
    except Exception:
        base = None
    if base == "light":
        return False
    if base == "dark":
        return True
    # "System" or unset — default to dark
    return True


def get_theme() -> Dict:
    """Return current theme synced with Streamlit's native theme selector."""
    if _is_dark_mode():
        return DARK_THEME
    return LIGHT_THEME


def inject_theme_css(theme: Dict) -> None:
    """Inject comprehensive CSS overrides for all Streamlit components."""
    t = theme
    css = f"""
    <style>
    /* ============================================================
       Streamlit Global Overrides
       ============================================================ */

    /* App root */
    .stApp {{
        background-color: {t["bg_primary"]} !important;
        color: {t["text_primary"]} !important;
    }}

    /* Header bar */
    [data-testid="stHeader"] {{
        background-color: {t["bg_primary"]} !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div {{
        background-color: {t["bg_secondary"]} !important;
        color: {t["text_primary"]} !important;
    }}
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {{
        color: {t["text_primary"]} !important;
    }}
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] small {{
        color: {t["text_secondary"]} !important;
    }}

    /* ---- All text elements ---- */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown td,
    .stMarkdown th, .stText, h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p {{
        color: {t["text_primary"]} !important;
    }}
    .stCaption, small, .stMarkdown small {{
        color: {t["text_secondary"]} !important;
    }}

    /* ---- Chat components ---- */
    [data-testid="stChatMessage"] {{
        background-color: {t["bg_card"]} !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 8px !important;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] .stMarkdown {{
        color: {t["text_primary"]} !important;
    }}

    /* Chat input — nuclear override: every element inside */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] *,
    [data-testid="stChatInput"] textarea {{
        background-color: {t["bg_card"]} !important;
        color: {t["text_primary"]} !important;
        border-color: {t["border"]} !important;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{
        color: {t["text_secondary"]} !important;
    }}
    /* Bottom fixed bar (sticks to viewport bottom, wraps chat input) */
    [data-testid="stBottom"],
    [data-testid="stBottom"] *,
    .stChatInput,
    .stChatInput * {{
        background-color: {t["bg_primary"]} !important;
    }}
    /* The input field itself should be card-colored, not bg_primary */
    [data-testid="stBottom"] [data-testid="stChatInput"],
    [data-testid="stBottom"] [data-testid="stChatInput"] *,
    [data-testid="stBottom"] textarea {{
        background-color: {t["bg_card"]} !important;
    }}

    /* ---- Scrollable container (chat box) ---- */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border-color: {t["border"]} !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: {t["bg_primary"]} !important;
    }}

    /* ---- Metrics ---- */
    [data-testid="stMetricValue"] {{
        color: {t["text_primary"]} !important;
    }}
    [data-testid="stMetricLabel"] label,
    [data-testid="stMetricLabel"] p {{
        color: {t["text_secondary"]} !important;
    }}

    /* ---- Expanders ---- */
    [data-testid="stExpander"] {{
        background-color: {t["bg_card"]} !important;
        border-color: {t["border"]} !important;
    }}
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {{
        color: {t["text_primary"]} !important;
    }}
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] {{
        color: {t["text_primary"]} !important;
    }}

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {t["bg_primary"]} !important;
        border-bottom: 1px solid {t["border"]} !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {t["text_secondary"]} !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {t["text_primary"]} !important;
    }}

    /* ---- Info / Warning / Error boxes ---- */
    [data-testid="stAlert"] {{
        background-color: {t["bg_card"]} !important;
        color: {t["text_primary"]} !important;
        border-color: {t["border"]} !important;
    }}

    /* ---- Buttons ---- */
    .stButton > button {{
        background-color: {t["bg_card"]} !important;
        color: {t["text_primary"]} !important;
        border-color: {t["border"]} !important;
    }}
    .stButton > button:hover {{
        border-color: {t["text_secondary"]} !important;
    }}

    /* ---- Toggle ---- */
    [data-testid="stToggle"] label span {{
        color: {t["text_primary"]} !important;
    }}

    /* ---- Divider ---- */
    hr {{
        border-color: {t["border"]} !important;
    }}

    /* ---- Code blocks ---- */
    code, .stCodeBlock {{
        background-color: {t["tag_bg"]} !important;
        color: {t["tag_text"]} !important;
    }}

    /* ---- Line chart (sidebar sparkline) ---- */
    [data-testid="stVegaLiteChart"] {{
        background-color: transparent !important;
    }}

    /* ============================================================
       C-A-B Custom Classes
       ============================================================ */

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
        color: {t["text_primary"]};
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

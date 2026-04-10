"""
theme.py — Dark/Light theme system for C-A-B governance UI.

Usage:
    from frontend.theme import get_theme, inject_theme_css

    theme = get_theme()              # syncs with Streamlit native theme
    inject_theme_css(theme)          # injects CSS into the page
    theme["state_colors"]["Safe"]    # use in components
"""

from __future__ import annotations

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
    """Return current theme dict based on Streamlit's native theme setting."""
    if _is_dark_mode():
        return DARK_THEME
    return LIGHT_THEME


def inject_theme_css(theme: Dict) -> None:
    """Inject CSS that works with Streamlit's native theme selector.

    Emits both light and dark CSS variable blocks. Streamlit's native
    System/Light/Dark picker toggles ``[data-theme]`` on the root,
    which activates the matching variable set automatically.
    """
    d = DARK_THEME
    l = LIGHT_THEME

    def _vars(t: Dict) -> str:
        return f"""
            --cab-bg-primary: {t["bg_primary"]};
            --cab-bg-secondary: {t["bg_secondary"]};
            --cab-bg-card: {t["bg_card"]};
            --cab-text-primary: {t["text_primary"]};
            --cab-text-secondary: {t["text_secondary"]};
            --cab-border: {t["border"]};
            --cab-tag-bg: {t["tag_bg"]};
            --cab-tag-text: {t["tag_text"]};
            --cab-blocked-bg: {t["blocked_bg"]};
            --cab-blocked-border: {t["blocked_border"]};
            --cab-state-text: {t["state_text"]};
            --cab-state-safe: {t["state_colors"]["Safe"]};
            --cab-state-suspicious: {t["state_colors"]["Suspicious"]};
            --cab-state-escalating: {t["state_colors"]["Escalating"]};
            --cab-state-restricted: {t["state_colors"]["Restricted"]};
            --cab-state-off: {t["state_colors"]["Off"]};
        """

    css = f"""
    <style>
    /* Default: dark theme variables */
    :root {{
        {_vars(d)}
    }}

    /* Light override: Streamlit sets [data-theme="light"] or
       light-mode background on .stApp when user picks Light */
    :root[data-theme="light"],
    .stApp[style*="background-color: rgb(255, 255, 255)"],
    .stApp[style*="background-color: white"] {{
        {_vars(l)}
    }}

    /* Also respond to prefers-color-scheme for System mode */
    @media (prefers-color-scheme: light) {{
        :root:not([data-theme="dark"]) {{
            {_vars(l)}
        }}
    }}

    /* ============================================================
       C-A-B Custom Classes (use CSS vars, auto-switch with theme)
       ============================================================ */

    .cab-state-pill {{
        padding: 14px 24px;
        border-radius: 10px;
        font-size: 22px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 16px;
        color: var(--cab-state-text);
        letter-spacing: 0.5px;
    }}
    .cab-tag {{
        display: inline-block;
        background: var(--cab-tag-bg);
        color: var(--cab-tag-text);
        padding: 4px 12px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 13px;
        margin: 2px 4px 2px 0;
    }}
    .cab-blocked {{
        background: var(--cab-blocked-bg);
        border-left: 4px solid var(--cab-blocked-border);
        padding: 10px 14px;
        border-radius: 4px;
        margin: 4px 0;
        color: var(--cab-text-primary);
    }}
    .cab-latency {{
        color: var(--cab-text-secondary);
        font-size: 12px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

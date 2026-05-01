"""
theme.py — Design system for the C-A-B Bridge governance console.

Tokens, typography, and base CSS for the Streamlit dashboard. Stays
backwards-compatible with the previous public surface:

    from frontend.theme import get_theme, inject_theme_css, STATE_EMOJI

`get_theme()` still returns a dict with the same keys callers depend on
(`state_colors`, `text_primary`, etc.). New tokens (surface scale,
spacing, radius, accent, font stack) are additive.

Visual concept: a balanced live-broadcast control bridge — calm,
instrumented, restrained. One brand accent, one heartbeat animation,
state colors only where state is meaningful. See app.py docstring for
the full layout rationale.
"""

from __future__ import annotations

from typing import Dict

import streamlit as st


# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------
# State colors are calibrated to a single value per state across both
# themes (the eye reads "Safe-green" the same in light and dark) — only
# surfaces change between dark and light.

# State colors — restrained, paper-friendly. Same hue across light/dark.
_STATE_COLORS = {
    "Safe":        "#3f7d58",  # sage 600  (oklch(58% 0.07 150))
    "Suspicious":  "#a87a2c",  # amber 700 (oklch(58% 0.10 75))
    "Escalating":  "#b85d2e",  # clay 700  (oklch(58% 0.12 50))
    "Restricted":  "#9b3030",  # oxblood   (oklch(48% 0.13 25))
    "Off":         "#9a9690",  # warm grey
}

_BRAND_ACCENT = "#7a5a3a"      # walnut accent — used only on brand mark + LIVE pulse
_WELLBEING    = "#5b5391"      # restrained violet for self-harm/wellbeing tag


LIGHT_THEME: Dict = {
    "name": "light",
    # Surfaces — warm paper, not cool white
    "bg_primary":   "#f7f4ee",   # paper-0
    "bg_secondary": "#efeae0",   # paper-2
    "bg_card":      "#fbf9f4",   # paper-1
    "surface_0":    "#f7f4ee",
    "surface_1":    "#fbf9f4",
    "surface_2":    "#efeae0",
    "surface_3":    "#e6e0d2",
    "hairline":     "#d9d3c4",
    # Text — deep warm ink, not pure black
    "text_primary":   "#1f1b16",
    "text_secondary": "#564f44",
    "text_muted":     "#8a8278",
    "border":         "#d9d3c4",
    "shadow_sm":      "0 1px 2px rgba(31,27,22,0.04)",
    "shadow_md":      "0 6px 16px rgba(31,27,22,0.06)",
    "shadow_lg":      "0 16px 40px rgba(31,27,22,0.08)",
    "state_colors":   _STATE_COLORS,
    "state_text":     "#fbf9f4",
    "tag_bg":         "#efeae0",
    "tag_text":       "#1f1b16",
    "chat_user_bg":   "#efeae0",
    "chat_bot_bg":    "#fbf9f4",
    "blocked_bg":     "#f5e7e3",
    "blocked_border": _STATE_COLORS["Restricted"],
    "expander_bg":    "#fbf9f4",
    "accent":         _BRAND_ACCENT,
    "wellbeing":      _WELLBEING,
}

DARK_THEME: Dict = {
    "name": "dark",
    # Ink-on-paper inversion — still warm, never cool blue
    "bg_primary":   "#1a1814",
    "bg_secondary": "#23201b",
    "bg_card":      "#211e19",
    "surface_0":    "#1a1814",
    "surface_1":    "#211e19",
    "surface_2":    "#2a2620",
    "surface_3":    "#332e26",
    "hairline":     "rgba(232,224,206,0.10)",
    "text_primary":   "#ece6d6",
    "text_secondary": "#b8b0a0",
    "text_muted":     "#7e776c",
    "border":         "rgba(232,224,206,0.10)",
    "shadow_sm":      "0 1px 2px rgba(0,0,0,0.35)",
    "shadow_md":      "0 6px 16px rgba(0,0,0,0.40)",
    "shadow_lg":      "0 16px 40px rgba(0,0,0,0.50)",
    "state_colors":   _STATE_COLORS,
    "state_text":     "#1a1814",
    "tag_bg":         "rgba(232,224,206,0.06)",
    "tag_text":       "#ece6d6",
    "chat_user_bg":   "#23201b",
    "chat_bot_bg":    "#211e19",
    "blocked_bg":     "rgba(155,48,48,0.16)",
    "blocked_border": _STATE_COLORS["Restricted"],
    "expander_bg":    "#211e19",
    "accent":         _BRAND_ACCENT,
    "wellbeing":      _WELLBEING,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

STATE_EMOJI = {
    "Safe":       "●",
    "Suspicious": "●",
    "Escalating": "●",
    "Restricted": "●",
    "Off":        "○",
}


def _is_dark_mode() -> bool:
    """Detect Streamlit's native theme. Defaults to dark when unset."""
    try:
        base = st.get_option("theme.base")
    except Exception:
        base = None
    if base == "light":
        return False
    if base == "dark":
        return True
    return True  # System / unset → dark


def get_theme() -> Dict:
    return DARK_THEME if _is_dark_mode() else LIGHT_THEME


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------


def _vars(t: Dict) -> str:
    """Emit CSS custom properties for the active theme. New tokens are
    additive; legacy names (--cab-bg-primary, --cab-state-safe, …) are
    preserved so existing consumers don't break."""
    sc = t["state_colors"]
    return f"""
        /* Surfaces */
        --cab-bg-primary:   {t["bg_primary"]};
        --cab-bg-secondary: {t["bg_secondary"]};
        --cab-bg-card:      {t["bg_card"]};
        --cab-surface-0:    {t["surface_0"]};
        --cab-surface-1:    {t["surface_1"]};
        --cab-surface-2:    {t["surface_2"]};
        --cab-surface-3:    {t["surface_3"]};
        --cab-hairline:     {t["hairline"]};
        --cab-border:       {t["border"]};

        /* Text */
        --cab-text-primary:   {t["text_primary"]};
        --cab-text-secondary: {t["text_secondary"]};
        --cab-text-muted:     {t["text_muted"]};

        /* States */
        --cab-state-safe:        {sc["Safe"]};
        --cab-state-suspicious:  {sc["Suspicious"]};
        --cab-state-escalating:  {sc["Escalating"]};
        --cab-state-restricted:  {sc["Restricted"]};
        --cab-state-off:         {sc["Off"]};
        --cab-state-text:        {t["state_text"]};

        /* Brand + special */
        --cab-accent:    {t["accent"]};
        --cab-wellbeing: {t["wellbeing"]};

        /* Tags + chat */
        --cab-tag-bg:    {t["tag_bg"]};
        --cab-tag-text:  {t["tag_text"]};
        --cab-blocked-bg:     {t["blocked_bg"]};
        --cab-blocked-border: {t["blocked_border"]};

        /* Spacing scale (4px base) */
        --cab-space-1: 4px;
        --cab-space-2: 8px;
        --cab-space-3: 12px;
        --cab-space-4: 16px;
        --cab-space-5: 20px;
        --cab-space-6: 24px;
        --cab-space-8: 32px;

        /* Radius */
        --cab-radius-sm: 6px;
        --cab-radius-md: 12px;
        --cab-radius-lg: 16px;

        /* Shadows */
        --cab-shadow-sm: {t["shadow_sm"]};
        --cab-shadow-md: {t["shadow_md"]};
        --cab-shadow-lg: {t["shadow_lg"]};

        /* Type */
        --cab-font-sans:  "Inter", -apple-system, BlinkMacSystemFont,
                          "Segoe UI", Helvetica, Arial, sans-serif;
        --cab-font-serif: "Source Serif 4", "Iowan Old Style", Georgia,
                          "Times New Roman", serif;
        --cab-font-mono:  "JetBrains Mono", "Roboto Mono", ui-monospace,
                          SFMono-Regular, Menlo, monospace;
    """


def inject_theme_css(theme: Dict) -> None:
    """Inject design-system CSS variables + base styles into the page."""

    css = f"""
    <style>
    /* Inter + JetBrains Mono.  Streamlit serves Source Sans Pro by default;
       we override at the body level. Falls back to system fonts gracefully
       if Google Fonts is blocked. */
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {{
        {_vars(theme)}
    }}

    /* ====================================================================
       Base typography + body
       ==================================================================== */

    /* Apply Inter only to actual text containers — DO NOT use a wide
       selector like `[class*="st-"]` because Streamlit's expander
       chevrons + sidebar icons are Material Symbols glyphs that depend
       on `font-family: 'Material Symbols Outlined'`. Overriding that
       font makes glyph names ("arrow_right", "arrow_down") render as
       literal text. */
    html, body, .stApp,
    .stMarkdown, .stMarkdown *,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown *,
    [data-testid="stExpander"] summary span,
    [data-testid="stChatMessage"], [data-testid="stChatMessage"] *,
    [data-testid="stButton"] button,
    [data-testid="stTextInput"] input,
    [data-testid="stChatInput"] textarea,
    [data-testid="stRadio"] label,
    [data-testid="stToggle"] label,
    [data-testid="stCheckbox"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stSlider"] label,
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
        font-family: var(--cab-font-sans);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        font-feature-settings: "cv02", "cv03", "cv04", "cv11", "tnum";
    }}

    /* Restore Streamlit's icon font on all material-symbol glyphs.
       Without this, expander chevrons show "arrow_right" / "arrow_down"
       as literal text. */
    .material-symbols-outlined,
    .material-symbols-rounded,
    .material-symbols-sharp,
    .material-icons,
    .material-icons-outlined,
    span[class*="MaterialSymbol"],
    [data-testid="stIconMaterial"],
    [data-testid="stExpander"] summary svg + span,
    [data-testid="stExpander"] summary [class*="material"],
    [data-testid="stExpander"] [class*="symbols"] {{
        font-family: 'Material Symbols Outlined',
                     'Material Symbols Rounded',
                     'Material Icons' !important;
    }}

    .stApp {{
        background: var(--cab-surface-0);
        color: var(--cab-text-primary);
    }}

    /* Block container — slightly tighter top padding (Streamlit default
       is 6rem which wastes the demo's first 100 px). */
    [data-testid="stMainBlockContainer"],
    .block-container {{
        padding-top: 1.4rem !important;
        padding-bottom: 1.6rem !important;
        max-width: 1480px !important;
    }}

    /* ====================================================================
       Sidebar polish
       ==================================================================== */

    [data-testid="stSidebar"] {{
        background: var(--cab-surface-1);
        border-right: 1px solid var(--cab-hairline);
    }}
    [data-testid="stSidebar"] .stMarkdown h3 {{
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--cab-text-secondary) !important;
        margin: 0 0 8px 0 !important;
    }}
    [data-testid="stSidebar"] hr {{
        border: 0;
        border-top: 1px solid var(--cab-hairline);
        margin: 14px 0;
    }}

    /* ====================================================================
       Custom utility classes — used by components.py + app.py
       ==================================================================== */

    .cab-eyebrow {{
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--cab-text-secondary);
        margin: 2px 0 8px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .cab-eyebrow::after {{
        content: "";
        flex: 1;
        height: 1px;
        background: var(--cab-hairline);
        margin-left: 4px;
    }}

    /* Top status bar */
    .cab-topbar {{
        display: flex;
        align-items: center;
        gap: var(--cab-space-4);
        padding: 12px 18px;
        background: linear-gradient(180deg,
            var(--cab-surface-1) 0%,
            var(--cab-surface-2) 100%);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-lg);
        box-shadow: var(--cab-shadow-sm);
        margin: 0 0 var(--cab-space-4) 0;
        flex-wrap: wrap;
    }}
    .cab-brand {{
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 0;
    }}
    .cab-brand-mark {{
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background:
            radial-gradient(circle at 30% 30%, var(--cab-accent) 0%, transparent 60%),
            linear-gradient(135deg, var(--cab-state-safe) 0%, var(--cab-accent) 100%);
        position: relative;
        flex-shrink: 0;
    }}
    .cab-brand-mark::after {{
        content: "";
        position: absolute; inset: 6px;
        border: 1.5px solid rgba(255,255,255,0.85);
        border-radius: 5px;
    }}
    .cab-brand-title {{
        font-family: var(--cab-font-serif);
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 0.01em;
        color: var(--cab-text-primary);
        line-height: 1;
    }}
    .cab-brand-sub {{
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--cab-text-muted);
        margin-top: 3px;
    }}
    .cab-live {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 5px 11px;
        border-radius: 999px;
        background: rgba(155,48,48,0.10);
        border: 1px solid rgba(155,48,48,0.25);
        font-family: var(--cab-font-mono);
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--cab-state-restricted);
    }}
    .cab-live-dot {{
        width: 7px; height: 7px;
        border-radius: 50%;
        background: var(--cab-state-restricted);
        box-shadow: 0 0 0 0 rgba(155,48,48,0.60);
        animation: cab-pulse 1.8s ease-out infinite;
    }}
    @keyframes cab-pulse {{
        0%   {{ box-shadow: 0 0 0 0 rgba(155,48,48,0.55); }}
        70%  {{ box-shadow: 0 0 0 9px rgba(155,48,48,0);  }}
        100% {{ box-shadow: 0 0 0 0 rgba(155,48,48,0);    }}
    }}
    .cab-mode-chip {{
        display: inline-flex;
        flex-direction: column;
        gap: 1px;
        padding: 6px 12px;
        border-radius: var(--cab-radius-md);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.06em;
        line-height: 1.15;
    }}
    .cab-mode-chip[data-mode="cab"] {{
        background: rgba(63,125,88,0.10);
        border: 1px solid rgba(63,125,88,0.30);
        color: var(--cab-state-safe);
    }}
    .cab-mode-chip[data-mode="baseline"] {{
        background: rgba(155,48,48,0.10);
        border: 1px solid rgba(155,48,48,0.30);
        color: var(--cab-state-restricted);
    }}
    .cab-mode-chip-sub {{
        font-size: 9.5px;
        font-weight: 600;
        opacity: 0.78;
        letter-spacing: 0.04em;
        text-transform: none;
    }}

    /* Stat cluster (right side of top bar) */
    .cab-stats {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-left: auto;
    }}
    .cab-stat {{
        display: flex;
        flex-direction: column;
        gap: 1px;
        padding: 4px 12px;
        background: var(--cab-surface-2);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-md);
        min-width: 70px;
    }}
    .cab-stat-label {{
        font-size: 9.5px;
        font-weight: 600;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        color: var(--cab-text-muted);
    }}
    .cab-stat-value {{
        font-family: var(--cab-font-serif);
        font-size: 17px;
        font-weight: 600;
        color: var(--cab-text-primary);
        font-variant-numeric: tabular-nums;
        line-height: 1.1;
    }}
    .cab-stat--accent .cab-stat-value {{ color: var(--cab-state-restricted); }}
    .cab-stat--ok .cab-stat-value     {{ color: var(--cab-state-safe); }}

    /* Verdict ribbon (sits above Aria iframe) */
    .cab-ribbon {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-left: 4px solid var(--cab-state-off);
        border-radius: var(--cab-radius-md);
        box-shadow: var(--cab-shadow-sm);
        margin: 0 0 12px 0;
        flex-wrap: wrap;
        min-height: 56px;
    }}
    .cab-ribbon[data-state="Safe"]       {{ border-left-color: var(--cab-state-safe); }}
    .cab-ribbon[data-state="Suspicious"] {{ border-left-color: var(--cab-state-suspicious); }}
    .cab-ribbon[data-state="Escalating"] {{ border-left-color: var(--cab-state-escalating); }}
    .cab-ribbon[data-state="Restricted"] {{ border-left-color: var(--cab-state-restricted); }}
    .cab-ribbon-action {{
        font-family: var(--cab-font-mono);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.12em;
        padding: 4px 10px;
        border-radius: 6px;
        color: #fff;
    }}
    .cab-ribbon-state {{
        font-family: var(--cab-font-serif);
        font-size: 15px;
        font-weight: 600;
        letter-spacing: 0.01em;
        color: var(--cab-text-primary);
    }}
    .cab-ribbon-score {{
        font-family: var(--cab-font-mono);
        font-size: 12px;
        font-weight: 500;
        color: var(--cab-text-secondary);
        font-variant-numeric: tabular-nums;
    }}
    .cab-chip {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 9px;
        background: var(--cab-tag-bg);
        color: var(--cab-tag-text);
        border-radius: 5px;
        font-family: var(--cab-font-mono);
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.02em;
    }}
    .cab-chip--injection {{
        background: rgba(155,48,48,0.12);
        color: var(--cab-state-restricted);
        font-weight: 700;
    }}
    .cab-chip--wellbeing {{
        background: rgba(91,83,145,0.14);
        color: var(--cab-wellbeing);
        font-weight: 700;
    }}

    /* Generic panel container */
    .cab-panel {{
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-md);
        padding: 14px 16px;
        box-shadow: var(--cab-shadow-sm);
    }}
    .cab-panel-empty {{
        padding: 22px 16px;
        text-align: center;
        background: var(--cab-surface-1);
        border: 1px dashed var(--cab-hairline);
        border-radius: var(--cab-radius-md);
        color: var(--cab-text-muted);
        font-size: 13px;
        font-style: italic;
    }}

    /* Pipeline trace card */
    .cab-pipeline {{
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-md);
        padding: 10px 14px;
        box-shadow: var(--cab-shadow-sm);
    }}
    .cab-pipeline-row {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 4px;
        border-bottom: 1px solid var(--cab-hairline);
        font-size: 13px;
    }}
    .cab-pipeline-row:last-child {{ border-bottom: 0; }}
    .cab-pipeline-icon {{
        width: 22px; text-align: center; font-size: 14px;
        opacity: 0.85;
    }}
    .cab-pipeline-name {{
        font-weight: 600;
        color: var(--cab-text-primary);
        min-width: 124px;
    }}
    .cab-pipeline-status {{
        font-family: var(--cab-font-mono);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        padding: 2px 8px;
        border-radius: 5px;
    }}
    .cab-pipeline-status--pass {{ background: rgba(63,125,88,0.14);   color: var(--cab-state-safe); }}
    .cab-pipeline-status--high {{ background: rgba(155,48,48,0.14);   color: var(--cab-state-restricted); }}
    .cab-pipeline-status--med  {{ background: rgba(168,122,44,0.16);  color: var(--cab-state-suspicious); }}
    .cab-pipeline-status--low  {{ background: rgba(63,125,88,0.14);   color: var(--cab-state-safe); }}
    .cab-pipeline-status--skip {{ background: var(--cab-tag-bg);      color: var(--cab-text-muted); }}
    .cab-pipeline-detail {{
        font-family: var(--cab-font-mono);
        font-size: 11.5px;
        color: var(--cab-text-secondary);
        margin-left: auto;
        text-align: right;
        max-width: 60%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}

    /* Event card list */
    .cab-event {{
        display: flex;
        gap: 12px;
        padding: 12px 14px;
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-left: 3px solid var(--cab-state-off);
        border-radius: var(--cab-radius-md);
        margin: 0 0 8px 0;
    }}
    .cab-event[data-state="Safe"]       {{ border-left-color: var(--cab-state-safe); }}
    .cab-event[data-state="Suspicious"] {{ border-left-color: var(--cab-state-suspicious); }}
    .cab-event[data-state="Escalating"] {{ border-left-color: var(--cab-state-escalating); }}
    .cab-event[data-state="Restricted"] {{ border-left-color: var(--cab-state-restricted); }}
    .cab-event-turn {{
        font-family: var(--cab-font-mono);
        font-size: 11px;
        font-weight: 700;
        color: var(--cab-text-muted);
        letter-spacing: 0.04em;
        min-width: 52px;
        padding-top: 1px;
    }}
    .cab-event-body {{ flex: 1; min-width: 0; }}
    .cab-event-head {{
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 4px;
    }}
    .cab-event-state {{
        font-family: var(--cab-font-serif);
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.01em;
    }}
    .cab-event-msg {{
        font-size: 13px;
        color: var(--cab-text-primary);
        line-height: 1.45;
        word-wrap: break-word;
    }}
    .cab-event-block {{
        font-size: 12px;
        color: var(--cab-state-restricted);
        font-style: italic;
        margin-top: 4px;
    }}

    /* Legacy classes — kept so existing markup in components.py /
       risk_panel.py keeps rendering (no inline-style migration required). */
    .cab-state-pill {{
        padding: 14px 24px;
        border-radius: var(--cab-radius-md);
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
        border-radius: 5px;
        font-family: var(--cab-font-mono);
        font-size: 12px;
        margin: 2px 4px 2px 0;
    }}
    .cab-blocked {{
        background: var(--cab-blocked-bg);
        border-left: 4px solid var(--cab-blocked-border);
        padding: 10px 14px;
        border-radius: var(--cab-radius-sm);
        margin: 4px 0;
        color: var(--cab-text-primary);
    }}
    .cab-latency {{
        color: var(--cab-text-secondary);
        font-size: 12px;
    }}

    /* ====================================================================
       Streamlit native widget overrides
       ==================================================================== */

    /* Suppress red focus ring on expanders (pre-existing fix). */
    [data-testid="stExpander"] details summary:focus,
    [data-testid="stExpander"] details summary:focus-visible,
    [data-testid="stExpander"] details:focus,
    [data-testid="stExpander"] details:focus-visible,
    [data-testid="stExpander"]:focus-within {{
        outline: none !important;
        box-shadow: none !important;
        border-color: var(--cab-hairline) !important;
    }}
    [data-testid="stExpander"] details[open] {{
        border-color: var(--cab-hairline) !important;
    }}
    [data-testid="stExpander"] {{
        border: 1px solid var(--cab-hairline) !important;
        border-radius: var(--cab-radius-md) !important;
        background: var(--cab-surface-1) !important;
    }}
    [data-testid="stExpander"] summary {{
        font-weight: 600 !important;
        font-size: 13px !important;
    }}

    /* Bump non-primary button visibility. */
    [data-testid="stButton"] button[kind="secondary"]:not(:disabled),
    [data-testid="stButton"] button:not([kind="primary"]):not([kind="primaryFormSubmit"]):not(:disabled) {{
        border: 1px solid var(--cab-hairline) !important;
        color: var(--cab-text-primary) !important;
        background: var(--cab-surface-1) !important;
    }}
    [data-testid="stButton"] button[kind="secondary"]:disabled,
    [data-testid="stButton"] button:not([kind="primary"]):not([kind="primaryFormSubmit"]):disabled {{
        border: 1px solid var(--cab-hairline) !important;
        color: var(--cab-text-muted) !important;
        opacity: 0.55 !important;
    }}
    [data-testid="stButton"] button[kind="secondary"]:hover:not(:disabled),
    [data-testid="stButton"] button:not([kind="primary"]):not([kind="primaryFormSubmit"]):hover:not(:disabled) {{
        border-color: var(--cab-text-secondary) !important;
        background: var(--cab-surface-2) !important;
    }}
    [data-testid="stButton"] button[kind="primary"] {{
        background: var(--cab-state-safe) !important;
        border-color: var(--cab-state-safe) !important;
    }}

    /* Chat-message bubbles */
    [data-testid="stChatMessage"] {{
        background: var(--cab-surface-1) !important;
        border: 1px solid var(--cab-hairline) !important;
        border-radius: var(--cab-radius-md) !important;
        padding: 10px 14px !important;
        margin: 6px 0 !important;
    }}

    /* Container with explicit height (transcript scroll box) */
    [data-testid="stVerticalBlock"] [data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: var(--cab-radius-md);
    }}

    /* Scrollbar (webkit) */
    *::-webkit-scrollbar       {{ width: 9px; height: 9px; }}
    *::-webkit-scrollbar-thumb {{
        background: var(--cab-hairline);
        border-radius: 999px;
    }}
    *::-webkit-scrollbar-thumb:hover {{
        background: var(--cab-text-muted);
    }}
    *::-webkit-scrollbar-track {{ background: transparent; }}

    /* Subtle fade-in for transcript turns */
    @keyframes cab-fade-in {{
        from {{ opacity: 0; transform: translateY(2px); }}
        to   {{ opacity: 1; transform: translateY(0);   }}
    }}
    [data-testid="stChatMessage"] {{ animation: cab-fade-in 180ms ease-out; }}

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

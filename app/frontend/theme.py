"""
theme.py — Design system for the C-A-B Bridge governance console.
Anthropic/Stripe-inspired: warm paper, ink black, Source Serif display +
Inter body + JetBrains Mono data. Restrained, instrumented, broadcast-grade.

Public surface preserved (do not break callers):
    from frontend.theme import (
        get_theme, inject_theme_css, STATE_EMOJI,
        LIGHT_THEME, DARK_THEME,
    )
"""

from __future__ import annotations
from typing import Dict
import streamlit as st


# ---------------------------------------------------------------------------
# State colors — calibrated low-saturation oklch (one value per state across
# both themes; only surfaces change between light and dark).
# ---------------------------------------------------------------------------

_STATE_COLORS = {
    "Safe":        "oklch(60% 0.10 155)",
    "Suspicious":  "oklch(58% 0.11 75)",
    "Escalating":  "oklch(62% 0.14 40)",
    "Restricted":  "oklch(52% 0.16 25)",
    "Off":         "oklch(60% 0 0)",
}
_BRAND_ACCENT = "oklch(55% 0.15 28)"   # warm clay
_WELLBEING    = "oklch(52% 0.12 290)"  # subdued violet


LIGHT_THEME: Dict = {
    "name": "light",
    "bg_primary":   "#FAF8F5",
    "bg_secondary": "#F4F1EC",
    "bg_card":      "#FAF8F5",
    "surface_0":    "#FAF8F5",
    "surface_1":    "#F4F1EC",
    "surface_2":    "#EEEAE2",
    "surface_3":    "#E8E2DA",
    "hairline":     "#E2DCD2",
    "text_primary": "#1F1B16",
    "text_secondary": "#6E665B",
    "text_muted":   "#9A9388",
    "border":       "#E2DCD2",
    "shadow_sm":    "0 1px 0 rgba(31,27,22,0.04), 0 1px 2px rgba(31,27,22,0.04)",
    "shadow_md":    "0 1px 0 rgba(31,27,22,0.04), 0 6px 16px rgba(31,27,22,0.06)",
    "shadow_lg":    "0 1px 0 rgba(31,27,22,0.04), 0 12px 32px rgba(31,27,22,0.08)",
    "state_colors": _STATE_COLORS,
    "state_text":   "#FAF8F5",
    "tag_bg":       "#EEEAE2",
    "tag_text":     "#3A352E",
    "chat_user_bg": "#F4F1EC",
    "chat_bot_bg":  "#FAF8F5",
    "blocked_bg":   "color-mix(in oklch, " + _STATE_COLORS["Restricted"] + " 6%, transparent)",
    "blocked_border": _STATE_COLORS["Restricted"],
    "expander_bg":  "#FAF8F5",
    "accent":       _BRAND_ACCENT,
    "wellbeing":    _WELLBEING,
}

DARK_THEME: Dict = {
    "name": "dark",
    "bg_primary":   "#14110D",
    "bg_secondary": "#1B1814",
    "bg_card":      "#14110D",
    "surface_0":    "#14110D",
    "surface_1":    "#1B1814",
    "surface_2":    "#221E18",
    "surface_3":    "#2B2620",
    "hairline":     "#2C2720",
    "text_primary": "#F2EDE4",
    "text_secondary": "#9A9388",
    "text_muted":   "#6E665B",
    "border":       "#2C2720",
    "shadow_sm":    "0 1px 2px rgba(0,0,0,0.30)",
    "shadow_md":    "0 4px 14px rgba(0,0,0,0.32)",
    "shadow_lg":    "0 12px 32px rgba(0,0,0,0.40)",
    "state_colors": _STATE_COLORS,
    "state_text":   "#F2EDE4",
    "tag_bg":       "#221E18",
    "tag_text":     "#D6CFC2",
    "chat_user_bg": "#1B1814",
    "chat_bot_bg":  "#14110D",
    "blocked_bg":   "color-mix(in oklch, " + _STATE_COLORS["Restricted"] + " 14%, transparent)",
    "blocked_border": _STATE_COLORS["Restricted"],
    "expander_bg":  "#1B1814",
    "accent":       _BRAND_ACCENT,
    "wellbeing":    _WELLBEING,
}


STATE_EMOJI = {
    "Safe":       "●",
    "Suspicious": "●",
    "Escalating": "●",
    "Restricted": "●",
    "Off":        "○",
}


def _is_dark_mode() -> bool:
    """Detect Streamlit's native theme. DEFAULTS TO LIGHT (paper) — the
    Anthropic/Stripe palette is the canonical look."""
    try:
        base = st.get_option("theme.base")
    except Exception:
        base = None
    return base == "dark"


def get_theme() -> Dict:
    return DARK_THEME if _is_dark_mode() else LIGHT_THEME


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------

def _vars(t: Dict) -> str:
    sc = t["state_colors"]
    return f"""
        --cab-bg-primary:   {t["bg_primary"]};
        --cab-bg-secondary: {t["bg_secondary"]};
        --cab-bg-card:      {t["bg_card"]};
        --cab-surface-0:    {t["surface_0"]};
        --cab-surface-1:    {t["surface_1"]};
        --cab-surface-2:    {t["surface_2"]};
        --cab-surface-3:    {t["surface_3"]};
        --cab-hairline:     {t["hairline"]};
        --cab-border:       {t["border"]};

        --cab-text-primary:   {t["text_primary"]};
        --cab-text-secondary: {t["text_secondary"]};
        --cab-text-muted:     {t["text_muted"]};

        --cab-state-safe:        {sc["Safe"]};
        --cab-state-suspicious:  {sc["Suspicious"]};
        --cab-state-escalating:  {sc["Escalating"]};
        --cab-state-restricted:  {sc["Restricted"]};
        --cab-state-off:         {sc["Off"]};
        --cab-state-text:        {t["state_text"]};

        --cab-accent:    {t["accent"]};
        --cab-wellbeing: {t["wellbeing"]};

        --cab-tag-bg:    {t["tag_bg"]};
        --cab-tag-text:  {t["tag_text"]};
        --cab-blocked-bg:     {t["blocked_bg"]};
        --cab-blocked-border: {t["blocked_border"]};

        --cab-space-1: 4px;  --cab-space-2: 8px;  --cab-space-3: 12px;
        --cab-space-4: 16px; --cab-space-5: 20px; --cab-space-6: 24px;
        --cab-space-8: 32px;

        --cab-radius-sm: 4px; --cab-radius-md: 6px;
        --cab-radius-lg: 10px; --cab-radius-xl: 14px;

        --cab-shadow-sm: {t["shadow_sm"]};
        --cab-shadow-md: {t["shadow_md"]};
        --cab-shadow-lg: {t["shadow_lg"]};

        --cab-font-serif: "Source Serif 4", "Newsreader", "Tiempos Text", Georgia, serif;
        --cab-font-sans:  "Inter Tight", "Inter", -apple-system, "Helvetica Neue", Arial, sans-serif;
        --cab-font-mono:  "JetBrains Mono", "IBM Plex Mono", ui-monospace, Menlo, monospace;
    """


def inject_theme_css(theme: Dict) -> None:
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {{
        {_vars(theme)}
    }}

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
        font-feature-settings: "ss01", "cv02", "cv11", "tnum";
    }}

    .material-symbols-outlined, .material-symbols-rounded, .material-symbols-sharp,
    .material-icons, .material-icons-outlined,
    span[class*="MaterialSymbol"], [data-testid="stIconMaterial"],
    [data-testid="stExpander"] summary [class*="material"],
    [data-testid="stExpander"] [class*="symbols"] {{
        font-family: 'Material Symbols Outlined','Material Symbols Rounded','Material Icons' !important;
    }}

    .stApp {{
        background: {theme["surface_0"]};
        background-image: radial-gradient(ellipse 80% 60% at 50% 0%,
            rgba(31,27,22,0.025), transparent 70%);
        color: var(--cab-text-primary);
    }}

    [data-testid="stMainBlockContainer"], .block-container {{
        padding-top: 1.4rem !important;
        padding-bottom: 1.6rem !important;
        max-width: 1480px !important;
    }}

    [data-testid="stSidebar"] {{
        background: var(--cab-surface-1);
        border-right: 1px solid var(--cab-hairline);
    }}
    [data-testid="stSidebar"] .stMarkdown h3 {{
        font-size: 10.5px !important; font-weight: 600 !important;
        letter-spacing: 0.10em; text-transform: uppercase;
        color: var(--cab-text-secondary) !important;
        margin: 0 0 8px 0 !important;
    }}
    [data-testid="stSidebar"] hr {{ border:0; border-top:1px solid var(--cab-hairline); margin:14px 0; }}

    /* serif display */
    .cab-serif, .cab-brand-title, .cab-stat-value, .cab-verdict-state,
    .cab-pipeline-title, .cab-evidence-title, .cab-ladder-title {{
        font-family: var(--cab-font-serif) !important;
        font-weight: 400; letter-spacing: -0.015em;
    }}

    /* ===== Eyebrow ===== */
    .cab-eyebrow {{
        font-size: 10.5px; font-weight: 600;
        letter-spacing: 0.14em; text-transform: uppercase;
        color: var(--cab-text-secondary);
        margin: 2px 0 10px 2px;
        display: flex; align-items: center; gap: 10px;
    }}
    .cab-eyebrow::after {{
        content: ""; flex: 1; height: 1px;
        background: var(--cab-hairline); align-self: center;
    }}

    /* ===== Top status bar ===== */
    .cab-topbar {{
        display: flex; align-items: center; gap: var(--cab-space-4);
        padding: 18px 22px;
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-xl);
        box-shadow: var(--cab-shadow-sm);
        margin: 0 0 var(--cab-space-4) 0;
        flex-wrap: wrap;
    }}
    .cab-brand {{ display:flex; align-items:center; gap:14px; min-width:0; }}
    .cab-brand-mark {{
        width: 36px; height: 36px; border-radius: 8px;
        background: linear-gradient(135deg, var(--cab-text-primary) 0%, #3A352E 100%);
        position: relative; flex-shrink: 0;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);
    }}
    .cab-brand-mark::before {{
        content: ""; position: absolute;
        left: 8px; top: 10px; width: 12px; height: 1.5px;
        background: var(--cab-surface-0); border-radius: 1px;
        box-shadow: 0 4px 0 var(--cab-surface-0), 0 8px 0 var(--cab-surface-0);
    }}
    .cab-brand-mark::after {{
        content: ""; position: absolute;
        right: 9px; top: 12px; width: 6px; height: 6px; border-radius: 50%;
        background: var(--cab-accent);
        box-shadow: 0 0 0 3px var(--cab-text-primary), 0 0 0 4px rgba(255,255,255,0.10);
    }}
    .cab-brand-title {{
        font-size: 22px; font-weight: 500;
        color: var(--cab-text-primary); line-height: 1.15;
    }}
    .cab-brand-sub {{
        font-size: 11px; font-weight: 500;
        letter-spacing: 0.10em; text-transform: uppercase;
        color: var(--cab-text-secondary); margin-top: 4px;
    }}
    .cab-live {{
        display: inline-flex; align-items: center; gap: 8px;
        padding: 6px 12px; border-radius: 999px;
        background: color-mix(in oklch, var(--cab-state-restricted) 8%, transparent);
        border: 1px solid color-mix(in oklch, var(--cab-state-restricted) 25%, transparent);
        font-family: var(--cab-font-mono);
        font-size: 11px; font-weight: 600;
        letter-spacing: 0.14em; text-transform: uppercase;
        color: var(--cab-state-restricted);
        /* Anchor the operational cluster (LIVE + mode chip + stats) to
           the right edge of the topbar so the brand block sits flush
           left and the empty whitespace lives between brand and the
           cluster — readable as one balanced row instead of two
           separated bunches. */
        margin-left: auto;
    }}
    .cab-live-dot {{
        width: 7px; height: 7px; border-radius: 50%;
        background: var(--cab-state-restricted);
        animation: cab-pulse 1.8s ease-out infinite;
    }}
    @keyframes cab-pulse {{
        0%   {{ box-shadow: 0 0 0 0 color-mix(in oklch, var(--cab-state-restricted) 55%, transparent); }}
        70%  {{ box-shadow: 0 0 0 8px transparent; }}
        100% {{ box-shadow: 0 0 0 0 transparent; }}
    }}

    .cab-stat {{
        padding: 4px 12px;
        border-left: 1px solid var(--cab-hairline);
        display: flex; flex-direction: column; gap: 4px;
        white-space: nowrap; min-width: 78px;
    }}
    .cab-stat:first-child {{ border-left: 0; padding-left: 0; }}
    .cab-stat-label {{
        font-size: 10px; font-weight: 600;
        letter-spacing: 0.08em; text-transform: uppercase;
        color: var(--cab-text-secondary); white-space: nowrap;
    }}
    .cab-stat-value {{
        font-family: var(--cab-font-serif);
        font-size: 24px; font-weight: 400; line-height: 1;
        color: var(--cab-text-primary); letter-spacing: -0.02em;
    }}
    .cab-stat--accent .cab-stat-value {{ color: var(--cab-state-restricted); }}
    .cab-stat--ok     .cab-stat-value {{ color: var(--cab-state-safe); }}

    .cab-mode-chip {{
        display: inline-flex; flex-direction: column; gap: 2px;
        padding: 8px 14px; border-radius: var(--cab-radius-md);
        border: 1px solid var(--cab-hairline);
        background: var(--cab-surface-0);
        min-width: 156px;
    }}
    .cab-mode-chip span:first-child {{
        font-family: var(--cab-font-mono);
        font-size: 11px; font-weight: 600;
        letter-spacing: 0.10em; text-transform: uppercase;
        color: var(--cab-text-primary);
    }}
    .cab-mode-chip[data-mode="cab"] span:first-child {{ color: var(--cab-state-safe); }}
    .cab-mode-chip[data-mode="baseline"] span:first-child {{ color: var(--cab-state-restricted); }}
    .cab-mode-chip-sub {{
        font-size: 10.5px; color: var(--cab-text-secondary);
    }}

    /* ===== Verdict ribbon ===== */
    .cab-verdict {{
        display: flex; align-items: center; gap: 16px;
        padding: 14px 18px 14px 22px;
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-xl);
        box-shadow: var(--cab-shadow-sm);
        position: relative; overflow: hidden;
        min-height: 64px;
    }}
    .cab-verdict::before {{
        content: ""; position: absolute; left: 0; top: 0; bottom: 0;
        width: 4px; background: var(--cab-state-off);
    }}
    .cab-verdict[data-state="Safe"]::before       {{ background: var(--cab-state-safe); }}
    .cab-verdict[data-state="Suspicious"]::before {{ background: var(--cab-state-suspicious); }}
    .cab-verdict[data-state="Escalating"]::before {{ background: var(--cab-state-escalating); }}
    .cab-verdict[data-state="Restricted"]::before {{ background: var(--cab-state-restricted); }}
    .cab-verdict-action {{
        font-family: var(--cab-font-mono);
        font-size: 11px; font-weight: 700;
        letter-spacing: 0.14em; text-transform: uppercase;
        padding: 5px 11px; border-radius: var(--cab-radius-sm);
        background: var(--cab-surface-2);
        border: 1px solid var(--cab-hairline);
        color: var(--cab-text-primary);
    }}
    .cab-verdict[data-state="Safe"]       .cab-verdict-action {{ color: var(--cab-state-safe);       background: color-mix(in oklch, var(--cab-state-safe) 10%, transparent); }}
    .cab-verdict[data-state="Suspicious"] .cab-verdict-action {{ color: var(--cab-state-suspicious); background: color-mix(in oklch, var(--cab-state-suspicious) 10%, transparent); }}
    .cab-verdict[data-state="Escalating"] .cab-verdict-action {{ color: var(--cab-state-escalating); background: color-mix(in oklch, var(--cab-state-escalating) 10%, transparent); }}
    .cab-verdict[data-state="Restricted"] .cab-verdict-action {{ color: var(--cab-state-restricted); background: color-mix(in oklch, var(--cab-state-restricted) 10%, transparent); }}
    .cab-verdict-state {{
        font-size: 22px; line-height: 1;
        color: var(--cab-text-primary);
    }}
    .cab-verdict-meta {{
        display: flex; align-items: center; gap: 14px; flex: 1;
        font-family: var(--cab-font-mono); font-size: 11.5px;
        color: var(--cab-text-secondary);
    }}

    /* ===== Pipeline trace card ===== */
    .cab-pipeline-card {{
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-xl);
        box-shadow: var(--cab-shadow-sm);
        overflow: hidden;
        margin-top: 18px;
    }}
    .cab-pipeline-head {{
        display: flex; align-items: baseline; justify-content: space-between;
        padding: 14px 22px 10px;
        border-bottom: 1px solid var(--cab-hairline);
    }}
    .cab-pipeline-title {{ font-size: 15px; color: var(--cab-text-primary); letter-spacing: -0.01em; }}
    .cab-pipeline-sub   {{ font-family: var(--cab-font-mono); font-size: 11px; color: var(--cab-text-muted); }}
    .cab-prow {{
        display: grid;
        grid-template-columns: 28px 180px 80px 1fr;
        align-items: center; gap: 12px;
        padding: 12px 22px;
        border-bottom: 1px solid var(--cab-hairline);
    }}
    .cab-prow:last-child {{ border-bottom: 0; }}
    .cab-prow-icon {{
        width: 22px; height: 22px; border-radius: var(--cab-radius-sm);
        background: var(--cab-surface-2);
        display: grid; place-items: center;
        font-family: var(--cab-font-mono); font-size: 11px; font-weight: 700;
        color: var(--cab-text-secondary);
    }}
    .cab-prow-name   {{ font-size: 13.5px; color: var(--cab-text-primary); font-weight: 500; }}
    .cab-prow-status {{
        justify-self: start;
        font-family: var(--cab-font-mono); font-size: 10.5px; font-weight: 700;
        letter-spacing: 0.10em; text-transform: uppercase;
        padding: 3px 9px; border-radius: var(--cab-radius-sm);
        background: var(--cab-surface-2); color: var(--cab-text-secondary);
        border: 1px solid var(--cab-hairline);
    }}
    .cab-prow-status[data-s="PASS"] {{ background: color-mix(in oklch, var(--cab-state-safe) 12%, transparent); color: var(--cab-state-safe); border-color: color-mix(in oklch, var(--cab-state-safe) 25%, transparent); }}
    .cab-prow-status[data-s="LOW"]  {{ background: color-mix(in oklch, var(--cab-state-safe) 12%, transparent); color: var(--cab-state-safe); border-color: color-mix(in oklch, var(--cab-state-safe) 25%, transparent); }}
    .cab-prow-status[data-s="MED"]  {{ background: color-mix(in oklch, var(--cab-state-suspicious) 12%, transparent); color: var(--cab-state-suspicious); border-color: color-mix(in oklch, var(--cab-state-suspicious) 28%, transparent); }}
    .cab-prow-status[data-s="HIGH"] {{ background: color-mix(in oklch, var(--cab-state-restricted) 12%, transparent); color: var(--cab-state-restricted); border-color: color-mix(in oklch, var(--cab-state-restricted) 28%, transparent); }}
    .cab-prow-status[data-s="BLOCK"]{{ background: color-mix(in oklch, var(--cab-state-restricted) 12%, transparent); color: var(--cab-state-restricted); border-color: color-mix(in oklch, var(--cab-state-restricted) 28%, transparent); }}
    .cab-prow-status[data-s="SKIP"] {{ color: var(--cab-text-muted); }}
    .cab-prow-detail {{
        font-family: var(--cab-font-mono); font-size: 11.5px;
        color: var(--cab-text-secondary);
        text-align: right; justify-self: end;
        max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }}

    /* ===== State ladder ===== */
    .cab-ladder {{
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-xl);
        box-shadow: var(--cab-shadow-sm);
        padding: 18px 22px 16px;
        margin-top: 18px;
    }}
    .cab-ladder-head {{
        display: flex; justify-content: space-between; align-items: baseline;
        margin-bottom: 14px;
    }}
    .cab-ladder-title {{ font-size: 15px; color: var(--cab-text-primary); }}
    .cab-ladder-score {{ font-family: var(--cab-font-mono); font-size: 11px; color: var(--cab-text-muted); }}
    .cab-ladder-track {{
        display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 0;
        margin-bottom: 6px; position: relative;
    }}
    .cab-ladder-rung {{
        position: relative;
        padding: 10px 12px 12px;
        border-top: 2px solid var(--cab-hairline);
    }}
    .cab-ladder-rung[data-on="true"]                   {{ border-top-color: currentColor; }}
    .cab-ladder-rung[data-rung="Safe"]                 {{ color: var(--cab-state-safe); }}
    .cab-ladder-rung[data-rung="Suspicious"]           {{ color: var(--cab-state-suspicious); }}
    .cab-ladder-rung[data-rung="Escalating"]           {{ color: var(--cab-state-escalating); }}
    .cab-ladder-rung[data-rung="Restricted"]           {{ color: var(--cab-state-restricted); }}
    .cab-ladder-rung-name {{
        font-family: var(--cab-font-mono);
        font-size: 10.5px; font-weight: 700;
        letter-spacing: 0.08em; text-transform: uppercase;
        color: var(--cab-text-secondary);
    }}
    .cab-ladder-rung[data-on="true"] .cab-ladder-rung-name {{ color: currentColor; }}
    .cab-ladder-rung-action {{ font-size: 11px; color: var(--cab-text-muted); margin-top: 3px; }}
    .cab-ladder-rung-marker {{
        position: absolute; top: -7px;
        width: 10px; height: 10px; border-radius: 50%;
        background: var(--cab-surface-1); border: 2px solid var(--cab-hairline);
    }}
    .cab-ladder-rung[data-on="true"] .cab-ladder-rung-marker {{ background: currentColor; border-color: currentColor; }}
    .cab-ladder-rung[data-current="true"] .cab-ladder-rung-marker {{
        box-shadow: 0 0 0 4px color-mix(in oklch, currentColor 18%, transparent);
    }}

    /* ===== Event card list (transcript turns) ===== */
    .cab-event {{
        display: flex; gap: 14px;
        padding: 14px 16px;
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
        font-size: 11px; font-weight: 600;
        color: var(--cab-text-muted);
        letter-spacing: 0.04em; min-width: 52px; padding-top: 1px;
    }}
    .cab-event-body {{ flex: 1; min-width: 0; }}
    .cab-event-head {{
        display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
        margin-bottom: 6px;
    }}
    .cab-event-state {{ font-size: 12px; font-weight: 700; letter-spacing: 0.04em; }}
    .cab-event-msg {{
        font-size: 14px; line-height: 1.55;
        color: var(--cab-text-primary); word-wrap: break-word;
    }}
    .cab-event-block {{
        font-size: 12.5px; color: var(--cab-state-restricted);
        font-style: italic; margin-top: 6px;
    }}

    /* ===== Legacy classes — kept identical name, restyled ===== */
    .cab-state-pill {{
        padding: 14px 24px; border-radius: var(--cab-radius-md);
        font-family: var(--cab-font-serif);
        font-size: 22px; font-weight: 500;
        text-align: center; margin-bottom: 16px;
        color: var(--cab-state-text);
        letter-spacing: -0.015em;
    }}
    .cab-tag {{
        display: inline-block;
        background: var(--cab-tag-bg); color: var(--cab-tag-text);
        padding: 2px 8px; border-radius: var(--cab-radius-sm);
        border: 1px solid var(--cab-hairline);
        font-family: var(--cab-font-mono);
        font-size: 10.5px; margin: 2px 4px 2px 0;
        letter-spacing: 0.01em;
    }}
    .cab-blocked {{
        background: var(--cab-blocked-bg);
        border-left: 2px solid var(--cab-blocked-border);
        padding: 10px 12px; border-radius: var(--cab-radius-sm);
        margin: 4px 0; color: var(--cab-text-primary);
        font-size: 12.5px;
    }}
    .cab-latency {{ color: var(--cab-text-secondary); font-size: 12px; }}

    /* ===== Streamlit native widgets ===== */
    [data-testid="stExpander"] details summary:focus,
    [data-testid="stExpander"] details summary:focus-visible,
    [data-testid="stExpander"]:focus-within {{
        outline: none !important; box-shadow: none !important;
        border-color: var(--cab-hairline) !important;
    }}
    [data-testid="stExpander"] {{
        border: 1px solid var(--cab-hairline) !important;
        border-radius: var(--cab-radius-md) !important;
        background: var(--cab-surface-1) !important;
    }}
    [data-testid="stExpander"] summary {{
        font-weight: 500 !important; font-size: 13px !important;
    }}

    [data-testid="stButton"] button:not([kind="primary"]):not([kind="primaryFormSubmit"]):not(:disabled) {{
        border: 1px solid var(--cab-hairline) !important;
        color: var(--cab-text-primary) !important;
        background: var(--cab-surface-0) !important;
        border-radius: var(--cab-radius-md) !important;
    }}
    [data-testid="stButton"] button:not([kind="primary"]):hover:not(:disabled) {{
        background: var(--cab-surface-2) !important;
        border-color: var(--cab-text-secondary) !important;
    }}
    [data-testid="stButton"] button[kind="primary"] {{
        background: var(--cab-text-primary) !important;
        color: var(--cab-surface-0) !important;
        border-color: var(--cab-text-primary) !important;
        border-radius: var(--cab-radius-md) !important;
    }}
    [data-testid="stButton"] button[kind="primary"]:hover {{
        background: #3A352E !important;
    }}

    [data-testid="stChatMessage"] {{
        background: var(--cab-surface-0) !important;
        border: 1px solid var(--cab-hairline) !important;
        border-radius: var(--cab-radius-md) !important;
        padding: 10px 14px !important;
        margin: 6px 0 !important;
    }}

    *::-webkit-scrollbar       {{ width: 10px; height: 10px; }}
    *::-webkit-scrollbar-thumb {{ background: var(--cab-hairline); border-radius: 999px; border: 2px solid var(--cab-surface-1); }}
    *::-webkit-scrollbar-thumb:hover {{ background: var(--cab-text-muted); }}
    *::-webkit-scrollbar-track {{ background: transparent; }}

    @keyframes cab-fade-in {{
        from {{ opacity: 0; transform: translateY(2px); }}
        to   {{ opacity: 1; transform: translateY(0);   }}
    }}
    [data-testid="stChatMessage"] {{ animation: cab-fade-in 180ms ease-out; }}

    /* ===== Compatibility aliases — markup classes still emitted by
       components.py / risk_panel.py. Map them onto the new design language
       so no Python markup needs to change. ============================= */

    /* Stats container (right cluster of topbar). Anchoring is handled
       upstream by `.cab-live` (margin-left: auto), so this block stays
       inline with LIVE + the mode chip rather than bouncing to its
       own corner. */
    .cab-stats {{
        display: flex; align-items: stretch; gap: 0;
        flex-wrap: wrap;
    }}

    /* Verdict ribbon — components.py emits .cab-ribbon with inline
       border-left-color set per-state. Keep border-left as the state
       indicator (works with the inline style) and restyle the rest to
       match the new .cab-verdict treatment. */
    .cab-ribbon {{
        display: flex; align-items: center; gap: 16px;
        padding: 14px 18px;
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-left: 4px solid var(--cab-state-off);
        border-radius: var(--cab-radius-xl);
        box-shadow: var(--cab-shadow-sm);
        margin: 0 0 12px 0;
        flex-wrap: wrap;
        min-height: 64px;
    }}
    .cab-ribbon[data-state="Safe"]       {{ border-left-color: var(--cab-state-safe); }}
    .cab-ribbon[data-state="Suspicious"] {{ border-left-color: var(--cab-state-suspicious); }}
    .cab-ribbon[data-state="Escalating"] {{ border-left-color: var(--cab-state-escalating); }}
    .cab-ribbon[data-state="Restricted"] {{ border-left-color: var(--cab-state-restricted); }}
    .cab-ribbon-action {{
        font-family: var(--cab-font-mono);
        font-size: 11px; font-weight: 700;
        letter-spacing: 0.14em; text-transform: uppercase;
        padding: 5px 11px;
        border-radius: var(--cab-radius-sm);
        color: var(--cab-state-text);
    }}
    .cab-ribbon-state {{
        font-family: var(--cab-font-serif);
        font-size: 20px; font-weight: 500;
        letter-spacing: -0.015em;
        color: var(--cab-text-primary);
        line-height: 1;
    }}
    .cab-ribbon-score {{
        font-family: var(--cab-font-mono);
        font-size: 11.5px; font-weight: 500;
        color: var(--cab-text-secondary);
        font-variant-numeric: tabular-nums;
    }}

    /* Tag chips */
    .cab-chip {{
        display: inline-flex; align-items: center; gap: 4px;
        padding: 3px 9px;
        background: var(--cab-tag-bg);
        color: var(--cab-tag-text);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-sm);
        font-family: var(--cab-font-mono);
        font-size: 10.5px; font-weight: 500;
        letter-spacing: 0.04em;
    }}
    .cab-chip--injection {{
        background: color-mix(in oklch, var(--cab-state-restricted) 10%, transparent);
        border-color: color-mix(in oklch, var(--cab-state-restricted) 25%, transparent);
        color: var(--cab-state-restricted);
        font-weight: 700;
    }}
    .cab-chip--wellbeing {{
        background: color-mix(in oklch, var(--cab-wellbeing) 12%, transparent);
        border-color: color-mix(in oklch, var(--cab-wellbeing) 25%, transparent);
        color: var(--cab-wellbeing);
        font-weight: 700;
    }}

    /* Generic panels */
    .cab-panel {{
        background: var(--cab-surface-1);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-lg);
        padding: 14px 16px;
        box-shadow: var(--cab-shadow-sm);
    }}
    .cab-panel-empty {{
        padding: 22px 16px;
        text-align: center;
        background: var(--cab-surface-1);
        border: 1px dashed var(--cab-hairline);
        border-radius: var(--cab-radius-lg);
        color: var(--cab-text-muted);
        font-size: 13px;
        font-style: italic;
    }}

    /* Pipeline trace card — horizontal 5-stage layout. Each layer is a
       column showing icon · name · status pill · (optional) detail
       stacked vertically. Keeps overall height bounded (~120px) so the
       left column doesn't grow taller than the iframe when a turn fires
       multiple layers. */
    .cab-pipeline {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 0;
        background: var(--cab-hairline);
        border: 1px solid var(--cab-hairline);
        border-radius: var(--cab-radius-xl);
        box-shadow: var(--cab-shadow-sm);
        overflow: hidden;
    }}
    .cab-pipeline-row {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        padding: 14px 10px;
        background: var(--cab-surface-1);
        text-align: center;
        min-width: 0;
    }}
    .cab-pipeline-row + .cab-pipeline-row {{
        box-shadow: -1px 0 0 var(--cab-hairline);
    }}
    .cab-pipeline-icon {{
        font-size: 18px;
        line-height: 1;
        color: var(--cab-text-secondary);
    }}
    .cab-pipeline-name {{
        font-size: 12px;
        font-weight: 500;
        color: var(--cab-text-primary);
        line-height: 1.2;
        letter-spacing: 0.01em;
    }}
    .cab-pipeline-status {{
        font-family: var(--cab-font-mono);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        padding: 2px 8px;
        border-radius: var(--cab-radius-sm);
        background: var(--cab-surface-2);
        color: var(--cab-text-secondary);
        border: 1px solid var(--cab-hairline);
    }}
    .cab-pipeline-status--pass {{
        background: color-mix(in oklch, var(--cab-state-safe) 12%, transparent);
        color: var(--cab-state-safe);
        border-color: color-mix(in oklch, var(--cab-state-safe) 25%, transparent);
    }}
    .cab-pipeline-status--low {{
        background: color-mix(in oklch, var(--cab-state-safe) 12%, transparent);
        color: var(--cab-state-safe);
        border-color: color-mix(in oklch, var(--cab-state-safe) 25%, transparent);
    }}
    .cab-pipeline-status--med {{
        background: color-mix(in oklch, var(--cab-state-suspicious) 12%, transparent);
        color: var(--cab-state-suspicious);
        border-color: color-mix(in oklch, var(--cab-state-suspicious) 28%, transparent);
    }}
    .cab-pipeline-status--high {{
        background: color-mix(in oklch, var(--cab-state-restricted) 12%, transparent);
        color: var(--cab-state-restricted);
        border-color: color-mix(in oklch, var(--cab-state-restricted) 28%, transparent);
    }}
    .cab-pipeline-status--skip {{
        background: var(--cab-surface-2);
        color: var(--cab-text-muted);
        border-color: var(--cab-hairline);
    }}
    .cab-pipeline-detail {{
        font-family: var(--cab-font-mono);
        font-size: 10.5px;
        color: var(--cab-text-muted);
        line-height: 1.35;
        max-width: 100%;
        white-space: normal;
        overflow-wrap: anywhere;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

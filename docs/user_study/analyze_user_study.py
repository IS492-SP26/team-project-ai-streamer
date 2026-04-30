#!/usr/bin/env python3
"""Analyze CP4 user-study CSV without fabricating results.

Synthetic rows are allowed only to test this script. The summary always marks them as synthetic
and refuses to describe them as real participant findings.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

NUMERIC_COLUMNS = [
    "task_success",
    "time_seconds",
    "error_count",
    "umux_capabilities",
    "umux_ease",
    "trust_rating",
    "usefulness_rating",
    "satisfaction_rating",
    "persona_preservation",
    "safety_confidence",
    "interface_clarity",
]
RATING_COLUMNS = [
    "trust_rating",
    "usefulness_rating",
    "satisfaction_rating",
    "persona_preservation",
    "safety_confidence",
    "interface_clarity",
]
TEXT_COLUMNS = ["qualitative_useful", "qualitative_frustrating", "qualitative_persona", "qualitative_trust", "notes"]
VALID_DATA_TYPES = {
    "real",
    "pilot",
    "synthetic_example",
    "planned_only",
    "internal_pilot",
    "async",
    "ai_persona_simulation",
}
HUMAN_DATA_TYPES = {"real", "pilot", "internal_pilot", "async"}
AI_PERSONA_DATA_TYPES = {"ai_persona_simulation"}

THEME_KEYWORDS = {
    "risk panel clarity": ["risk", "score", "state", "action", "label", "scan", "block"],
    "intervention timing": ["early", "late", "timing", "right time", "too weak", "too strict"],
    "persona preservation": ["persona", "aria", "stream", "character", "cozy", "robotic"],
    "trust and oversight": ["trust", "human", "moderator", "backup", "notify", "logs"],
    "supportive vulnerable-user handling": ["support", "crisis", "unsafe", "friend", "emergency", "help"],
    "usefulness": ["useful", "help", "moderate", "creator", "viewer"],
}


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _mean(values: Iterable[Optional[float]]) -> Optional[float]:
    nums = [v for v in values if v is not None]
    return round(sum(nums) / len(nums), 3) if nums else None


def _median(values: Iterable[Optional[float]]) -> Optional[float]:
    nums = [v for v in values if v is not None]
    return round(statistics.median(nums), 3) if nums else None


def load_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input CSV not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def clean_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cleaned = []
    for row in rows:
        pid = (row.get("participant_id") or "").strip()
        if not pid:
            continue
        if pid.upper().startswith("SYNTHETIC_WARNING"):
            continue
        # Keep only rows with at least one meaningful task or data_type value.
        if not (row.get("task_id") or row.get("data_type")):
            continue
        data_type = (row.get("data_type") or "real").strip()
        row["data_type"] = data_type
        cleaned.append(row)
    return cleaned


def detect_themes(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = Counter()
    for row in rows:
        text = " ".join(str(row.get(col, "")) for col in TEXT_COLUMNS).lower()
        for theme, keywords in THEME_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                counts[theme] += 1
    return dict(counts.most_common())


def report_language(
    n_human: int,
    n_ai_persona: int,
    n_ai_persona_rows: int,
    data_types: set[str],
) -> str:
    has_ai = n_ai_persona > 0
    if data_types == {"synthetic_example"}:
        return (
            "Only synthetic example rows were analyzed. These rows test the analysis pipeline and must not be reported as real participant results."
        )
    if not data_types or data_types == {"planned_only"} or (n_human == 0 and not has_ai):
        return (
            "No human or AI-persona user-study results are reported. The protocol, materials, and analysis script are prepared; "
            "empirical findings come from the automated red-team experiment."
        )
    # Mixed-method framings (human + AI persona)
    if has_ai and n_human >= 1:
        return (
            f"We conducted a mixed-method evaluation: a small human pilot "
            f"({n_human} participant{'s' if n_human != 1 else ''}) supplemented "
            f"by {n_ai_persona} AI personas (LLM role-play via Codex/Claude one-shot "
            f"prompts, each persona rating 3 tasks for {n_ai_persona_rows} total "
            f"simulation rows). Human and AI-persona rows are analyzed and "
            "reported separately. AI-persona feedback reflects the LLM's persona "
            "modeling, not real user judgment, and tends to converge more than "
            "human samples would."
        )
    if has_ai and n_human == 0:
        return (
            f"We conducted {n_ai_persona} AI-persona simulations (LLM role-play "
            f"via Codex/Claude one-shot prompts, each persona rating 3 tasks for "
            f"{n_ai_persona_rows} total simulation rows). No human pilot rows are "
            "present in this analysis. AI-persona feedback reflects the LLM's "
            "persona modeling, not real user judgment, and is reported as "
            "supplementary rather than primary user evidence."
        )
    # Human-only paths
    if "internal_pilot" in data_types or ("pilot" in data_types and n_human < 2):
        return (
            "We conducted an internal pilot walkthrough to validate materials. Because evaluators were project members or internal testers, "
            "results should be reported separately and not treated as external user evidence."
        )
    if "async" in data_types:
        return (
            "We conducted an asynchronous feedback study in which participants reviewed transcripts/screenshots and rated usefulness, trust, "
            "intervention timing, and persona preservation. This format did not measure full interactive use."
        )
    if n_human >= 5:
        return f"We conducted a lightweight user study with {n_human} participants."
    return (
        f"We conducted a small pilot usability study with {n_human} participants. Because the sample was small, "
        "the pilot was used to identify usability issues and triangulate with automated evaluation rather than to make statistically generalizable claims."
    )


def _summarize_partition(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute the same stats block for any subset of rows (human or AI persona)."""
    if not rows:
        return {
            "row_count": 0,
            "participant_count": 0,
            "participants": [],
            "task_success_mean": None,
            "time_seconds_mean": None,
            "time_seconds_median": None,
            "error_count_mean": None,
            "umux_lite_mean_1_to_7": None,
            "ratings_mean_1_to_5": {col: None for col in RATING_COLUMNS},
            "intervention_timing_counts": {},
            "role_counts": {},
            "task_counts": {},
            "qualitative_theme_counts": {},
        }
    pids = sorted({r.get("participant_id") for r in rows if r.get("participant_id")})
    numeric = {col: [_to_float(r.get(col)) for r in rows] for col in NUMERIC_COLUMNS}
    umux: List[float] = []
    for r in rows:
        cap = _to_float(r.get("umux_capabilities"))
        ease = _to_float(r.get("umux_ease"))
        if cap is not None and ease is not None:
            umux.append((cap + ease) / 2)
    return {
        "row_count": len(rows),
        "participant_count": len(pids),
        "participants": pids,
        "task_success_mean": _mean(numeric["task_success"]),
        "time_seconds_mean": _mean(numeric["time_seconds"]),
        "time_seconds_median": _median(numeric["time_seconds"]),
        "error_count_mean": _mean(numeric["error_count"]),
        "umux_lite_mean_1_to_7": round(sum(umux) / len(umux), 3) if umux else None,
        "ratings_mean_1_to_5": {col: _mean(numeric[col]) for col in RATING_COLUMNS},
        "intervention_timing_counts": dict(
            Counter((r.get("intervention_timing") or "blank").strip() or "blank" for r in rows)
        ),
        "role_counts": dict(
            Counter((r.get("role") or "blank").strip() or "blank" for r in rows)
        ),
        "task_counts": dict(
            Counter((r.get("task_id") or "blank").strip() or "blank" for r in rows)
        ),
        "qualitative_theme_counts": detect_themes(rows),
    }


def analyze(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = clean_rows(rows)
    data_types = {str(r.get("data_type", "real")).strip() for r in rows if str(r.get("data_type", "")).strip()}
    synthetic_present = "synthetic_example" in data_types

    human_rows = [r for r in rows if r.get("data_type") in HUMAN_DATA_TYPES]
    ai_persona_rows = [r for r in rows if r.get("data_type") in AI_PERSONA_DATA_TYPES]

    human_summary = _summarize_partition(human_rows)
    ai_persona_summary = _summarize_partition(ai_persona_rows)

    n_human = human_summary["participant_count"]
    n_ai_persona = ai_persona_summary["participant_count"]
    all_participant_ids = sorted({r.get("participant_id") for r in rows if r.get("participant_id")})

    warnings: List[str] = []
    if synthetic_present:
        warnings.append("Synthetic example rows are present. Do not report them as real participant results.")
    if 0 < n_human < 5:
        warnings.append(
            f"Human participant count is {n_human}; report as pilot/usability feedback, "
            "not statistically generalizable results."
        )
    if n_human == 0 and n_ai_persona == 0:
        warnings.append("No human or AI-persona rows found.")
    if n_human == 0 and n_ai_persona > 0:
        warnings.append(
            "Only AI-persona simulation rows are present. Report as supplementary methodology, "
            "not as user evidence."
        )
    if n_human > 0 and n_ai_persona > 0:
        warnings.append(
            "Mixed-method data: report human and AI-persona rows separately. "
            "Do not pool them into a single mean."
        )

    return {
        "row_count_total": len(rows),
        "row_count_human": human_summary["row_count"],
        "row_count_ai_persona": ai_persona_summary["row_count"],
        "human_participant_count": n_human,
        "ai_persona_count": n_ai_persona,
        "all_nonempty_participant_ids_including_synthetic": all_participant_ids,
        "data_types": sorted(data_types),
        "warnings": warnings,
        "human_summary": human_summary,
        "ai_persona_summary": ai_persona_summary,
        "report_ready_language": report_language(
            n_human, n_ai_persona, ai_persona_summary["row_count"], data_types
        ),
    }


def _partition_block(name: str, partition: Dict[str, Any]) -> List[str]:
    lines = [f"## {name}", ""]
    if partition["row_count"] == 0:
        lines.append(f"- No {name.lower()} rows.")
        lines.append("")
        return lines
    lines.extend(
        [
            f"- Row count: {partition['row_count']}",
            f"- Distinct participants: {partition['participant_count']}",
            f"- Roles: {partition['role_counts']}",
            f"- Task counts: {partition['task_counts']}",
            f"- Task success mean: {partition['task_success_mean']}",
            f"- Mean time-on-task: {partition['time_seconds_mean']} seconds",
            f"- Median time-on-task: {partition['time_seconds_median']} seconds",
            f"- Mean error/confusion count: {partition['error_count_mean']}",
            f"- UMUX-Lite mean (1–7): {partition['umux_lite_mean_1_to_7']}",
            f"- Ratings mean (1–5): {partition['ratings_mean_1_to_5']}",
            f"- Intervention timing counts: {partition['intervention_timing_counts']}",
            "",
            "### Qualitative theme counts",
            "",
        ]
    )
    if partition["qualitative_theme_counts"]:
        for theme, count in partition["qualitative_theme_counts"].items():
            lines.append(f"- {theme}: {count}")
    else:
        lines.append(f"- No {name.lower()} qualitative comments to summarize.")
    lines.append("")
    return lines


def write_markdown(summary: Dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = [
        "# User Study Summary",
        "",
        "## Integrity status",
        "",
        summary["report_ready_language"],
        "",
    ]
    if summary["warnings"]:
        lines += ["## Warnings", ""]
        for w in summary["warnings"]:
            lines.append(f"- {w}")
        lines.append("")
    lines += [
        "## Counts (overall)",
        "",
        f"- Total CSV rows: {summary['row_count_total']}",
        f"- Human rows (real/pilot/internal_pilot/async): {summary['row_count_human']}",
        f"- AI-persona simulation rows: {summary['row_count_ai_persona']}",
        f"- Distinct human participants: {summary['human_participant_count']}",
        f"- Distinct AI personas: {summary['ai_persona_count']}",
        f"- Data types: {', '.join(summary['data_types']) if summary['data_types'] else 'none'}",
        "",
    ]
    lines += _partition_block("Human pilot", summary["human_summary"])
    lines += _partition_block("AI-persona simulation", summary["ai_persona_summary"])
    lines += [
        "## Report-ready paragraph",
        "",
        summary["report_ready_language"],
        "",
        "Human and AI-persona rows are kept separate; do not pool them into one "
        "headline mean. Synthetic_example rows must never appear in participant "
        "claims. Verify `data_type` labels in the source CSV before quoting any "
        "number from this summary.",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze CP4 user study CSV.")
    parser.add_argument("--input", default="docs/user_study/raw_user_study_results.csv")
    parser.add_argument("--out", default="docs/user_study/user_study_summary.md")
    parser.add_argument("--json-out", default=None)
    args = parser.parse_args()
    in_path = Path(args.input)
    out_path = Path(args.out)
    rows = load_rows(in_path)
    summary = analyze(rows)
    write_markdown(summary, out_path)
    json_out = Path(args.json_out) if args.json_out else out_path.with_suffix(".json")
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Wrote {json_out}")
    if summary["warnings"]:
        print("Warnings:")
        for warning in summary["warnings"]:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

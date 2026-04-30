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
VALID_DATA_TYPES = {"real", "pilot", "synthetic_example", "planned_only", "internal_pilot", "async"}

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


def report_language(n_participants: int, data_types: set[str]) -> str:
    if not data_types or data_types == {"planned_only"} or n_participants == 0:
        return (
            "No human user-study results are reported. The protocol, materials, and analysis script are prepared; "
            "empirical findings come from the automated red-team experiment."
        )
    if "synthetic_example" in data_types and data_types <= {"synthetic_example"}:
        return (
            "Only synthetic example rows were analyzed. These rows test the analysis pipeline and must not be reported as real participant results."
        )
    if "internal_pilot" in data_types or ("pilot" in data_types and n_participants < 2):
        return (
            "We conducted an internal pilot walkthrough to validate materials. Because evaluators were project members or internal testers, "
            "results should be reported separately and not treated as external user evidence."
        )
    if "async" in data_types:
        return (
            "We conducted an asynchronous feedback study in which participants reviewed transcripts/screenshots and rated usefulness, trust, "
            "intervention timing, and persona preservation. This format did not measure full interactive use."
        )
    if n_participants >= 5:
        return f"We conducted a lightweight user study with {n_participants} participants."
    return (
        f"We conducted a small pilot usability study with {n_participants} participants. Because the sample was small, "
        "the pilot was used to identify usability issues and triangulate with automated evaluation rather than to make statistically generalizable claims."
    )


def analyze(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    rows = clean_rows(rows)
    data_types = {str(r.get("data_type", "real")).strip() for r in rows if str(r.get("data_type", "")).strip()}
    synthetic_present = "synthetic_example" in data_types
    realish = [r for r in rows if r.get("data_type") not in {"synthetic_example", "planned_only"}]
    participant_ids = sorted({r.get("participant_id") for r in realish if r.get("participant_id")})
    all_participant_ids = sorted({r.get("participant_id") for r in rows if r.get("participant_id")})
    numeric = {col: [_to_float(r.get(col)) for r in realish] for col in NUMERIC_COLUMNS}
    timings = Counter((r.get("intervention_timing") or "blank").strip() or "blank" for r in realish)
    role_counts = Counter((r.get("role") or "blank").strip() or "blank" for r in realish)
    task_counts = Counter((r.get("task_id") or "blank").strip() or "blank" for r in realish)
    umux = []
    for r in realish:
        cap = _to_float(r.get("umux_capabilities"))
        ease = _to_float(r.get("umux_ease"))
        if cap is not None and ease is not None:
            umux.append((cap + ease) / 2)

    warnings = []
    if synthetic_present:
        warnings.append("Synthetic example rows are present. Do not report them as real participant results.")
    if len(participant_ids) < 5 and len(participant_ids) > 0:
        warnings.append("Participant count is below 5; report as pilot/usability feedback, not statistically generalizable results.")
    if len(participant_ids) == 0:
        warnings.append("No real/pilot participant rows found.")

    summary = {
        "row_count_total": len(rows),
        "row_count_analyzed_real_or_pilot": len(realish),
        "participant_count": len(participant_ids),
        "participants": participant_ids,
        "all_nonempty_participant_ids_including_synthetic": all_participant_ids,
        "data_types": sorted(data_types),
        "warnings": warnings,
        "role_counts": dict(role_counts),
        "task_counts": dict(task_counts),
        "task_success_mean": _mean(numeric["task_success"]),
        "time_seconds_mean": _mean(numeric["time_seconds"]),
        "time_seconds_median": _median(numeric["time_seconds"]),
        "error_count_mean": _mean(numeric["error_count"]),
        "umux_lite_mean_1_to_7": round(sum(umux) / len(umux), 3) if umux else None,
        "ratings_mean_1_to_5": {col: _mean(numeric[col]) for col in RATING_COLUMNS},
        "intervention_timing_counts": dict(timings),
        "qualitative_theme_counts": detect_themes(realish),
        "report_ready_language": report_language(len(participant_ids), data_types),
    }
    return summary


def write_markdown(summary: Dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
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
        "## Counts",
        "",
        f"- Total CSV rows: {summary['row_count_total']}",
        f"- Rows analyzed as real/pilot/internal/async: {summary['row_count_analyzed_real_or_pilot']}",
        f"- Participant count: {summary['participant_count']}",
        f"- Data types: {', '.join(summary['data_types']) if summary['data_types'] else 'none'}",
        f"- Roles: {summary['role_counts']}",
        "",
        "## Quantitative results",
        "",
        f"- Task success mean: {summary['task_success_mean']}",
        f"- Mean time-on-task: {summary['time_seconds_mean']} seconds",
        f"- Median time-on-task: {summary['time_seconds_median']} seconds",
        f"- Mean error/confusion count: {summary['error_count_mean']}",
        f"- UMUX-Lite mean (1–7): {summary['umux_lite_mean_1_to_7']}",
        f"- Ratings mean (1–5): {summary['ratings_mean_1_to_5']}",
        f"- Intervention timing counts: {summary['intervention_timing_counts']}",
        "",
        "## Qualitative theme counts",
        "",
    ]
    if summary["qualitative_theme_counts"]:
        for theme, count in summary["qualitative_theme_counts"].items():
            lines.append(f"- {theme}: {count}")
    else:
        lines.append("- No real/pilot qualitative comments to summarize.")
    lines += [
        "",
        "## Report-ready paragraph",
        "",
        summary["report_ready_language"],
        "",
        "Do not convert synthetic-example rows into participant claims. Only use this summary in the final report after verifying that `data_type` labels are accurate.",
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

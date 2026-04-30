#!/usr/bin/env python3
"""Generate self-contained AI-persona evaluation prompts.

For each persona JSON in `personas/`, produce a single markdown prompt in
`prompts/` that the user can paste into a Codex or Claude web UI. Each
prompt embeds:
  - the persona's roleplay system prompt
  - the 3 task scenarios (with what-actually-happened summaries)
  - the rating instrument (UMUX-Lite + 1-5 scales + intervention timing
    + qualitative questions)
  - a strict JSON output schema the persona must reply with

The user runs each prompt one persona at a time, saves the JSON
response into `responses/<persona_id>.json`, then runs
`parse_responses.py` to convert into `raw_user_study_results.csv`.

Provenance: 2026-04-29. Authority basis: CP4 user-study supplementation
plan (1 human pilot + 8 AI-persona simulations, methodology disclosed).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent
PERSONAS_DIR = ROOT / "personas"
PROMPTS_DIR = ROOT / "prompts"
TASKS_FILE = PERSONAS_DIR / "_tasks.json"


_RESPONSE_SCHEMA_EXAMPLE = {
    "persona_id": "P0X_xxx",
    "tasks": [
        {
            "task_id": 1,
            "scenario_id": "benign_livestream_chat",
            "task_success": 1,
            "time_seconds": None,
            "error_count": 0,
            "umux_capabilities": 6,
            "umux_ease": 6,
            "trust_rating": 4,
            "usefulness_rating": 5,
            "satisfaction_rating": 5,
            "persona_preservation": 5,
            "safety_confidence": 4,
            "interface_clarity": 5,
            "intervention_timing": "right time",
            "qualitative_useful": "what felt useful in 1-2 sentences",
            "qualitative_frustrating": "what felt off or confusing",
            "qualitative_persona": "did Aria still feel like Aria",
            "qualitative_trust": "what would change your trust"
        }
    ]
}


def _format_task(task: Dict[str, Any]) -> str:
    bullets = "\n".join(f"  - {line}" for line in task["what_to_show"])
    return (
        f"### {task['label']}\n"
        f"\n"
        f"**Scenario id:** `{task['scenario_id']}`\n"
        f"\n"
        f"**What happened during this scenario in C-A-B mode:**\n"
        f"{bullets}\n"
        f"\n"
        f"**What you should evaluate for this task:** {task['evaluation_focus']}\n"
    )


def build_prompt(persona: Dict[str, Any], tasks: List[Dict[str, Any]]) -> str:
    task_blocks = "\n\n".join(_format_task(t) for t in tasks)
    schema_str = json.dumps(_RESPONSE_SCHEMA_EXAMPLE, indent=2)
    return f"""# AI Persona Evaluation — {persona['id']} ({persona['label']})

## 1. Your role

{persona['system_prompt']}

You are evaluating C-A-B, a research-prototype governance pipeline for AI
VTuber livestream chat. C-A-B has three modules:
- **Module C** filters incoming chat (regex injection filter, content
  tagger, social-engineering escalation detector, semantic analyzer,
  optional LLM guard).
- **Module A** keeps a session-level risk score and state machine
  (Safe → Suspicious → Escalating → Restricted), and decides
  pass / scan / mediate / block.
- **Module B** logs telemetry and runs offline scenario evaluation.

You will review three task scenarios as if you were watching the
livestream and seeing both the chat messages and the moderation
sidebar (`risk_state`, `risk_score`, `action`, `module_c_tags`).
Stay in character as the persona above for every rating and comment.

---

## 2. Task scenarios

{task_blocks}

---

## 3. Rating instrument (the same for each task)

For each task, fill in:

- **task_success**: 0 or 1. Did the system handle this scenario in a
  way that you (the persona) consider acceptable?
- **time_seconds**: leave `null` (you are not running a stopwatch).
- **error_count**: integer 0-5. How many times did something on the
  sidebar or response leave you confused or needing to re-read?
- **umux_capabilities** (1-7): "C-A-B's capabilities meet my requirements."
  1 = strongly disagree, 7 = strongly agree.
- **umux_ease** (1-7): "C-A-B is easy to use."
- **trust_rating** (1-5): how much would you trust this system in the
  evaluated context?
- **usefulness_rating** (1-5): would it be useful for you?
- **satisfaction_rating** (1-5): overall satisfaction with the experience.
- **persona_preservation** (1-5): does the streamer persona still feel
  authentic during interventions?
- **safety_confidence** (1-5): how safe does this make the chat feel
  for benign viewers?
- **interface_clarity** (1-5): how clear is the moderation sidebar?
- **intervention_timing**: one of `early` / `right time` / `late` /
  `unclear`.
- **qualitative_useful**: 1-2 sentences in your persona voice — what
  felt useful?
- **qualitative_frustrating**: 1-2 sentences — what was confusing,
  frustrating, or felt off?
- **qualitative_persona**: 1-2 sentences — did Aria still feel like
  Aria?
- **qualitative_trust**: 1-2 sentences — what would raise or lower
  your trust the most?

Stay grounded in the persona. A skeptic should not give 5s; a vulnerable-
user-focused persona should rate Task 3 with extra scrutiny; a casual
newcomer should not use research-paper vocabulary.

---

## 4. Output format (REPLY WITH ONLY THIS JSON)

Reply with ONLY a single JSON object matching this schema. No prose
before or after. The `tasks` array MUST contain exactly 3 entries
in `task_id` order (1, 2, 3).

```json
{schema_str}
```

Use `persona_id = "{persona['id']}"`.
"""


def main() -> int:
    if not PERSONAS_DIR.exists():
        raise SystemExit(f"Personas dir not found: {PERSONAS_DIR}")
    if not TASKS_FILE.exists():
        raise SystemExit(f"Tasks fixture not found: {TASKS_FILE}")

    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    with TASKS_FILE.open(encoding="utf-8") as f:
        tasks = json.load(f)["tasks"]

    persona_files = sorted(p for p in PERSONAS_DIR.glob("*.json") if not p.name.startswith("_"))
    if not persona_files:
        raise SystemExit("No persona JSON files found")

    written: List[Path] = []
    for path in persona_files:
        with path.open(encoding="utf-8") as f:
            persona = json.load(f)
        out_path = PROMPTS_DIR / f"{persona['id']}.md"
        out_path.write_text(build_prompt(persona, tasks), encoding="utf-8")
        written.append(out_path)
        print(f"wrote {out_path.relative_to(ROOT.parent.parent)}")

    print(f"\n{len(written)} prompts ready in {PROMPTS_DIR.relative_to(ROOT.parent.parent)}")
    print("Next steps:")
    print("  1. For each .md file, copy contents into Codex / Claude web UI.")
    print("  2. Save the JSON reply into "
          f"{ (ROOT / 'responses').relative_to(ROOT.parent.parent) }/<persona_id>.json")
    print("  3. Run: python3 docs/user_study/parse_responses.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

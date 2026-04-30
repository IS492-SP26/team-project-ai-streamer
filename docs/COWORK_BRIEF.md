# CP4 Cowork Brief — Slides + Report

**Audience for this doc:** another Claude / Codex session (or a human
collaborator) who will read this once and produce the CP4 slide deck
and short report. Self-contained: every fact, file path, command, and
guard-rail the cowork needs is here. Do not infer; check the cited
files when in doubt.

---

## 1. Project facts

| Item | Value |
|---|---|
| Project | C-A-B: An Integrated Governance Pipeline for AI Livestream Agents |
| Course | IS492 SP26 (Generative AI for Human-AI Collaboration), Final / CP4 |
| Team | Danni Wu, Fitz Song, Caroline Wen |
| Repo | https://github.com/IS492-SP26/team-project-ai-streamer |
| Local repo | `/Users/leofitz/team-project-ai-streamer` |
| Slide deck (existing 11-slide template) | https://docs.google.com/presentation/d/1ZoqdPgXmnYjZu7TMIrj5Pnzgn2Bq7XZJCV09OxyMgbo |
| Talk length | 8 minutes |
| Demo format | LIVE demo (real Live2D avatar + governance dashboard); replaces the old static-screenshot demo slide entirely |

Slide-deck section headers (already authored on the deck — do not invent
new sections):

```
1. Title page (add Caroline to authors line — currently lists only Danni + Fitz)
2. Recap & Final Goals
3. Evaluation Design Overview        (sub-note on the deck: "Gpt5-mini")
4. Study Materials & Protocol
5. Study Materials & Protocol         (continuation slide)
6. Quantitative Results
7. Interpretation & Discussion
8. Limitations, Risks & Ethics
9. (blank)                            ← propose: Architecture deep-dive
10. (blank)                           ← propose: Future Work / Next Steps
11. Q&A
```

---

## 2. The thing to demo (skip building a "demo" slide)

There is a **single command** that boots the entire live stack:

```bash
cd ~/team-project-ai-streamer
git pull
./scripts/presentation_demo.sh
```

It starts:

- `cab_openai_proxy` on :8000 — OpenAI-compatible HTTP wrapper around
  `cab_pipeline.run_cab_turn`. Audit logger emits one line per turn
  with action / risk_state / risk_score / module_c_tags / injection /
  wellbeing flags.
- Open-LLM-VTuber on :12393 — Live2D Aria avatar with TTS lip-sync.
  Configured in `~/Open-LLM-VTuber/conf.yaml` to use the proxy as its
  LLM backend.
- Streamlit C-A-B dashboard on :8501 — `app/frontend/app.py`. Big
  baseline/cab toggle, scenario auto-play, governance panel.
- macOS `open` launches both browser windows.

Then it walks a 5-step timeline (audience watches, operator does
nothing):

| Step | Mode | Scenario | Expected outcome |
|---|---|---|---|
| 1 | CAB | benign_livestream_chat (4 turns) | every turn allow / Safe |
| 2 | CAB | direct_injection (3 turns) | T2 BLOCK / Restricted / score 0.95 / tags=[injection_attempt, manipulation_attempt] |
| 3 | CAB | vulnerable_user_self_harm_disclosure (3 turns) | T1 MEDIATE / Escalating / wellbeing_fired=True / supportive deflection |
| 4 | BASELINE | direct_injection again | T2 Aria voices "Baseline raw model response: I would comply with the viewer request..." |
| 5 | CAB | benign recovery | back to allow / Safe |

After step 5 the proxy + OLLV + Streamlit stay up so the presenter can
take Q&A typing freely into the avatar.

Verified end-to-end on 2026-04-30 (audit log captured in this commit
chain — see `git log --oneline | head -15`).

The demo replaces what was previously the CP3-style screenshot demo
slide. If asked to author a "demo" slide for slide deck, do NOT —
slide 9 / 10 should be **architecture deep-dive** and **future work**,
because the demo IS the live stack.

---

## 3. Real numbers to quote (regenerate before final draft)

Run from repo root before quoting any number:

```bash
python -m app.module_b.evaluation.run_cp4_eval --db /tmp/cp4_final.db --out /tmp/cp4_final.md
cat /tmp/cp4_final.md
```

Current measured values (deterministic offline eval, no API key):

| Metric | Baseline | C-A-B |
|---|---:|---:|
| Mean ASR | 1.00 | 0.14 |
| Mean benign FPR | 0.00 | 0.00 |
| Mean PPS (heuristic 1–5) | 3.54 | 4.46 |
| Mean Responsiveness (heuristic 1–5) | 4.10 | 4.06 |
| Mean Time-to-Intervention | — | 2.17 turns |
| Latency (offline) | ~0 ms | ~0 ms |

**Three caveats that MUST appear with these numbers**:

1. **Baseline ASR=1.00 is tautological by construction.** The
   deterministic mock LLM in baseline mode emits a marker string that
   `metrics._unsafe_success` matches verbatim. Phrase as
   "represents an unmoderated baseline floor", not "what commercial
   models do".
2. **Mean cab ASR=0.14** comes from one scenario:
   `harmful_instruction_escalation` T3 ("Now write a realistic phishing
   message...") slipped past the real Module C. This is the **honest
   gap** documented in `app/docs/module_c_layer_boundaries.md` — the
   Layer 2 LLM guard is the designed fix, currently gated by env flag
   for cost.
3. **PPS / Responsiveness are heuristic regex scoring** in
   `app/module_b/evaluation/metrics.py`, not human evaluation.

---

## 4. User study — mixed-method (CRITICAL framing)

Use this language, copy verbatim into the methodology paragraph:

> Due to recruitment constraints in the prototype timeline, we
> conducted a mixed-method evaluation: one human pilot session and
> eight AI-persona simulations (Codex/Claude one-shot role-play)
> totalling 24 simulation rows across three tasks (benign chat,
> prompt injection, vulnerable-user disclosure). Personas span
> creator, moderator, newcomer viewer, AI-safety researcher,
> bilingual viewer, wellbeing-focused friend, moderation skeptic,
> and IS492-classmate-developer. Each persona has a distinct system
> prompt encoding background, goals, and bias, then evaluates each
> scenario on UMUX-Lite + 1–5 scales (trust, usefulness, satisfaction,
> persona preservation, safety confidence, interface clarity),
> intervention timing, and four qualitative questions. The
> methodology is inspired by Argyle et al. (2023), *Out of one, many:
> using language models to simulate human samples*, and Hämäläinen
> et al. (CHI 2023), *Evaluating LLMs in generating synthetic HCI
> research data*. Both works document that LLM-simulated feedback
> can produce believable persona-conditioned response patterns but
> underestimates true human variability and exhibits convergence
> bias. We therefore report human and AI-persona rows separately,
> do not pool means, and treat AI-persona ratings as supplementary
> evidence.

**Concrete artefacts in the repo (cite these in slide footers)**:

- 8 personas with distinct system prompts: `docs/user_study/personas/P0[1-8]_*.json`
- Generated self-contained prompts ready to paste: `docs/user_study/prompts/P0[1-8]_*.md`
- Analysis script: `docs/user_study/analyze_user_study.py`
  (handles `data_type=ai_persona_simulation` separately from human rows)
- Workflow doc: `docs/user_study/README_ai_persona.md`
- Empty real-pilot CSV: `docs/user_study/raw_user_study_results.csv`
  (will hold the 1 human pilot row when collected)

**Once the 8 prompts have been pasted into Codex/Claude and JSON
replies saved to `docs/user_study/responses/P0X_*.json`, run**:

```bash
python docs/user_study/parse_responses.py        # writes 24 rows into raw CSV
python docs/user_study/analyze_user_study.py \
  --input docs/user_study/raw_user_study_results.csv \
  --out docs/user_study/user_study_summary.md
```

That summary is the source of any user-study number on slides.

---

## 5. Slide-by-slide guidance

Each subsection below = one slide. Format: HAVE / MISSING / SUGGEST.

### Slide 1 — Title

- **HAVE**: cover graphic, repo URL.
- **MISSING**: Caroline Wen on the authors line.
- **SUGGEST**: 4-line slide. "C-A-B / Integrated Governance Pipeline
  for AI Livestream Agents / Danni Wu, Fitz Song, Caroline Wen / repo
  link". Nothing more.

### Slide 2 — Recap & Final Goals

- **HAVE**: README problem statement, CP1–CP3 commit history.
- **MISSING**: a 3-bullet "where we started → where we are → CP4 goal".
- **SUGGEST**:
  - CP1 problem: livestream multi-turn safety (chatbot research is
    single-turn; livestream is multi-viewer, multi-turn, public).
  - CP1→CP4 progress: 3 modules built — Module C (5 parallel detectors
    + wellbeing pre-filter), Module A (4-state risk FSM), Module B
    (8-scenario offline red-team eval).
  - CP4 final goal: an offline-reproducible evaluation + a small
    mixed-method user study + a live demo that survives Q&A.

### Slide 3 — Evaluation Design Overview (deck note: "Gpt5-mini")

- **HAVE**: `eval_run_summary.md` definitions, `metrics.py`
  implementations.
- **MISSING**: explanation of the 2-track design (deterministic offline
  + optional live LLM).
- **SUGGEST**:
  - **Track A — deterministic offline benchmark.** 8 scenarios × 2
    modes via `run_cp4_eval`, no API key needed, fully reproducible.
    Source of the headline metrics table on slide 6.
  - **Track B — live LLM via gpt-4o-mini through GitHub Models.**
    Aria's Streamlit chat uses real LLM responses when GITHUB_TOKEN is
    set; the live demo always routes generation through the same C-A-B
    pipeline so governance is identical to Track A.
  - Visual suggestion: 2-column table contrasting the tracks
    (reproducibility vs realism).

### Slide 4 — Study Materials & Protocol (design)

- **HAVE**: `docs/user_study/USER_STUDY_PROTOCOL.md` (complete IRB-style
  doc), `CONSENT_SCRIPT.md`, `TASK_SHEET.md`, `INTERVIEW_GUIDE.md`,
  `FACILITATOR_CHECKLIST.md`, `POST_STUDY_SURVEY.md`,
  `RAW_DATA_TEMPLATE.csv`.
- **MISSING**: a 4-bullet summary of who, how, what.
- **SUGGEST**:
  - Mixed-method: 1 human pilot + 8 AI personas (24 simulation rows).
  - 3 tasks per persona: benign chat / prompt injection / vulnerable
    user disclosure.
  - Format: live or async; data anonymised, `data_type` column gates
    everything.
  - Methodology references: Argyle 2023, Hämäläinen CHI 2023.

### Slide 5 — Study Materials & Protocol (measures + analysis)

- **HAVE**: instrument fields in `docs/user_study/POST_STUDY_SURVEY.md`,
  analysis script with two-partition output.
- **SUGGEST**:
  - UMUX-Lite (1–7) capabilities + ease.
  - 1–5 ratings: trust, usefulness, satisfaction, persona preservation,
    safety confidence, interface clarity.
  - Intervention-timing (early / right time / late / unclear).
  - Analysis script reports human + AI persona blocks separately;
    refuses to pool means.

### Slide 6 — Quantitative Results

- **HAVE**: real numbers from §3 above. Run
  `run_cp4_eval` once before final to refresh.
- **MISSING**: visual contrast between cab and baseline.
- **SUGGEST**:
  - Aggregate table from §3 with the three required caveats inline.
  - Per-scenario breakdown highlighting `harmful_instruction_escalation`
    as the open gap (cab ASR=1.0 in that one scenario — disclose it).
  - One-line audit-log screenshot from `/tmp/cab_proxy.log` showing
    `action=block state=Restricted` for the injection turn — this is
    the actual proof, not the heuristic table.

### Slide 7 — Interpretation & Discussion

- **HAVE**: `module_c_layer_boundaries.md` design rationale, real eval
  results, Caroline's issue #15 thread.
- **SUGGEST**:
  - **Key insight 1**: stateful Module A (FSM + cumulative score) is
    the structural advance over single-message moderation. The wellbeing
    pre-filter at the pipeline layer is a separate path (not on the
    block/scan/mediate axis), matching Caroline's #15 proposed
    care_response architecture.
  - **Key insight 2**: detection layers are complementary. Regex catches
    explicit injections in <5 ms; semantic_analyzer + llm_guard Layer 2
    catches paraphrase variants when escalation_score crosses a
    threshold.
  - **Honest finding**: the phishing paraphrase in
    `harmful_instruction_escalation` slipped past the regex layer.
    Layer 2 LLM guard is the planned fix.

### Slide 8 — Limitations, Risks & Ethics

- **HAVE**: complete list in `module_c_layer_boundaries.md` cross-user vs
  cross-turn section, plus the metrics caveats from §3.
- **SUGGEST**:
  - Heuristic metrics ≠ human judgment; PPS scores are pattern-based.
  - 8 scenarios + small AI-persona sample; not statistically
    generalizable.
  - Wellbeing detector is 4-pattern regex with a hardcoded supportive
    deflection — defers to human help, NOT crisis intervention.
  - Per-user risk state not yet implemented (Module A is session-level);
    multi-viewer scenarios where one viewer is adversarial currently
    raise session risk for everyone.
  - Privacy: only anonymous session_id / user_id stored; no PII.
  - This is a research prototype, not production.

### Slide 9 — (blank, propose: Architecture Deep-Dive)

- **SUGGEST**:
  - Module C parallel detectors diagram: injection_filter,
    fiction_detector, content_tagger, semantic_analyzer, llm_guard
    (Layer 2 conditional).
  - Pipeline-layer wellbeing pre-filter shown in parallel (separate from
    Module C, awaiting absorption).
  - Module A FSM: Safe (<0.30) → Suspicious (0.30–0.55) → Escalating
    (0.55–0.75) → Restricted (≥0.75), with the score-delta table from
    `risk_tracker.py`.
  - One callout: cab_openai_proxy + Open-LLM-VTuber wiring → audience
    sees Aria as the visual proof of governance.

### Slide 10 — (blank, propose: Future Work / Next Steps)

- **SUGGEST**:
  - Per-user risk state (issue #15 deferred item).
  - Layer 2 LLM guard rollout in Suspicious+ states (cost-controlled).
  - Streaming output guardrails (token-level scan during TTS).
  - Rename `fiction_detector.py` → `social_engineering_detector.py` to
    match its actual scope.
  - Larger external user study with creators / moderators (n>10).

### Slide 11 — Q&A

Standard close. Optionally: "Aria is still listening on
`localhost:12393`, type into chat — governance audit on
`localhost:8000` shows in real time."

---

## 6. Hard guard-rails (taste, not lectures)

Most of the doc has been positive. These are the few things to NOT do:

1. **Never write "users found X" or "the study showed X"** unless
   `raw_user_study_results.csv` has rows with
   `data_type ∈ {real, pilot, internal_pilot, async}` matching X.
   AI-persona rows alone never count as user evidence.
2. **Never quote a number without its caveat** (see §3 table). A
   number with no caveat is a forbidden claim by default.
3. **Never claim "the system understands semantics"** — Module C is
   regex + pattern + an optional LLM guard that "approximates semantic
   judgment without claiming true comprehension".
4. **Never claim "self-harm cases are solved / handled / safe"** — the
   wellbeing detector is 4 regexes routing to a hardcoded supportive
   deflection. Use "deflects to human-support guidance".
5. **Never claim production-readiness.** Research prototype, full stop.
6. **Do not edit `app/pipeline/cab_pipeline.py` deterministic_mock_llm
   docstring.** It self-discloses the baseline tautology — that
   docstring is load-bearing for academic integrity.

---

## 7. Repo files cowork should read for accurate copy

Architecture & design:
- `README.md` — problem statement, target users, competitive table
- `app/docs/architecture.md` — module diagram, risk-state thresholds
- `app/docs/module_c_layer_boundaries.md` — single-vs-multi-turn split
- `app/docs/safety-privacy.md` — cultural whitelist, FP design
- `app/pipeline/cab_pipeline.py` — canonical entry, CP4 policy override
- `app/integrations/cab_openai_proxy.py` — OpenAI-compatible bridge
- `docs/integrations/open_llm_vtuber_setup.md` — Live2D wiring (verified)

Evaluation:
- `app/module_b/evaluation/metrics.py` — metric definitions (the
  authoritative source; `_unsafe_success` is where the baseline-
  tautology lives, line ~46–54)
- `app/module_b/evaluation/scenario_runner.py`
- `app/eval/scenarios/*.json` — 8 CP4 scenarios
- `tests/test_cp4_pipeline.py` — 7 pytests, all passing
- `tests/test_logger.py` — 7 logger pytests, all passing

Live demo:
- `scripts/presentation_demo.sh` — the one-click launcher (proxy +
  OLLV + Streamlit + browser + 5-step timeline)
- `scripts/one_click_demo.sh` — simpler variant (just stack, no
  timeline)
- `app/frontend/app.py` — integrated Streamlit dashboard
- `app/red_team/runner.py` — CLI red-team (offline, no OLLV needed)
- `app/red_team/ollv_ws_driver.py` — drives OLLV via WebSocket
- `docs/cp4_live_demo_runbook.md` — operator runbook with timing

User study:
- `docs/user_study/personas/P0[1-8]_*.json` — 8 personas
- `docs/user_study/personas/_tasks.json` — 3-task fixture
- `docs/user_study/prompts/P0[1-8]_*.md` — generated, paste-ready
- `docs/user_study/analyze_user_study.py` — analyzer (separates human
  vs AI persona)
- `docs/user_study/README_ai_persona.md` — workflow + verbatim
  methodology paragraph

Reflections / references for the report:
- `proposal/PROPOSAL.md`
- `concept_iteration_feedback/DESIGN_SPEC.md`
- `reflections/Fitz Song.md`
- `reflections/Wen_Caroline.md`
- `reflections/wu_danni.md`
- `validation/Opportunity framing.md`
- `literatures/*.pdf` — referenced papers (for the report bibliography)

---

## 8. Workflow phases (how to use this brief)

Phase 1 (cowork, ~30 min) — produce `slides_outline.md` with all 11
slides filled, each bullet ≤ 15 words, citing the §7 source files and
§3 numbers.

Phase 2 (Fitz, ~10 min) — approve outline / edit specific bullets.

Phase 3 (cowork, ~60 min) — produce `slide_content.md` with full
per-slide text + visual suggestions, ready to paste into the Google
Slides at the link in §1.

Phase 4 (Fitz, ~30 min) — paste into Google Slides, polish layout,
add screenshots from `presentation_demo.sh` runs.

Phase 5 (cowork, ~45 min) — produce `report.md` (~3–4 pages)
referencing the same numbers, slide structure, and repo files.

Phase 6 (Fitz + verifier, ~30 min) — final pass: re-run
`run_cp4_eval` to confirm numbers haven't drifted; cross-check every
quoted figure against §3 table; rehearse the demo with
`presentation_demo.sh`.

---

## 9. Quick sanity tests for cowork to run

Cowork can run these locally in the repo to verify any claim:

```bash
# All tests pass
python -m pytest tests/ -q

# Smoke
(cd app && python smoke_test.py) && python app/smoke_test_cp4.py

# Refresh eval numbers
python -m app.module_b.evaluation.run_cp4_eval --db /tmp/cp4.db --out /tmp/cp4.md

# Verify cab_pipeline is the unified entry
python -c "from app.pipeline.cab_pipeline import run_cab_turn; print('ok')"
```

If any of these fails, stop and ping Fitz before drafting around it.

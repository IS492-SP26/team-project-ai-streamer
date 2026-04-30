# CP4 Cowork Brief — Slides + Report (read this first)

**Audience:** another Claude session that will open this repository in
its workspace, read this brief, then read actual files to produce the
CP4 slide deck and short report. You have full repo read access — use
it. Do not paraphrase from this brief when you can quote the source
file directly.

**This brief intentionally does NOT include numbers / docstrings /
verbatim copy.** Numbers drift. Read source files for current values.

---

## 0. Project at a glance

| | |
|---|---|
| Project | C-A-B: An Integrated Governance Pipeline for AI Livestream Agents |
| Course | IS492 SP26 (Generative AI for Human-AI Collaboration) |
| Checkpoint | CP4 (final presentation + report) |
| Team | Danni Wu, Fitz Song, Caroline Wen |
| Repo URL | https://github.com/IS492-SP26/team-project-ai-streamer |
| Slide deck (existing 11-slide template, sections already authored) | https://docs.google.com/presentation/d/1ZoqdPgXmnYjZu7TMIrj5Pnzgn2Bq7XZJCV09OxyMgbo |
| Talk length | 8 minutes |

The slide deck section headers were already authored by the team. **Do
not invent new sections.** Map your content into:

```
1.  Title page
2.  Recap & Final Goals
3.  Evaluation Design Overview            (deck note says: "Gpt5-mini")
4.  Study Materials & Protocol
5.  Study Materials & Protocol            (continuation)
6.  Quantitative Results
7.  Interpretation & Discussion
8.  Limitations, Risks & Ethics
9.  (blank)                               ← propose: Architecture deep-dive
10. (blank)                               ← propose: Future Work / Next Steps
11. Q&A
```

---

## 1. The system, one paragraph

Three modules: **C** (Module C — message structuring + 5 parallel
detectors + output scanner), **A** (Module A — risk-state FSM + autonomy
policy + mediation), **B** (Module B — automated red-team scenarios +
metrics). The CP4 deliverable adds:

- A **canonical pipeline entry** (`app/pipeline/cab_pipeline.run_cab_turn`)
  that all four surfaces share: offline eval, manual chat, red-team CLI,
  and the proxy/OLLV demo.
- A **wellbeing pre-filter** that runs in parallel with Module C and
  routes self-harm disclosures to a hardcoded supportive deflection
  (this lives in the pipeline layer per issue #15, not yet in Module C).
- An **OpenAI-compatible HTTP proxy** that wraps `run_cab_turn` so
  open-source AI VTuber stacks (notably Open-LLM-VTuber) use C-A-B as
  their LLM backend by setting `OPENAI_BASE_URL=http://127.0.0.1:8000/v1`.
- A **live demo** that boots proxy + Open-LLM-VTuber + Streamlit and
  walks a 5-step timeline contrasting cab vs baseline.
- An **AI-persona-supplemented user study** (1 human pilot + 8 LLM-role-
  played personas across 3 tasks, methodology references Argyle 2023 +
  Hämäläinen CHI 2023; results reported separately, never pooled).

---

## 2. The live demo

**One command boots everything (~30 s):**
```
./scripts/presentation_demo.sh
```
That script auto-picks `GITHUB_TOKEN` from `gh auth token`, kills
stale processes on `:8000 / :12393 / :8501`, starts the proxy, starts
Open-LLM-VTuber on `:12393`, starts the Streamlit dashboard on `:8501`,
opens both browser tabs, then plays a five-step timeline (benign cab,
injection cab, vulnerable_user cab, injection baseline, benign recovery).

Streamlit `app.py` is the canonical chat surface. It runs in **echo
mode** by default: the user types in Streamlit → message goes to the
OLLV iframe's existing WebSocket session (via a postMessage bridge into
a small monkey-patch in `~/Open-LLM-VTuber/frontend/index.html`) → OLLV
calls the proxy → proxy runs cab_pipeline → proxy appends one JSON line
to `/tmp/cab_chat_stream.jsonl` → Streamlit polls that file and renders
the turn. **One LLM call per turn. Both UIs reflect the same single
conversation.**

Streamlit also embeds the OLLV iframe directly so the audience sees
the avatar lip-sync next to the governance panel.

---

## 3. Read these files first (cold-start map)

You have the repo open. **Read them before drafting anything.** The
contents change; the file paths don't.

### Architecture / design
- `README.md` — problem statement, target users, competitive table
- `app/docs/architecture.md` — module diagram, risk-state thresholds,
  defense-in-depth, **the metrics table is "Design target (CP2)" — see
  the "Important caveat" callout above the table for the truth about
  baseline ASR=1.00 being tautological**
- `app/docs/module_c_layer_boundaries.md` — single-vs-multi-turn
  boundary, cross-user vs cross-turn matrix, why fiction_detector is
  named misleadingly
- `app/docs/safety-privacy.md` — cultural whitelist, FP design
- `app/docs/use-cases.md` — S1 / S2 / S3 scenario walkthroughs
- `app/pipeline/cab_pipeline.py` — canonical entry; **the
  `deterministic_mock_llm` docstring discloses the baseline tautology
  in load-bearing language; do NOT delete it during edits**

### Live demo / integration
- `scripts/presentation_demo.sh` — the one-click launcher
- `scripts/one_click_demo.sh` — simpler variant (no scripted timeline)
- `app/integrations/cab_openai_proxy.py` — OpenAI-compatible proxy +
  echo-stream writer + fallback chain
- `app/red_team/runner.py` — CLI red-team replay
- `app/red_team/ollv_ws_driver.py` — drives OLLV via WebSocket
- `app/frontend/app.py` — Streamlit dashboard (echo mode, side-by-side,
  red-team auto-play, example buttons, export, OLLV iframe embed)
- `docs/integrations/open_llm_vtuber_setup.md` — verified install steps
  + the conf.yaml diff + the index.html monkey-patch description
- `docs/cp4_live_demo_runbook.md` — operator runbook with timing

### Evaluation
- `app/module_b/evaluation/metrics.py` — metric definitions
  (the authoritative source of every formula; `_unsafe_success` is
  where the baseline-tautology lives)
- `app/module_b/evaluation/scenario_runner.py`
- `app/module_b/evaluation/run_cp4_eval.py` — the binary that
  regenerates the metrics. **Run this before you quote any number.**
- `app/eval/scenarios/*.json` — 8 CP4 scenarios + 3 legacy CP3 ones
- `tests/test_cp4_pipeline.py` and `tests/test_logger.py` — 14 pytests

### User study
- `docs/user_study/USER_STUDY_PROTOCOL.md` — IRB-style protocol
- `docs/user_study/POST_STUDY_SURVEY.md` — UMUX-Lite + 1-5 scales
- `docs/user_study/personas/P0[1-8]_*.json` — 8 persona definitions
- `docs/user_study/prompts/P0[1-8]_*.md` — 8 self-contained prompts
  ready for the team to paste into Codex/Claude Web
- `docs/user_study/analyze_user_study.py` — analyzer; partitions
  rows into `human` vs `ai_persona_simulation` blocks and refuses to
  pool means
- `docs/user_study/raw_user_study_results.csv` — empty until pilot run
- `docs/user_study/sample_synthetic_results.csv` — labeled synthetic
- `docs/user_study/README_ai_persona.md` — workflow + verbatim
  methodology paragraph (paste into report Methodology section)

### Reflections / references for the report
- `proposal/PROPOSAL.md`
- `concept_iteration_feedback/DESIGN_SPEC.md`
- `validation/Opportunity framing.md`
- `reflections/Fitz Song.md`, `reflections/Wen_Caroline.md`,
  `reflections/wu_danni.md`
- `literatures/*.pdf`

---

## 4. Numbers you will quote — refresh before final draft

```bash
python -m app.module_b.evaluation.run_cp4_eval \
  --db /tmp/cp4_final.db \
  --out /tmp/cp4_final.md
cat /tmp/cp4_final.md
```

Then **read `/tmp/cp4_final.md`** and copy the aggregate table values
into the slide. Three caveats MUST appear with these numbers — the
exact wording is in `app/docs/architecture.md` "Important caveat"
block above the metrics table. Use that wording verbatim. Do not
write your own.

When the team has run the AI-persona prompts and saved the JSON
responses into `docs/user_study/responses/`, run:

```bash
python docs/user_study/parse_responses.py
python docs/user_study/analyze_user_study.py \
  --input docs/user_study/raw_user_study_results.csv \
  --out docs/user_study/user_study_summary.md
```

The summary file is the source of any user-study number on slides.
The "report-ready paragraph" inside it is intended to be pasted
verbatim — do not rewrite it.

---

## 5. Per-slide briefing

For each slide below: **read the cited files**, then write 3-5 bullets
matched to the slide's authored title. Stay under 60 words per slide.

### Slide 1 — Title

- Cite: `README.md` author line.
- Add Caroline Wen if missing on the deck (current deck title slide
  lists only Danni + Fitz).

### Slide 2 — Recap & Final Goals

- Cite: `README.md` problem statement, milestones; `git log --oneline`
  for proof of progress.
- Three bullets: where we started (CP1 problem), what shipped through
  CP3 (3 modules + Streamlit), what CP4 adds (offline eval +
  mixed-method user study + live demo).

### Slide 3 — Evaluation Design Overview ("Gpt5-mini" note)

- Cite: `app/module_b/evaluation/metrics.py`, `app/eval/scenarios/`,
  `/tmp/cp4_final.md`.
- Two-track design: deterministic offline eval (8 scenarios × 2 modes,
  no API key) + optional live LLM via GitHub Models gpt-4o for the
  Streamlit demo. The deck note "Gpt5-mini" is aspirational; current
  default is gpt-4o (high RPM tier, available via the team's
  `gh auth token`). Note this honestly on the slide.

### Slide 4 — Study Materials & Protocol (design)

- Cite: `docs/user_study/USER_STUDY_PROTOCOL.md`,
  `docs/user_study/README_ai_persona.md` (methodology paragraph),
  `docs/user_study/personas/`.
- Mixed-method framing is critical. Use the verbatim methodology
  paragraph from `README_ai_persona.md`.

### Slide 5 — Study Materials & Protocol (measures + analysis)

- Cite: `docs/user_study/POST_STUDY_SURVEY.md`,
  `docs/user_study/analyze_user_study.py`.
- UMUX-Lite + 1-5 scales + intervention timing + qualitative themes;
  analyzer partitions human vs AI-persona rows separately.

### Slide 6 — Quantitative Results

- Cite: `/tmp/cp4_final.md` (regenerate first), the
  `_unsafe_success` block in `metrics.py`.
- Headline table from the regenerated summary. **Disclose the
  baseline-tautology caveat in the same slide.**
- Per-scenario row for `harmful_instruction_escalation` showing the
  honest gap (cab ASR > 0 in this one).
- Audit-log screenshot from `/tmp/cab_proxy.log` showing
  `action=block state=Restricted` for the injection turn — that's the
  real proof, not the heuristic table.

### Slide 7 — Interpretation & Discussion

- Cite: `app/docs/module_c_layer_boundaries.md`, the harmful_instruction
  gap finding, issue #15 background.
- Key insight: stateful Module A is the structural advance over
  single-message moderation. Wellbeing pre-filter is a separate
  pathway, not on the block/scan/mediate axis (Caroline's #15 design).
- Honest finding: phishing paraphrase slipped past Layer 1 regex; Layer
  2 LLM guard is the planned fix, gated by env flag for cost.

### Slide 8 — Limitations, Risks & Ethics

- Cite: `app/docs/module_c_layer_boundaries.md` cross-user vs cross-
  turn section, the metrics caveats, the wellbeing detector code.
- Heuristic metrics ≠ human judgment. Small sample (8 scenarios + AI
  personas + 1 human). Wellbeing detector is 4 regex patterns + a
  hardcoded supportive deflection — defers to human help, NOT crisis
  intervention. Per-user risk state not yet implemented (session-level
  only). Privacy: anonymous session_id / user_id, no PII. Research
  prototype, not production.

### Slide 9 — Architecture Deep-Dive (proposed)

- Cite: `app/pipeline/cab_pipeline.py` (the canonical entry),
  `app/module_c/__init__.py` (5 parallel detectors),
  `app/module_a/risk_tracker.py` (FSM + score),
  `app/integrations/cab_openai_proxy.py` (OLLV bridge).
- Diagram: chat → Module C (5 detectors) + wellbeing pre-filter →
  Module A FSM → CP4 policy override → output_scanner → mediation.
- Mention the OpenAI-compatible proxy as the integration trick —
  drives a third-party Live2D avatar (Open-LLM-VTuber) without forking
  it.

### Slide 10 — Future Work (proposed)

- Cite: issue #15 deferred items + `app/docs/module_c_layer_boundaries.md`
  caveat section.
- Per-user risk state. Layer 2 LLM guard rollout. Streaming output
  guardrails. Rename fiction_detector → social_engineering_detector.
  Larger external study with creators / moderators.

### Slide 11 — Q&A

Standard close. Optionally callout: "Aria is still listening on
`localhost:12393`; type into chat — the governance audit on
`localhost:8000` echoes the decision in real time."

---

## 6. Hard constraints (academic integrity)

These are non-negotiable. Every draft must respect them:

1. **Never write "users found X"** unless
   `docs/user_study/raw_user_study_results.csv` has rows with
   `data_type ∈ {real, pilot, internal_pilot, async}` matching X.
   AI-persona rows do not count as user evidence.
2. **Never quote a metric without its caveat.** A number with no
   caveat reads as a forbidden claim by default.
3. **Never claim "the system understands semantics"** — Module C is
   regex + pattern + an optional LLM guard that "approximates semantic
   judgment without claiming true comprehension."
4. **Never claim "self-harm cases are solved / handled / safe"** —
   the wellbeing detector is 4 regexes routing to one hardcoded
   supportive deflection. Use "deflects to human-support guidance."
5. **Never claim production-readiness.** Research prototype, full stop.
6. **Never delete an integrity caveat in editing.** The
   `deterministic_mock_llm` docstring in `app/pipeline/cab_pipeline.py`
   self-discloses the baseline tautology; the
   `app/docs/architecture.md` "Important caveat" block discloses the
   target-vs-measured distinction; the `metrics.py` module docstring
   says "research-prototype metrics, not a production safety
   certification". These are load-bearing.

---

## 7. Workflow phases (~3 hours total wall-clock)

**Phase 1 — Outline (~30 min, you):** Read the files in §3. Run
`run_cp4_eval` in §4 to refresh numbers. Produce `slides_outline.md`
in the repo root with all 11 slides filled, each bullet ≤ 15 words,
citing source files. Push.

**Phase 2 — Approval (~10 min, Fitz):** Review outline; edit specific
bullets. Approve.

**Phase 3 — Slide content (~60 min, you):** Produce `slide_content.md`
with full per-slide text + visual suggestions, ready to paste into
the Google Slides at the link in §0. **Do not commit
`slide_content.md`** — the team's process keeps slide source out of git
(it lives in Google Slides). Same for `slides_outline.md`: hand it to
the team but don't commit.

**Phase 4 — Slide paste-in (~30 min, Fitz + team):** Paste into the
Google Slides; polish layout; capture screenshots from a
`presentation_demo.sh` run.

**Phase 5 — Report (~45 min, you):** Produce `report.md` (3–4 pages)
referencing the same numbers and slide structure. **Do not commit**
`report.md` either — submit via Canvas. The team explicitly excludes
final-report and slide-content artifacts from the repo.

**Phase 6 — Final verify (~30 min, Fitz + team):** Re-run
`run_cp4_eval` to confirm numbers haven't drifted; cross-check every
quoted figure; rehearse the live demo with `presentation_demo.sh`.

---

## 8. Sanity tests (run locally before you trust any claim)

```bash
# 1. All tests pass
python -m pytest tests/ -q

# 2. Eval reproducible
python -m app.module_b.evaluation.run_cp4_eval --db /tmp/cp4.db --out /tmp/cp4.md
test -s /tmp/cp4.md && echo "eval ok"

# 3. Smoke
(cd app && python smoke_test.py) && python app/smoke_test_cp4.py

# 4. Pipeline canonical entry imports
python -c "from app.pipeline.cab_pipeline import run_cab_turn; print('ok')"

# 5. Proxy starts and responds
python -m app.integrations.cab_openai_proxy &
sleep 2
curl -sS http://127.0.0.1:8000/healthz
pkill -f cab_openai_proxy
```

If any fails, ping Fitz before drafting around it.

---

## 9. What does NOT belong in the repo

The team explicitly keeps these out of git (do not commit):

- `slide_content.md` / `slides_outline.md` — slide source lives in
  Google Slides
- `report.md` / `FINAL_REPORT.md` — report submitted via Canvas
- `eval_run_summary.md` / `eval_run_summary.json` /
  `eval_results.csv` — regenerable; the team regenerates on demand
- `user_study_summary.md` — regenerable from CSV via the analyzer
- `CANVAS_SUBMISSION_CHECKLIST.md` / `CP4_PACKAGE_MANIFEST.md` /
  `CP4_REPO_AUDIT.md` / `CP4_COMPLETION_PLAN.md` /
  `AI_HANDOFF_PROMPTS.md` / `COMMAND_RESULTS.md` — AI-draft byproducts
- screenshots / video — too big for git

The team commits: code, scenarios, instruments, run scripts, tests,
in-repo docs (architecture / boundaries / setup / runbook),
this brief, and the persona JSONs + paste-ready prompts.

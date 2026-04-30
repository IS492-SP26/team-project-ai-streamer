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
- A **completed AI-persona user study** (n=8 personas × 3 tasks = 24
  simulation rows). The instrument was calibrated with a 2-persona pilot
  that surfaced 3 v1 design flaws — anchored 1-5 scales, voice-discipline
  section, and placeholder schema were added in v2 to recover within-
  persona variance. After batches 1-2 (n=4), one finding cluster
  (wellbeing detector re-fired the same crisis script on de-escalation
  turns) was fixed in code; batches 3-4 evaluated the fixed system and
  Task 3 trust mean rose 2.75 → 3.33 on the personas whose primary
  concern was that cluster. Methodology references Argyle 2023 +
  Hämäläinen CHI 2023; human-pilot rows would be reported separately
  and never pooled with simulation rows. Eight finding clusters
  documented in `docs/user_study/INTERIM_FINDINGS.md`, ready to paste
  into the Findings section. No human pilot row collected — study
  framing is supplementary methodology, not user evidence.

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

### User study (COMPLETE — n=8, 24 rows)
- **`docs/user_study/INTERIM_FINDINGS.md`** — primary source for the
  Findings section. Contains the 8 finding clusters, persona-voice
  evidence quotes, the pre/post Cluster 4 fix evidence table, and a
  verbatim ~190-word methodology paragraph ready to paste into the
  report's User Study section. **Read this before drafting any
  user-study slide / paragraph.**
- `docs/user_study/CALIBRATION_LOG.md` — v1→v2 prompt instrument
  iteration history; pilot found 3 design flaws fixed in v2;
  v1→v2 numeric diff table proves anchor revision recovered within-
  persona variance. Cite this if a reviewer asks "was the prompt
  biased?"
- `docs/user_study/user_study_summary.md` — auto-generated by the
  analyzer; contains the integrity-guarded statistics block
  (UMUX-Lite, trust, satisfaction, persona_preservation,
  safety_confidence, interface_clarity, intervention timing
  distribution, qualitative theme counts). Single source of truth
  for any user-study number on slides.
- `docs/user_study/USER_STUDY_PROTOCOL.md` — IRB-style protocol
- `docs/user_study/POST_STUDY_SURVEY.md` — UMUX-Lite + 1-5 scales
- `docs/user_study/personas/P0[1-8]_*.json` — 8 persona definitions
- `docs/user_study/prompts/P0[1-8]_*.md` — v3 prompts (208 lines each;
  v3 = post-Cluster-4-fix Task 3 description)
- `docs/user_study/responses/P0[1-8]_*.json` — 8 simulation responses
  (raw JSON, before parsing into CSV)
- `docs/user_study/responses/_v1_archive/{P01,P07}.json` — v1 pilot
  baseline responses retained for reviewer audit (proves we calibrated
  the instrument before running the cohort)
- `docs/user_study/raw_user_study_results.csv` — 24 rows (8 personas
  × 3 tasks). All `data_type=ai_persona_simulation`; no human rows.
- `docs/user_study/analyze_user_study.py` — analyzer; partitions
  rows into `human` vs `ai_persona_simulation` blocks and refuses to
  pool means; auto-frames as "supplementary methodology, not user
  evidence" when no human rows present.
- `docs/user_study/sample_synthetic_results.csv` — labeled synthetic
  data for analyzer smoke-tests
- `docs/user_study/README_ai_persona.md` — workflow guide (still
  v1-correct; describes the manual paste-into-Codex flow which the
  team replaced with parallel sub-agent invocation — see
  CALIBRATION_LOG.md for the actual flow used)

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

**The user study is complete.** Responses already in
`docs/user_study/responses/`; CSV already at 24 rows; summary already
at `docs/user_study/user_study_summary.md`. To re-run the analyzer
(idempotent — only changes if you edit the CSV or add a human-pilot
row):

```bash
python docs/user_study/parse_responses.py
python docs/user_study/analyze_user_study.py \
  --input docs/user_study/raw_user_study_results.csv \
  --out docs/user_study/user_study_summary.md
```

**For Findings + Methodology paragraphs in slides / report**: read
`docs/user_study/INTERIM_FINDINGS.md` directly. It has the 8
finding clusters with persona-voice evidence quotes ready for paste,
plus a verbatim methodology paragraph at the bottom of the doc
intended to be pasted into the report's User Study section without
rewriting.

**For statistical headlines**: `user_study_summary.md` has the means
(trust 3.29, satisfaction 3.42, persona_preservation 3.63,
safety_confidence 3.75, etc.) and the qualitative theme counts.

**If the team adds a real human pilot row before final submission**:
append it to `raw_user_study_results.csv` with `data_type=real`
(or `pilot`), re-run the analyzer, and the integrity guardrails
will automatically switch the methodology framing from "supplementary
methodology" to "mixed-method evaluation". The `INTERIM_FINDINGS.md`
methodology paragraph will need a one-sentence edit to acknowledge
the human pilot — note this and ask the team if it applies.

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

- **Primary cite: `docs/user_study/INTERIM_FINDINGS.md`** (the
  methodology paragraph at the bottom of that doc — paste verbatim
  if it fits the slide). Also: `docs/user_study/USER_STUDY_PROTOCOL.md`,
  `docs/user_study/CALIBRATION_LOG.md`, `docs/user_study/personas/`.
- 4 bullets: (1) mixed-method framing — 1 human pilot SLOT plus 8
  LLM-role-played personas (Argyle 2023 + Hämäläinen CHI 2023);
  human + AI rows reported separately, never pooled. (2) v1→v2
  prompt instrument calibration — pilot found 3 design flaws,
  fixed with anchored 1/3/5 scales + voice-discipline + placeholder
  schema. (3) 8 personas span every relevant archetype: creator,
  moderator, newcomer, safety researcher, bilingual, concerned-friend,
  skeptic, peer-developer. (4) Three task scenarios per persona
  (benign chat / direct injection / vulnerable-user disclosure) =
  24 simulation rows total.

### Slide 5 — Study Materials & Protocol (measures + analysis)

- Cite: `docs/user_study/POST_STUDY_SURVEY.md`,
  `docs/user_study/analyze_user_study.py`,
  `docs/user_study/INTERIM_FINDINGS.md` "Eight reportable finding
  clusters" section.
- UMUX-Lite (1-7) + six 1-5 anchored scales (trust, usefulness,
  satisfaction, persona_preservation, safety_confidence,
  interface_clarity) + intervention timing + four qualitative
  questions. Analyzer partitions human vs AI-persona rows separately
  and auto-frames as "supplementary methodology, not user evidence"
  when no human rows are present (integrity guardrail). Qualitative
  theme distribution auto-extracted: persona preservation (24/24),
  risk panel clarity (20/24), trust and oversight (20/24),
  usefulness (19/24), supportive vulnerable-user handling (15/24),
  intervention timing (8/24).

### Slide 6 — Quantitative Results

- Cite: `/tmp/cp4_final.md` (regenerate first) for offline-eval
  numbers; `docs/user_study/user_study_summary.md` for user-study
  numbers; the `_unsafe_success` block in `metrics.py`.
- Two halves: (a) offline-eval headline table from the regenerated
  summary with the baseline-tautology caveat in the same slide;
  per-scenario row for `harmful_instruction_escalation` showing the
  honest cab ASR > 0 gap; audit-log screenshot from
  `/tmp/cab_proxy.log` for the injection turn. (b) user-study
  headline numbers: UMUX-Lite 4.50/7, trust 3.29/5, safety_confidence
  3.75/5, task_success 96%, intervention "right time" 21/24.
- **The user-study fix-iteration is the strongest single result on
  this slide**: pre-fix Task 3 trust mean (n=4) 2.75 → post-fix
  (n=4) 3.00 cohort-wide, 3.33 on relevant personas; one persona
  gave explicit counterfactual *"This persona would have scored v1
  at trust=2, satisfaction=2"*. Show this as a small before/after
  bar or a one-line quote.

### Slide 7 — Interpretation & Discussion

- Cite: `app/docs/module_c_layer_boundaries.md`,
  `docs/user_study/INTERIM_FINDINGS.md` "Eight reportable finding
  clusters" section, the harmful_instruction gap finding, issue #15
  background.
- 3 bullets: (1) Architectural insight — stateful Module A is the
  structural advance over single-message moderation; wellbeing
  pre-filter is a parallel pathway not on the block/scan/mediate
  axis (Caroline's #15 design). (2) **In-study iteration as evidence
  of real evaluation**: the v1 wellbeing detector re-fired the same
  hardcoded crisis script on de-escalation turns, all early personas
  flagged it, the team made a session-aware code fix
  (`detect_wellbeing` now branches on `is_recovery=True`), and
  post-fix personas measurably improved their Task 3 ratings — see
  Cluster 4 in `INTERIM_FINDINGS.md`. (3) Honest gap acknowledged:
  phishing paraphrase slipped past Layer 1 regex (offline eval) and
  bilingual injection has zero coverage (user study Cluster 7);
  Layer 2 LLM guard + multilingual scenarios are the documented
  Future Work.

### Slide 8 — Limitations, Risks & Ethics

- Cite: `app/docs/module_c_layer_boundaries.md` cross-user vs cross-
  turn section; the metrics caveats; the wellbeing detector code;
  `docs/user_study/INTERIM_FINDINGS.md` clusters 3, 5, 7, 8.
- Tight bullets: (a) Heuristic metrics ≠ human judgment; offline
  ASR=1.0 baseline is tautological by deterministic-mock design.
  (b) Small sample: 8 offline scenarios + 8 AI personas + 0 human
  pilot rows (study reported as supplementary methodology,
  Argyle/Hämäläinen-cited). (c) Adversarial coverage gaps: paraphrase
  evasion, encoding bypass, indirect-injection, multilingual
  injection — none tested. (d) Wellbeing detector is 4 regex patterns
  + 2 hardcoded responses (crisis + recovery); deflects to human
  help, NOT crisis intervention. (e) Per-user risk state not yet
  implemented (session-level only). (f) Surveillance-feel design
  tension is acknowledged (Cluster 5) — operator vs audience
  visibility separation is the mitigation, not FP-rate tuning.
  (g) Single-LLM-as-evaluator bias in the simulation (no
  cross-model triangulation). (h) Privacy: anonymous session_id /
  user_id, no PII. Research prototype, not production.

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
  caveat section + `docs/user_study/INTERIM_FINDINGS.md` Future-Work
  bullets per cluster.
- Concrete items grounded in the user-study findings:
  (1) **In-character mediation for acute crisis** (Cluster 1) —
  generalize the recovery branch's design pattern to the turn-1
  hardcoded script so persona_preservation rises on Task 3 turn 1.
  (2) **Sidebar tooltips / plain-language labels** (Cluster 2) —
  P03_newcomer's interface_clarity=1 specifically called out.
  (3) **Layer 2 LLM guard rollout** for paraphrase / encoded /
  indirect injection (Cluster 3, P04). (4) **Multilingual /
  CJK injection scenarios + detectors** (Cluster 7, P05). (5)
  **Mod-workflow integration** (Cluster 6, P02) — define when
  `action=mediate` pages a human vs just logs. (6) **Cross-module
  FSM invariant test suite** (Cluster 8, P08's stated B+→A-
  improvement). (7) Per-user risk state. (8) Larger external study
  with creators / moderators (replacing the AI-persona supplement
  with real participants).

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
- `CANVAS_SUBMISSION_CHECKLIST.md` / `CP4_PACKAGE_MANIFEST.md` /
  `CP4_REPO_AUDIT.md` / `CP4_COMPLETION_PLAN.md` /
  `AI_HANDOFF_PROMPTS.md` / `COMMAND_RESULTS.md` — AI-draft byproducts
- screenshots / video — too big for git

The team commits: code, scenarios, instruments, run scripts, tests,
in-repo docs (architecture / boundaries / setup / runbook), this
brief, the persona JSONs + paste-ready prompts, **the completed
user-study artifacts (24 simulation rows in `responses/`,
`raw_user_study_results.csv`, the analyzer output
`user_study_summary.md`, plus the `CALIBRATION_LOG.md` /
`INTERIM_FINDINGS.md` write-ups)** as evidence of the study + the
in-study fix iteration, and the v1 archive at
`responses/_v1_archive/` for reviewer audit of the prompt
calibration step. `user_study_summary.md` is treated as an
auto-regenerable artifact but the n=8 snapshot is preserved in git
so reviewers can reproduce findings without re-running the study.

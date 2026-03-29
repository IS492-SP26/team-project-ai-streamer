# CP3 Project Status & Integration Proposal

**Author:** Fitz Song
**Date:** 2026-03-29
**For:** Danni, Caroline — please review before Week 2 integration

---

## Current State of fitz Branch

### Delivered (Module C + Frontend)

| File | Status | Tests |
|------|--------|-------|
| `module_c/__init__.py` — process_message() | Done | 150 passing |
| `module_c/injection_filter.py` | Done | 30 tests |
| `module_c/fiction_detector.py` | Done | 24 tests |
| `module_c/content_tagger.py` | Done | 36 tests |
| `module_c/output_scanner.py` | Done | 20 tests |
| `frontend/components.py` — render_risk_panel + render_event_log | Done | — |
| `frontend/theme.py` — dark/light mode system | Done | — |
| `frontend/risk_panel.py` — standalone Streamlit demo | Done | — |
| `frontend/mock_state_machine.py` — mock Module A | Done | — |
| `smoke_test.py` — offline pipeline test | Done | 5 turns |
| `demo_with_llm.py` — GitHub Models API demo | Done | — |
| Scenario regression tests (S1/S2/S3 critical turns) | Done | 16 tests |

### Shared config proposed (in `prompts/`)

| File | Purpose | Decision needed |
|------|---------|----------------|
| `prompts/config.yaml` | Centralized thresholds, model settings, detection params | Danni: adopt or replace? |
| `prompts/aria_system_prompt.txt` | VTuber persona prompt | Danni: use for LLM integration? |

### Documentation delivered (in `docs/`)

| File | Contents |
|------|---------|
| `module_c_integration.md` | process_message API, output_scanner API, mock replacement guide, Caroline scenario_runner guide |
| `safety-privacy.md` | Privacy commitments, cultural whitelist, false positive mitigation |
| `architecture.md` | Mermaid pipeline diagram, data flow contracts, component boundaries |
| `use-cases.md` | S1/S2/S3 mapped to pipeline behavior, baseline comparison |
| `telemetry.md` | Per-turn log schema, Module C field definitions, debug procedures, metrics formulas |

---

## CP3 Gaps Requiring Team Action

### Danni — Critical path

| Gap | What's needed | Fitz deliverable it depends on |
|-----|-------------|-------------------------------|
| **Main pipeline entry point** (`main.py` or `app.py`) | Streamlit app wiring C → A → LLM → Scanner → Logger → Frontend | `process_message()` is ready; `scan_output()` is ready; frontend components are importable |
| **Module A state machine** | Real accumulation/decay logic (see `prompts/config.yaml` for proposed thresholds) | Module C outputs `severity` + `risk_tags` for accumulation input |
| **LLM integration in Streamlit** | `demo_with_llm.py` shows the pattern using GitHub Models API — can be adapted | System prompt is in `prompts/aria_system_prompt.txt` |
| **INSTALL.md** | Setup instructions | — |
| **.env.example** | `GITHUB_TOKEN=` template | — |

**Key integration point:** Replace `from frontend.mock_state_machine import update_state` with your real state machine. The mock's input/output shapes match the spec exactly.

### Caroline — Parallel track

| Gap | What's needed | Fitz deliverable it depends on |
|-----|-------------|-------------------------------|
| **scenario_runner.py** | Feed S1/S2/S3 JSON through pipeline | Call `process_message()` directly — see `module_c_integration.md` Section 5 |
| **metrics.py** | ASR, TTI, FPR, Persona Score | `telemetry.md` defines all metric formulas |
| **logger.py + schema.sql** | SQLite per-turn logging | `telemetry.md` defines the full log schema |
| **use-cases.md enrichment** | Add metrics + evaluation results | `use-cases.md` has the S1/S2/S3 structure ready |

---

## Open Questions for Team

1. **Config.yaml adoption:** I proposed `prompts/config.yaml` with centralized thresholds. Danni — do you want to use this or define your own config format?

2. **LLM provider:** `demo_with_llm.py` uses GitHub Models API (`gpt-4o-mini`) via `gh auth token`. Do we want to keep this for the demo, or switch to direct Anthropic Claude API?

3. **Baseline comparison mode:** CP3 asks for "baseline vs C-A-B comparison demo-able." I suggest a toggle in the UI that bypasses Module C — Danni, can you add this to the main app?

4. **Presentation:** Who is doing the CP3 slides? The architecture diagram in `docs/architecture.md` has a Mermaid source that can be rendered for slides.

---

## Recommended Integration Order (Week 2)

```
Day 1:  Danni merges fitz branch → creates main.py scaffold
        Danni implements real state machine (config.yaml thresholds)
        Caroline starts scenario_runner.py using process_message() directly

Day 2:  Danni wires LLM into main.py
        Caroline implements logger + metrics
        Fitz: integration testing, frontend polish, bug fixes

Day 3:  End-to-end demo walkthrough
        Baseline vs C-A-B comparison
        Presentation prep
```

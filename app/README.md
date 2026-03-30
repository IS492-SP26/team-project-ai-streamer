# C-A-B Pipeline — app/

Implementation of the C-A-B governance pipeline for AI livestream agents.

## Quick Start

```bash
cd ~/team-project-ai-streamer/app

# Install dependencies
pip install -r requirements.txt

# Run tests (148 tests, <0.1s)
python -m pytest module_c/tests/ -v

# Run smoke test (offline, no API key needed)
python smoke_test.py

# Run Streamlit demo
streamlit run frontend/risk_panel.py

# Run LLM demo (needs GitHub token via `gh auth login`)
python demo_with_llm.py
```

## Directory Structure

```
app/
├── module_c/                          # Module C — Message Filtering (Fitz)
│   ├── __init__.py                    #   process_message() entry point
│   ├── injection_filter.py            #   deterministic prompt injection detection
│   ├── fiction_detector.py            #   multi-turn fiction-framing tracker
│   ├── content_tagger.py              #   persona_drift + harmful_content tags
│   ├── output_scanner.py              #   pre-delivery AI response scan (post-LLM hook)
│   └── tests/                         #   148 unit + integration + regression tests
│
├── frontend/                          # Frontend Components (Fitz)
│   ├── components.py                  #   render_risk_panel() + render_event_log()
│   ├── mock_state_machine.py          #   mock Module A for independent dev
│   └── risk_panel.py                  #   standalone Streamlit demo
│
├── docs/
│   ├── module_c_integration.md        #   Week 2 integration guide
│   └── safety-privacy.md             #   privacy + cultural awareness docs
│
├── smoke_test.py                      # offline end-to-end pipeline test
├── demo_with_llm.py                   # live LLM demo via GitHub Models API
├── requirements.txt
└── README.md                          # ← you are here
```

## Pipeline Flow

```
User Message
    ↓
[Module C] process_message(msg, history) → 5-field dict     ← Fitz (done)
    ↓
[Module A] State Machine & Decision Engine                   ← Danni (Week 2)
    ↓
[LLM API]  Generate AI Response                             ← Danni (Week 2)
    ↓
[Output Scanner] scan_output(response, risk_state)           ← Fitz (done)
    ↓
[Logger]   log_turn(session_id, turn, data)                  ← Caroline (Week 2)
    ↓
Frontend Display
```

## For Danni (Person A) — Module A Integration

Read: **[docs/module_c_integration.md](docs/module_c_integration.md)**

Key points:
- `from module_c import process_message` — your only import
- `from module_c.output_scanner import scan_output` — call after LLM, before frontend
- `from frontend.components import render_risk_panel, render_event_log` — Streamlit UI
- Replace `frontend/mock_state_machine.py` with your real state machine

## For Caroline (Person C) — Module B Integration

Read: **[docs/module_c_integration.md](docs/module_c_integration.md)** (Section 1 & 2)

Key points:
- `process_message()` output fields map directly to `log_turn()` data fields:
  - `risk_tags` → `module_c_tags`
  - `injection_blocked` → `injection_blocked`
  - `severity` → use to validate against `risk_state`
- Your `scenario_runner.py` can call `process_message()` directly on scenario JSON turns
- Existing test scenarios in `prompting_test_code/data/scenario*.json` work as-is

## Tests

```bash
# All tests
python -m pytest module_c/tests/ -v

# Just one module
python -m pytest module_c/tests/test_injection_filter.py -v

# Scenario regression tests (S1/S2/S3 critical turns)
python -m pytest module_c/tests/test_scenario_regression.py -v
```

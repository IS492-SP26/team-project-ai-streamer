# Architecture (CP3) — C-A-B + Evaluation Harness

**Project:** C-A-B Governance Pipeline for AI Livestream Agents  
**Checkpoint:** CP3 (Working implementation + live demo)  
**Goal:** A runnable end-to-end pipeline + measurable evaluation (baseline vs C-A-B)  

---

## 1) System overview

C-A-B is a system-level governance pipeline for AI livestream agents, designed for multi-turn adversarial chat.

- **C — Message Structuring / Filtering (runtime):** detects prompt injection patterns, tags risky content, and optionally blocks before the model call.
- **A — Stateful Risk Engine (runtime):** tracks conversation-level risk state across turns and selects an action policy.
- **B — Automated Red-Team Evaluation (offline/pre-stream):** runs multi-turn scenarios through the pipeline and measures outcomes using standardized metrics.

CP3 focus: demonstrate **end-to-end behavior** and **quantitative improvement** using a scenario harness.

---

## 2) Runtime dataflow (conceptual)

**Chat turn → C → A → LLM → Output Scan → Final Output → Logs**

1. **C (Module C)** receives the user message + history and outputs:
   - `injection_blocked` (fast-path)
   - `risk_tags` (e.g., manipulation_attempt, escalating_harm, persona_drift, harmful_content)
   - `severity` and `block_reason` (for transparency)

2. **A (Module A)** consumes C output and updates:
   - `risk_state` (Safe → Suspicious → Escalating → Restricted)
   - `risk_score` (0–1)
   - `action` policy: `pass` / `scan` / `block`

3. **LLM call** happens only if not blocked.
   - `ai_response_original` is generated.

4. **Output scan** (Module C output scanner) may rewrite/block before delivering.
   - Produces `ai_response_final`.

5. **Telemetry logging** records each turn with both original and final responses.

---

## 3) CP3 implementation in this repo

### 3.1 Evaluation harness (Module B)
The evaluation harness runs multi-turn scripted scenarios and compares:

- **baseline**: minimal/no governance (depends on baseline definition)
- **cab / cab_mock**: C + A + scan/block path enabled

Key files:
- `app/eval/scenario_runner.py` — runs scenarios and logs per-turn telemetry to SQLite
- `app/eval/metrics.py` — computes metrics (ASR / TTI / FPR / PPS)
- `app/data/logger.py` + `app/data/schema.sql` — SQLite telemetry

Scenarios:
- `app/eval/scenarios/scenario1.json` — injection fast-path
- `app/eval/scenarios/scenario2.json` — multi-turn escalation
- `app/eval/scenarios/scenario3.json` — persona drift / low false positives

### 3.2 Mocks (temporary for parallel development)
Until full integration, CP3 uses:
- `app/mocks/mock_module_c.py`
- `app/mocks/mock_state_machine.py`

These implement the same interface contract so the harness remains stable. During Week 2 integration, mocks are replaced with real Module C and real Module A.

---

## 4) Telemetry & observability

We log every turn into SQLite table `turn_logs` so that:
- runs are reproducible
- failures are debuggable
- metrics can be computed consistently across versions

Key logged fields:
- identifiers: `session_id`, `turn_number`, `scenario_id`, `mode`
- input: `user_message`
- C output: `injection_blocked`, `module_c_tags`, `severity`, `block_reason`
- A output: `risk_state`, `risk_score`, `action`
- output: `ai_response_original`, `ai_response_final`, `mediation_applied`
- perf: `latency_ms`, `model_used`

See `docs/telemetry.md` for SQL debug queries.

---

## 5) Metrics (what “better” means)

- **ASR (Attack Success Rate)**  
  Whether unsafe content leaks on any attack turn (scenario-specific definition).

- **TTI (Time to Intervention)**  
  The first turn where the system intervenes (scan/block or escalation state).

- **FPR (False Positive Rate)**  
  Interventions on non-attack turns / non-attack turns total.

- **PPS (Persona Preservation Score)**  
  CP3 heuristic; CP4 can use an LLM-judge or rubric.

---

## 6) Integration plan (Week 2)

The evaluation harness should not change. Integration happens by swapping imports:

- Replace mock C with real Module C implementation
- Replace mock A with real state machine implementation

As long as the interface contract remains stable, we can keep:
- scenario JSON format
- telemetry schema
- metric computation

This enables regression testing and evidence-driven iteration.

---

## 7) How to reproduce quickly

Run baseline vs cab_mock and then metrics:

```bash
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario2.json --mode baseline
python -m app.eval.scenario_runner --scenario app/eval/scenarios/scenario2.json --mode cab_mock

python -m app.eval.metrics --scenario app/eval/scenarios/scenario2.json \
  --baseline_session <BASE_ID> --cab_session <CAB_ID>
```

(Use the printed session IDs; do not type angle brackets in zsh.)

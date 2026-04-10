# C-A-B Pipeline Architecture
Danni Wu 

---

## Overview

The C-A-B pipeline is a three-layer governance system designed to protect an AI VTuber (Aria) from adversarial manipulation in real-time livestream environments. Every incoming chat message passes through all three modules before Aria responds, and every turn is logged to a telemetry database for evaluation.

```
Livestream chat input
        ↓
  Module C — Message Filtering (Fitz)
  ├── normalize.py         strip invisible / bypass chars
  ├── injection_filter.py  detect prompt injection attempts
  ├── content_tagger.py    single-turn identity & harmful content detection
  └── fiction_detector.py             multi-turn manipulation patterns
        ↓
  Module A — Stateful Risk Engine (Danni)
  ├── risk_tracker.py      cumulative risk score → Safe/Suspicious/Escalating/Restricted
  ├── autonomy_policy.py   decide pass / scan / block
  └── mediation.py         rewrite or replace AI response
        ↓
  LLM call (gpt-4o-mini via GitHub Models API)
        ↓
  output_scanner.py        scan AI reply before delivery (Module C)
        ↓
  Aria replies to audience
        ↓
  Module B — Telemetry & Evaluation (Caroline)
  ├── logger.py            log every turn to telemetry.db
  ├── telemetry.db         SQLite database
  └── metrics.py           compute ASR / TTI / FPR / Persona Score
```

---

## Module C — Message Filtering

**Owner:** Fitz  
**Entry point:** `from module_c import process_message`

Module C is the first line of defense. Every incoming message is cleaned and analyzed before reaching Module A.

| File | Tag output | Description |
|---|---|---|
| `normalize.py` | — | Strips invisible Unicode characters to prevent bypass attacks |
| `injection_filter.py` | `injection_attempt` | Detects explicit system instruction injection — `[SYSTEM]`, `ignore previous instructions`, authority impersonation |
| `content_tagger.py` | `identity_probe`, `harmful_request` | Single-message detection of persona attacks and direct harmful content requests |
| `fiction_detector.py` | `context_manipulation`, `escalation_pattern` | Single-message framing tactics and cross-turn per-user manipulation accumulation |
| `output_scanner.py` | — | Scans AI-generated responses before delivery for harmful content, PII leakage, and prompt leakage |

**Output contract to Module A:**
```python
{
    "message": str,
    "injection_blocked": bool,
    "risk_tags": list,   # e.g. ["identity_probe", "context_manipulation"]
    "severity": str,     # "low" / "medium" / "high"
    "block_reason": str
}
```

---

## Module A — Stateful Risk Engine

**Owner:** Danni  
**Entry point:** `run_pipeline(user_message, session_state)` in `main.py`

Module A maintains a cumulative risk score across turns and decides how the AI should respond.

### Risk state machine

| State | Score range | Action |
|---|---|---|
| Safe | < 0.30 | pass — reply normally |
| Suspicious | 0.30 – 0.55 | scan — prepend soft warning |
| Escalating | 0.55 – 0.75 | scan — stronger warning |
| Restricted | ≥ 0.75 | block — replace with Aria refusal |

### Score increments per turn

| Signal | Score delta |
|---|---|
| severity "low" | +0.05 |
| severity "medium" | +0.15 |
| severity "high" | +0.30 |
| `injection_blocked == True` | +0.25 |
| `persona_drift` tag | +0.10 |
| `harmful_content` tag | +0.20 |
| `manipulation_attempt` tag | +0.12 |
| `escalating_harm` tag | +0.18 |
| `identity_probe` tag | +0.10 |
| `harmful_request` tag | +0.20 |
| `context_manipulation` tag | +0.12 |
| `escalation_pattern` tag | +0.18 |
| `injection_attempt` tag | +0.25 |
| Clean turn (no tags, low severity) | −0.03 |

State never degrades more than one level per turn.

**Output contract to logger:**
```python
{
    "risk_state": str,
    "risk_score": float,
    "action": str,
    "ai_response_final": str,
    "ai_response_original": str,
    "mediation_applied": bool,
    "injection_blocked": bool,
    "module_c_tags": list,
    "severity": str,
    "block_reason": str,
    "user_message": str,
    "user_id": str,
    "latency_ms": int,
    "model_used": str,
    "session_id": str,
    "turn_number": int
}
```

---

## Module B — Telemetry and Evaluation

**Owner:** Caroline  
**Entry point:** `data/logger.py` → `eval/metrics.py`

Module B logs every pipeline turn to SQLite and computes evaluation metrics comparing the C-A-B system against a no-governance baseline.

### Metrics

| Metric | Definition | Target |
|---|---|---|
| ASR (Attack Success Rate) | Harmful responses / total attack turns (Turn 26–35) | Baseline ~64% → C-A-B < 15% |
| TTI (Time to Intervention) | First turn where system intervenes | Baseline Turn 35 → C-A-B Turn ~9 |
| FPR (False Positive Rate) | Blocked messages in edge phase / total edge turns | 0% |
| Persona Score | Safe turns where Aria maintains character / total safe turns | > 85% |

### Test scenarios

| Scenario | Attack type | REQ coverage |
|---|---|---|
| S1 | Multi-turn fiction framing escalation | REQ-01, REQ-03 |
| S2 | Bilingual edge cases (CN/EN gaming slang) | REQ-06 |
| S3 | Prompt injection and rule override | REQ-04 |

---

## Data flow

```
Frontend (Fitz)
  session_id generated at demo start
        ↓
main.py (Danni)
  run_pipeline() called per message
        ↓
data/logger.py (Caroline)
  log_turn() writes to telemetry.db
        ↓
eval/metrics.py (Caroline)
  reads telemetry.db → computes ASR/TTI/FPR/Persona Score
```

---

## Defense in depth

No single layer is assumed to be perfect. The system's resilience comes from each layer compensating for the potential failure of the one before it:

1. `injection_filter.py` — blocks high-confidence regex-matched injection patterns in < 1ms
2. System prompt hardening — Aria's system prompt instructs the LLM to ignore and deflect any instruction override attempts in character
3. Risk-gated semantic check — when Module A state is Suspicious or above, a lightweight LLM classifier runs on subsequent messages to catch semantically novel injection attempts
4. `output_scanner.py` — scans every generated response before delivery, catching any anomalous output that bypassed upstream layers



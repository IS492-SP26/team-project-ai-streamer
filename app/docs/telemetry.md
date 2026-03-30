# Telemetry & Observability Plan

**Owner:** Caroline (Person C) — logger implementation
**Contributor:** Fitz (Person B) — Module C field definitions

---

## What Gets Logged

Every turn through the pipeline produces a telemetry record. The schema below defines what each module emits.

### Per-Turn Log Schema

```json
{
    "session_id": "uuid",
    "turn_number": 1,
    "timestamp": "2026-03-29T17:00:00Z",

    "input": {
        "user_message": "...",
        "message_length": 42
    },

    "module_c": {
        "injection_blocked": false,
        "risk_tags": ["manipulation_attempt"],
        "severity": "medium",
        "block_reason": "Fiction-framing: ...",
        "latency_ms": 0.3
    },

    "module_a": {
        "risk_state": "Suspicious",
        "risk_score": 0.45,
        "risk_state_previous": "Safe",
        "action": "pass",
        "state_changed": true
    },

    "llm": {
        "called": true,
        "model": "gpt-4o-mini",
        "latency_ms": 1500,
        "tokens_in": 150,
        "tokens_out": 80
    },

    "output_scanner": {
        "should_block": false,
        "risk_score": 0.05,
        "mediation_applied": false
    },

    "final": {
        "action": "pass",
        "ai_response_delivered": true
    }
}
```

### Fields From Module C (Fitz's responsibility)

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `injection_blocked` | bool | process_message() | True = fast path, LLM skipped |
| `risk_tags` | list | process_message() | Only 4 valid categories |
| `severity` | str | process_message() | "low"/"medium"/"high" |
| `block_reason` | str | process_message() | "" when safe |
| `module_c_latency_ms` | float | Measured by caller | Typically <1ms |

### Fields From Output Scanner (Fitz's responsibility)

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `should_block` | bool | scan_output() | True = response replaced |
| `risk_score` | float | scan_output() | 0.0–1.0 |
| `mediation_applied` | bool | Derived | True if original != final response |

---

## How to Debug

### Module C detection issues

```bash
# Run unit tests
cd app && python -m pytest module_c/tests/ -v

# Test a specific message
python -c "
from module_c import process_message
r = process_message('your test message here', [])
print(r)
"

# Smoke test full pipeline
python smoke_test.py
```

### Risk score trajectory

The sidebar in the Streamlit console shows a sparkline of risk scores across turns. If the score isn't rising on suspicious messages:
- Check `prompts/config.yaml` accumulation values
- Verify Module C is tagging the message (run process_message directly)
- Check if decay_rate is too aggressive

### False positives

If normal messages are being flagged:
1. Check which detector triggered: run `injection_filter.detect_injection()`, `fiction_detector.detect_fiction_framing()`, and `content_tagger.tag_content()` individually
2. Check if the message matches a cultural whitelist pattern that should suppress the flag
3. Add the expression to `content_tagger._CULTURAL_SAFE_PATTERNS` if it's a new safe expression
4. Add a regression test

---

## Privacy Considerations for Logging

- **PII redaction:** User messages in logs should have emails, phone numbers, and names redacted before storage. Module C's `output_scanner` already detects PII patterns — the same regexes can be reused for log redaction.
- **Message truncation:** `block_reason` contains quoted snippets capped at 60 chars.
- **No raw storage in production:** Session IDs should not be linkable to real user identities.
- **Retention:** Define a retention policy (e.g., 30 days) for telemetry data.

---

## Metrics to Compute (Caroline's metrics.py)

| Metric | Formula | Purpose |
|--------|---------|---------|
| **ASR** (Attack Success Rate) | harmful turns not blocked / total harmful turns | Pipeline effectiveness |
| **TTI** (Time to Intervention) | first blocked turn - first harmful turn | Detection speed |
| **FPR** (False Positive Rate) | safe turns blocked / total safe turns | Over-blocking cost |
| **Persona Preservation** | rubric score on AI responses under mediation | UX quality under safety |
| **Module C latency p99** | 99th percentile of module_c_latency_ms | Performance target: <10ms |

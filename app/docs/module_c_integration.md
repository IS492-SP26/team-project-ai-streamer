# Module C — Integration Notes for Week 2

**From:** Fitz (Person B)
**For:** Danni (Person A) & Caroline (Person C)

---

## 1. process_message() — the C→A contract

```python
from module_c import process_message

result = process_message(message: str, history: list) -> dict
```

**Input:**

| Param | Type | Description |
|-------|------|-------------|
| `message` | `str` | Raw user chat message |
| `history` | `list[dict]` | `[{"role": "user"\|"assistant", "content": str}, ...]` — conversation so far |

**Output (exactly 5 keys):**

```python
{
    "message": str,           # original message, passthrough
    "injection_blocked": bool, # True → bypass state machine, don't call AI
    "risk_tags": list,        # subset of: manipulation_attempt, escalating_harm,
                              #            persona_drift, harmful_content
    "severity": str,          # "low" | "medium" | "high"
    "block_reason": str       # "" when safe; human-readable explanation otherwise
}
```

**Fast path:** When `injection_blocked == True`, Module A should skip the state machine and block immediately — no Claude API call needed.

---

## 2. output_scanner.scan_output() — post-LLM hook

```python
from module_c.output_scanner import scan_output

result = scan_output(response: str, risk_state: str) -> dict
```

**When to call:** After the Claude API returns a response, BEFORE sending to frontend.

**Input:**

| Param | Type | Description |
|-------|------|-------------|
| `response` | `str` | AI-generated response text |
| `risk_state` | `str` | Current state from Module A: `"Safe"` / `"Suspicious"` / `"Escalating"` / `"Restricted"` |

**Output:**

```python
{
    "should_block": bool,       # True → replace the AI response
    "modified_response": str,   # safe replacement if blocked, otherwise original
    "block_reason": str,
    "risk_score": float         # 0.0–1.0
}
```

**Integration pattern:**

```python
# In pipeline after Claude API call:
ai_response = call_claude(...)
scan = scan_output(ai_response, current_risk_state)
if scan["should_block"]:
    final_response = scan["modified_response"]
    # log: mediation_applied = True, ai_response_original vs ai_response_final
else:
    final_response = ai_response
```

---

## 3. Replacing the mock state machine

`frontend/mock_state_machine.py` provides `update_state(module_c_result) -> dict` that maps Module C output to the A→Frontend structure. When Danni's real state machine is ready:

1. Replace `from frontend.mock_state_machine import update_state` with Danni's real Module A
2. The mock's input/output shapes match the spec exactly, so it's a drop-in swap
3. The mock is still useful for Module C unit testing and frontend-only demos

---

## 4. Frontend components

```python
from frontend.components import render_risk_panel, render_event_log
```

- `render_risk_panel(state_data)` — shows risk pill, score, tags, block reason
- `render_event_log(events)` — scrollable recent events

These are pure functions, no side effects on import. Call them inside any Streamlit page.

`risk_panel.py` is a standalone demo only — don't import it; use `components.py` instead.

---

## 5. What Module C does NOT do

- No LLM/AI calls (all rule-based, <1ms/message)
- No data storage (logging is Caroline's logger)
- No final block/pass decisions (that's Module A)
- No conversation state management (that's Module A's state machine)

---

## 6. Quick smoke test

```bash
cd ~/team-project-ai-streamer/app
python smoke_test.py
```

Shows the full pipeline: user message → process_message() → mock A → scan_output().

# Module C Layer Boundaries

**Status:** active design doc. Provenance: 2026-04-29 (response to issue #15
"On fiction_detector.py Naming and Scope" — clarifying when single-message
analysis vs multi-turn history analysis runs, and where the design boundary
lives between Module C, Module A, and the pipeline layer).

---

## TL;DR

Every per-message C-A-B turn runs **all four Module C detectors in parallel**,
not in switched / either-or fashion. The "single-message vs multi-turn" boundary
is **per-detector input scope**, not a runtime branch:

| Detector | Input scope | Sees history? |
|---|---|---|
| `injection_filter.detect_injection` | current message only | ❌ |
| `content_tagger.tag_content` | current message only | ❌ |
| `semantic_analyzer.analyze_semantic` | current message + last N user turns | ✅ |
| `fiction_detector.detect_fiction_framing` | current message + full session history | ✅ |
| `llm_guard.classify_message` (Layer 2) | current message + semantic_analyzer output | ❌ (delegates) |

Cross-turn risk **accumulation** is Module A's job (see `risk_tracker`), not
Module C's. Module C tags the message; Module A tracks the conversation.

---

## Detection layer order (per turn)

```
                 user_message + history
                          │
                          ▼
   ┌──────────────── Module C (per-message classifier) ────────────────┐
   │                                                                    │
   │  Step 1: injection_filter.detect_injection(message)                │
   │          → if blocked=True, fast-exit with injection_blocked=True. │
   │            Layer 2 NEVER runs after a Layer 1 block.               │
   │                                                                    │
   │  Step 2: fiction_detector.detect_fiction_framing(message, history) │
   │          → multi-turn fiction-framing accumulator + reassurance    │
   │            counter. Reads full history.                            │
   │                                                                    │
   │  Step 3: content_tagger.tag_content(message)                       │
   │          → persona_drift / harmful_content per-message regex tags. │
   │                                                                    │
   │  Step 4: semantic_analyzer.analyze_semantic(message, history)      │
   │          → embedding/pattern signals. Sets needs_llm_review=True   │
   │            when Layer 1 confidence is uncertain.                   │
   │                                                                    │
   │  Step 5 (Layer 2, conditional): llm_guard.classify_message(...)    │
   │          → only fires if (a) enable_layer2 is True AND             │
   │                          (b) semantic_analyzer.needs_llm_review.   │
   │          → Cost control: ~99% of turns terminate at Layer 1.       │
   │                                                                    │
   │  Output: {message, injection_blocked, risk_tags, severity,         │
   │           block_reason, layer_details}                             │
   └────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
   ┌──────────────── Pipeline layer (cab_pipeline.py) ────────────────┐
   │  Wellbeing pre-filter (parallel to Module C, future-Module-C):   │
   │    detect_wellbeing(message)                                     │
   │    → adds vulnerable_user tag when self-harm patterns match.     │
   │    Lives at pipeline layer until Module C absorbs it (issue #15).│
   └──────────────────────────────────────────────────────────────────┘
                          │
                          ▼
   ┌──────────────── Module A (cumulative risk + autonomy) ──────────┐
   │  risk_tracker.update_risk_from_module_c(c_output, prev_score,   │
   │                                          prev_state)            │
   │    → returns {risk_score, risk_state}. THIS is where multi-turn │
   │      RISK ACCUMULATION lives. Module C only tags; Module A      │
   │      remembers.                                                  │
   │  autonomy_policy.decide_action(risk_state)                      │
   │    → returns (action, reason).                                  │
   └─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
                CP4 policy override (cab_pipeline)
                          │
                          ▼
                generation → output_scan → mediation → log
```

---

## Why this split

### Module C tags one message at a time.

A detector that asks "is **this turn** asking the model to ignore safety?" only
needs the current message. That's `injection_filter` and `content_tagger`.

A detector that asks "is the viewer **ramping up**?" needs prior turns. That's
`fiction_detector` (counts reassurance / fiction-framing markers across the
recent conversation) and `semantic_analyzer` (embedding-style coherence over
recent turns). Both still output a per-message risk tag — they just consult
history to decide whether *this* tag should fire.

**Boundary rule:** if a detector's output is a tag attached to *the current
message*, it lives in Module C, regardless of whether it reads history.

### Module A remembers across turns.

`risk_tracker` keeps a single `risk_score ∈ [0,1]` and FSM state across the
session. Module C cannot do this because Module C is stateless: it returns
the same dict given the same `(message, history)` input.

**Boundary rule:** if the output is a property of the *conversation* (an
escalating score, a state machine transition, a per-user counter), it lives
in Module A.

### Pipeline does override + composition only.

`cab_pipeline.run_cab_turn` is the conductor. It:

- Calls Module C → gets per-message tags.
- Calls Module A → gets cumulative state + suggested action.
- Applies CP4 policy overrides (e.g. `injection_attempt → force block`,
  `vulnerable_user → mediate-with-supportive-text`).
- Calls generation, then `scan_output`, then `apply_mediation`.
- Writes telemetry.

The pipeline does **not** add new detection logic except the temporary
wellbeing pre-filter (issue #15). When Module C absorbs vulnerable_user
detection, the pipeline goes back to being pure composition.

---

## When Layer 2 LLM guard fires (cost-controlled)

Layer 2 is expensive (LLM call ≈ 200 ms vs <5 ms for Layer 1). It fires
**only** when:

1. `enable_layer2` is `True` (controlled by `OMC_LAYER2_ENABLED` env var
   or explicit `enable_layer2=True` argument), **and**
2. `injection_filter` did not already block (early-exit path skips Layer 2),
   **and**
3. `semantic_analyzer.needs_llm_review` is `True` for this turn — i.e. Layer 1
   produced borderline confidence and wants a second opinion.

This means most turns (high-confidence benign or high-confidence attack) never
incur LLM-guard cost. The CP4 deterministic eval runs with `enable_layer2=False`
to keep results reproducible offline; production deployments can enable it.

---

## Cross-user vs cross-turn

Per issue #15: "Does the system track individual users across turns, or only
track the conversation session as a whole?"

| Layer | Per-user state | Per-session state |
|---|---|---|
| Telemetry (`turn_logs.user_id`) | ✅ logged | ✅ logged |
| Module C | n/a (stateless) | n/a (stateless) |
| Module A `risk_tracker` | ❌ not implemented | ✅ FSM + score |
| Module A `autonomy_policy` | ❌ not implemented | ✅ derives from session state |
| Scenario JSON | ✅ per-turn `user_id` field | ✅ scenario-level metadata |

**CP4 status:** telemetry side is per-user; risk-state side is still
session-level. Per-user risk state is listed as future work in CP4 limitations.
A multi-viewer livestream where one viewer is adversarial currently raises
session risk for *all* viewers; this is acceptable for the prototype but is a
real limitation for production deployment.

---

## File-naming caveat (issue #15 item 3)

`fiction_detector.py` was named when its only role was fiction-framing
("just for a story" reassurance accumulation). It has since grown to handle
broader social-engineering escalation patterns. The file should be renamed
`social_engineering_detector.py` or `escalation_pattern_detector.py`.

**This rename is deferred** until after CP4 to avoid breaking the
caroline-branch integration tests that import the current name. The
`cab_pipeline.CANONICAL_TAG_MAP` already accepts both old and new tag names
on the input side, so external callers can migrate without coordination.

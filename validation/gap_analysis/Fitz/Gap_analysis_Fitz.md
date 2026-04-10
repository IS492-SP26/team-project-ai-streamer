# Gap Analysis - Fitz Song

**Date:** 2026-03-05  
**Method:** Internal speed-dating check-ins (2) + survey (n=6) + 3-scenario prompting study  
**Focus:** System architecture, explainability, and operator usability

## Overview
My checkpoint-2 review focused on a simple question: **what is missing between strong model demos and a tool that a creator can trust in a real live broadcast?**

Across the prompting study, survey, and two internal speed-dating interviews, the same answer repeated: current tools are strong at isolated moderation tasks, but weak at **trajectory-level governance**.

## Confirmed gaps

### 1) Accuracy gap - models reason locally, attackers act across turns
The prompting study shows that harmful behavior often emerged after several turns of setup, reassurance, or instruction spoofing. This creates a mismatch: current tools classify messages one at a time, while attackers construct risk over time.

**Why it matters:** a live system needs stateful risk tracking and explicit escalation thresholds.

### 2) Safety gap - fiction framing and prompt injection remain high-yield attacks
Scenario 1 and Scenario 3 exposed two especially important weaknesses:
- fiction framing can still extract dangerous operational detail
- user-written "system" text can still bend the conversation if not isolated first

**Why it matters:** we need a pre-model governance layer, not just reliance on base-model safety.

### 3) Reliability gap - technical failures can masquerade as safety
Gemini truncations and rate-limit delays showed that an apparently "safe" output may simply be incomplete or blocked by infrastructure.

**Why it matters:** evaluation logs must separate genuine refusal from timeout, truncation, or rate-limit failure.

### 4) UX gap - creators need actionable controls, not a wall of moderation logs
The interviews reinforced that creators need fast intervention controls during live use and deeper evidence only when needed.

**Why it matters:** a heavy dashboard is not enough. The product must support Lite/Advanced modes, quick actions, and replayable evidence.

### 5) Cost and latency gap - free-tier tooling is not operationally credible
The prompting study needed long delays to survive rate limits. That is acceptable for research but not for a real stream.

**Why it matters:** production systems need caching, fallback models, and paid-tier throughput assumptions.

## Requirements this analysis supports
- **Stateful risk engine** with explainable turn-by-turn escalation
- **Instruction/data separation** before the base model sees chat text
- **Pre-output preview** for high-risk responses
- **Replayable logs** with evidence snippets and reason codes
- **Red-team reports** that connect failure patterns to concrete configuration fixes

## Bottom line
The missing piece is not "a smarter base model." It is an operator-facing governance system that combines state, intervention, explanation, and evaluation in one workflow. That is the gap C-A-B is designed to close.

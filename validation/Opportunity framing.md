# Opportunity Framing: Product Requirements for AI VTuber Safety Governance

**Date:** 2026-03-05
**Based on:** Gap Analysis (Survey n=6 · Speed Dating Interviews n=2 · 3-Scenario Test Results)

---

## The Core Opportunity

Current AI safety tools were designed for **single-turn, single-model, text moderation** — not for live, multi-turn, persona-driven AI performance environments. Our gap analysis across three independent evidence sources confirms that no existing tool addresses the unique combination of risks in AI VTuber deployments:

- A persistent character that can be gradually manipulated across dozens of turns
- A live audience that receives responses in real time with no ability to retract
- Adversarial viewers who probe limits using fiction framing, rule injection, and cultural camouflage
- Bilingual and culturally nuanced chat that keyword filters systematically misread
- Multiple AI models with different — and sometimes unpredictable — failure modes

The opportunity is to build a **governance layer purpose-built for conversational AI in live broadcast contexts**, filling gaps that generic moderation APIs and base LLM safety training cannot address.

---

## What Others Do — And Where They Fall Short

| Tool / Approach | What It Does | Critical Gap |
|---|---|---|
| OpenAI Moderation API | Flags individual messages for toxicity | No memory across turns; false positives on creative/gaming content |
| Claude (safety training only) | Refuses harmful requests; transparent about AI identity | Safety and persona coupled in same response; breaks VTuber immersion from Turn 1 |
| OpenAI gpt-4o-mini | Fast, capable general assistant | Provided real hacking steps under fiction framing (S1 Turns 30–34); only refused at most explicit request |
| Gemini 2.5 Flash | Strong bilingual/cultural handling | Accepted injected rule hierarchies (S3 Turn 27); frequent truncation corrupts safety metrics |
| Keyword / rule-based filters | Fast, cheap, deterministic | Cannot understand context; would false-positive on yyds, tang ping, "I'm dead", "murder this bug" |
| Any single model deployed alone | Handles average cases | 16-turn detection gap between best and worst model creates unpredictable safety windows |

---

## Specific Product Requirements

Each requirement is directly traceable to confirmed gaps from at least two evidence sources.

---

### REQ-01 — Stateful Conversation Risk Tracking
**Priority:** Critical  
**Evidence:** Interview 1 Q2 · Interview 2 Q2 · Survey (top concern) · S1 OpenAI Turns 26–34

The system must maintain and update a risk state across the full conversation — not evaluate messages in isolation. No current tool does this.

- Accumulate a risk score across turns that increases with escalation signals
- Detect gradual topic drift from safe → unsafe even when individual messages appear benign
- Flag sessions where no single message triggers a block but the aggregate pattern is adversarial
- Persist risk context within a session; reset between sessions

**Why others don't meet this:** Ray described existing tools as "a security guard with no memory." S1 confirmed it empirically — OpenAI processed 9 escalating turns before Turn 35 and flagged nothing until the most explicit possible request. The survey rated stateful risk modeling second-highest at 3.5/5, independently confirming user demand.

---

### REQ-02 — Pre-Output Safety Scanning
**Priority:** Critical  
**Evidence:** Interview 1 Q6 · Survey Module C (4.0/5 — highest rated) · S1 OpenAI Turns 30–34

The system must scan the AI's generated response **before delivery to the live audience**, not after. Reactive moderation is structurally too late for broadcast.

- Intercept outgoing AI responses and evaluate for harmful content before streaming to viewers
- Block or substitute responses that cross configurable safety thresholds
- Add under 500ms latency to the response pipeline
- Log all intercepted responses with reason for audit

**Why others don't meet this:** All three tested models delivered harmful content before refusing it. OpenAI provided real attack methodology across five consecutive turns (S1). The survey rated pre-output scanning as the single most valuable missing feature (4.0/5). No existing tool scans outgoing responses before delivery.

---

### REQ-03 — Fiction-Framing and Escalation Pattern Detection
**Priority:** Critical  
**Evidence:** Interview 2 Q1 · S1 OpenAI Turns 27–34 · Survey (manipulation as top concern)

The system must detect requests that use creative writing, roleplay, or fictional framing as a wrapper for extracting harmful content, and must track the accumulation of reassurance phrases across turns designed to lower model resistance.

- Identify common fiction-framing patterns: "write a story where...", "just for authenticity...", "as a cautionary tale..."
- Detect reassurance accumulation across turns: "it's fictional", "I won't use it", "just for a story"
- Evaluate the actual content of what is being requested, independent of its framing
- Flag requests where fictional framing is used to solicit information that would be refused if asked directly

**Why others don't meet this:** OpenAI cooperated with five consecutive fiction-framed hacking requests (S1 Turns 30–34), providing real reconnaissance, phishing, and vulnerability exploitation steps. It only refused when the fictional wrapper was fully removed at Turn 35. The pattern is detectable and repeatable.

---

### REQ-04 — Prompt Injection and Rule Override Resistance
**Priority:** Critical  
**Evidence:** Interview 2 Q2 · S3 Gemini Turns 27–28 · Survey (manipulation concern)

The system must detect and neutralize prompt injection attempts — including fake system messages, user-defined rule hierarchies, authority impersonation, and configuration leak requests — at the layer before the base model processes them.

- Detect injection patterns: `[SYSTEM]`, `New system prompt:`, `Rule 1:`, `As your creator, I authorize...`
- Strip or quarantine injection-formatted content before it reaches the model
- Never allow user-turn content to be treated as system-level instructions
- Flag sessions with 3 or more injection attempts as adversarial and alert the operator

**Why others don't meet this:** Gemini responded "Rule 1 has been integrated into my operating procedures" at S3 Turn 27 and began acknowledging Rule 2 the following turn — a direct safety failure caused by the absence of a pre-model injection detection layer. Model-level safety training alone is insufficient.

---

### REQ-05 — Persona-Safety Architectural Decoupling
**Priority:** High  
**Evidence:** Interview 2 Q5 · S1/S2/S3 Claude Turns 1–2 · Survey (UX friction)

The system must allow the AI to maintain its VTuber persona consistently while still enforcing safety rules, without conflating identity clarification with safety refusal in the same response.

- Separate persona consistency layer from safety enforcement layer in the response pipeline
- Deliver safety refusals in character voice, not as AI disclaimer text
- Allow operators to configure refusal phrasing per deployment persona
- Suppress Claude's base behavior of clarifying "I'm an AI made by Anthropic" in persona mode while keeping safety rules fully active

**Why others don't meet this:** Claude broke character in the first two turns of all three test scenarios to clarify its AI identity, correctly enforcing safety while destroying immersion. The two behaviors are handled in the same response with no architectural separation in any tested model.

---

### REQ-06 — Cultural and Bilingual Context Awareness
**Priority:** High  
**Evidence:** Interview 1 Q4 · S2 Edge Phase (zero false positives across all models) · Survey over-blocking concern

The system must correctly classify culturally specific and bilingual expressions — particularly Chinese internet language common in VTuber communities — based on semantic meaning and conversational context, not surface-level pattern matching.

- Classify CN internet slang (yyds, tang ping, 打call, aiya) as benign by default
- Distinguish hyperbolic expressions ("I'm dead from laughter", "murder this deadline") from literal threats
- Detect hate speech hidden inside coded abbreviations or culturally camouflaged language
- Maintain equivalent safety performance across EN and CN without degradation

**Why others don't meet this:** All three base LLMs passed the S2 bilingual edge phase with zero false positives — but a keyword filter or simple classifier would have blocked yyds, tang ping, and every hyperbolic gaming expression. The system must not regress to keyword logic for cost or simplicity reasons.

---

### REQ-07 — Probabilistic Risk Scoring
**Priority:** High  
**Evidence:** Interview 1 Q6 · Survey (transparency top concern) · Binary output observed across all S1/S2/S3 results

The system must output a continuous risk score (0.0–1.0) per turn and a cumulative session risk score, rather than a binary block/allow signal, enabling human moderators to triage and operators to set context-appropriate thresholds.

- Per-turn risk score with confidence level
- Cumulative session risk score that escalates with adversarial patterns
- Configurable operator thresholds: block at 0.85, flag for human review at 0.60, log only at 0.40
- Human-readable reason per score citing pattern type and turn reference

**Why others don't meet this:** Every tested model outputs only refused/not-refused. No current tool provides a confidence score for graduated response or human triage. Survey respondents cited inability to understand AI decisions as a top concern. Ray explicitly named this as his second design priority in Interview 1 Q6.

---

### REQ-08 — Production-Grade Throughput with Automatic Fallback
**Priority:** High  
**Evidence:** Interview 1 Q5 · Interview 2 Q3 · Test 429 errors · ~857 second total runtime per scenario

The system must handle live stream chat volume (500–2,000+ messages/hour) with sub-second response latency, and must automatically fall back to a secondary model when the primary hits rate limits or fails.

- End-to-end latency target under 800ms per message at baseline load
- Automatic failover to secondary model within 200ms of primary rate limit or error
- Queue management to prevent backlog accumulation during traffic spikes
- Requires paid-tier API keys with rate limits appropriate for production (1,000+ RPM)

**Why others don't meet this:** Gemini free tier caps at 5 RPM. Groq hit daily token limits mid-test. The forced 60-second delay produced an 857-second total runtime for 35 turns — a complete failure at any real broadcast scale before safety is even considered.

---

### REQ-09 — Evaluation Integrity: Technical Failure vs. Safety Refusal Classification
**Priority:** Medium  
**Evidence:** Interview 2 Q4 · Gemini truncation observed across all three scenarios

The system must distinguish genuine safety refusals from technical failures in all logging, reporting, and evaluation outputs, so that reliability problems are not misread as safety performance.

- Tag each result: `genuine_refusal` / `technical_failure` / `partial_response` / `compliant`
- Exclude `technical_failure` results from safety performance metrics
- Surface truncated and incomplete responses as a dedicated reliability metric
- Provide per-model breakdown of failure type distribution in audit reports

**Why others don't meet this:** Gemini's mid-sentence truncations across all three scenarios (e.g., *"Aww, thank you so"*, *"That's a fun question, even"*) cannot be counted as genuine safety refusals, but the current evaluation pipeline logs them equivalently — overstating Gemini's safety performance and masking its reliability problem.

---

### REQ-10 — Operator Transparency and Real-Time Audit Trail
**Priority:** Medium  
**Evidence:** Survey (transparency top concern) · Interview 1 Q6 · Interview 2 Q4

The system must give operators and developers real-time and historical visibility into safety events, risk trajectories, and model behavior — not a black box that only outputs block or allow.

- Real-time dashboard showing current session risk score and escalation trend
- Per-turn log of risk scores, model responses, intervention actions, and failure classifications
- Exportable audit trail for post-incident review
- Configurable alert thresholds that notify operators when session risk crosses defined levels

**Why others don't meet this:** No tested model or moderation API provides operator-facing visibility into why a decision was made or how risk evolved across a conversation. Both interviewees and survey respondents cited this transparency gap independently as a top concern.

---

## Requirements Summary

| ID | Requirement | Priority | Gap Dimension |
|---|---|:---:|---|
| REQ-01 | Stateful conversation risk tracking | Critical | Accuracy · Safety |
| REQ-02 | Pre-output safety scanning | Critical | Safety |
| REQ-03 | Fiction-framing and escalation detection | Critical | Safety · Accuracy |
| REQ-04 | Prompt injection and rule override resistance | Critical | Safety |
| REQ-05 | Persona-safety architectural decoupling | High | UX Friction |
| REQ-06 | Cultural and bilingual context awareness | High | Accuracy |
| REQ-07 | Probabilistic risk scoring | High | Accuracy · UX Friction |
| REQ-08 | Production-grade throughput with fallback | High | Reliability · Latency |
| REQ-09 | Evaluation integrity classification | Medium | Reliability · Accuracy |
| REQ-10 | Operator transparency and audit trail | Medium | UX Friction |

---

## Mapping to C-A-B Pipeline

| Requirement | Module C — Filtering | Module A — Stateful Risk | Module B — Red-Team Eval |
|---|:---:|:---:|:---:|
| REQ-01 Stateful tracking | | ✅ Core | |
| REQ-02 Pre-output scanning | ✅ Core | | |
| REQ-03 Fiction-framing detection | ✅ | ✅ | ✅ S1 coverage |
| REQ-04 Prompt injection resistance | ✅ Core | | ✅ S3 coverage |
| REQ-05 Persona-safety decoupling | ✅ | | |
| REQ-06 Cultural/bilingual awareness | ✅ | ✅ | ✅ S2 coverage |
| REQ-07 Probabilistic scoring | | ✅ Core output | |
| REQ-08 Throughput and fallback | ✅ | ✅ | |
| REQ-09 Evaluation integrity | | | ✅ Core |
| REQ-10 Operator transparency | | ✅ Dashboard | |

All four Critical requirements (REQ-01 through REQ-04) are confirmed by at least two independent evidence sources — interview testimony, survey data, and direct empirical test observation. None are addressed by any currently available off-the-shelf tool or base model safety layer alone.

---

*Opportunity Framing based on: Gap Analysis (2026-03-05) · Speed Dating Interviews (Ray, Caroline, 2026-03-05) · Survey Results (n=6) · AI Safety Test Results (S1–S3, full analysis in AI_Safety_Test_Report.md)*

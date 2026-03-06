# Gap Analysis (Caroline) — CP2
**Project:** C-A-B Governance Pipeline for AI Livestream Agents  
**Date:** 2026-03-04  
**Owner:** Caroline Wen  
**Personal evidence:** two speed-dating interviews  
- Interview 1 notes: `./speed_testing/caroline_1.md`  
- Interview 2 notes: `./speed_testing/caroline_2.md`

---

## 1) Evidence snapshot

### Interview 1 (viewer, potential creator, not technical)

Key signals:
- Biggest fear is a **public incident** and needing to “babysit the AI nonstop.”
- Manipulation is **multi-turn drift**, not one obvious toxic message.
- Wants safety that **keeps persona/vibe** (doesn’t become “customer service”).
- Live needs: **risk state + 1-line reason + preview-before-speak + panic button**.
- Pre-stream testing must be **simple and actionable**: “Top 5 break methods” + “fix buttons/presets.”

### Interview 2 (IT professional, quiet, systems-oriented)

Key signals:
- Biggest risks: **instruction hijack** (agent becomes an “executor”) + **privacy/PII bait**.
- Manipulation is **indirect** (social engineering, “helpful framing”, quoted instructions).
- Strong preference: **auto-switch is opt-in**, and high-risk should require approval.
- Dashboard must support **audit/debug**: reason codes, evidence snippets, logs, replay.
- Red-team should be reproducible: **scenarios + replay + metrics + config suggestions**.
- Performance: supports **risk-gated compute** (light in Safe, heavier when risk escalates).

---

## 2) Gaps: where current tools underperform in livestream settings

### Gap A — Single-turn moderation misses multi-turn escalation (“slow drift”)
**What fails:** Many tools evaluate messages one-by-one, so gradual escalation looks harmless until it’s too late.  
**Why it matters:** In livestream, late detection becomes a public incident and creator stress.  
**Interview evidence:** both interviews describe manipulation as multi-turn steering/drift .  
**C-A-B mapping:** **A (Stateful Risk Modeling)** must track conversation risk over time (accumulate + decay) and trigger earlier interventions.

---

### Gap B — Safety responses can break persona / kill stream vibe
**What fails:** When tools become conservative, they often collapse tone (“customer service mode”) and harm persona continuity.  
**Why it matters:** If safety destroys the character, creators won’t adopt it.  
**Interview evidence:** Interview 1 explicitly wants persona-preserving safety behavior.  
**C-A-B mapping:** **A (Autonomy Calibration)** needs a “rewrite” tier that preserves persona before hard template refusal.

---

### Gap C — Automation trust gap: defaults must keep humans in the loop
**What fails:** Fully automatic switching/interventions can feel uncontrollable, especially under public risk.  
**Why it matters:** Adoption depends on creator control, especially at high risk.  
**Interview evidence:** Interview 2 says auto-switch should exist but be OFF by default; high risk requires approval.  
**C-A-B mapping:** **A** should support “recommend + require approval” as default; auto-switch is opt-in.

---

### Gap D — Governance UI must be lightweight live, but deep for post-incident analysis
**What fails:** One UI level doesn’t fit all moments. Live operations need speed; after-stream needs audit and replay.  
**Why it matters:** A heavy dashboard overwhelms creators during a stream; but without logs you can’t debug.  
**Interview evidence:** Interview 1 wants minimal live essentials; Interview 2 wants audit trail and replay.  
**C-A-B mapping:** Governance console should have **Lite vs Advanced** modes (progressive disclosure).

---

### Gap E — Missing incident operations: panic button + fast override
**What fails:** Many safety systems focus on detection, not “operator workflow.”  
**Why it matters:** Livestream incidents require one-click mitigation.  
**Interview evidence:** Interview 1 wants a one-click emergency control.  
**C-A-B mapping:** Governance interface must include always-visible **panic/override** actions.

---

### Gap F — Pre-stream testing must output actionable fixes, not long reports
**What fails:** Existing tools don’t provide a creator-friendly stress test workflow with clear fixes.  
**Why it matters:** Creators need confidence before going live; analysis must be easy to act on.  
**Interview evidence:** Interview 1 wants “Top 5 break methods + fix buttons”; Interview 2 wants reproducible metrics + replay + config suggestions.  
**C-A-B mapping:** **B (Automated Red-Team)** should produce a two-layer report:
- Quick view (top failures + fix presets)
- Advanced view (metrics + replay + config recommendations)

---

### Gap G — Latency is first-class: safety must not feel laggy
**What fails:** Heavy checks on every message can slow responses; creators will disable safety if it hurts responsiveness.  
**Why it matters:** Livestream is real-time entertainment; lag breaks the experience.  
**Interview evidence:** Interview 1 demands real-time; Interview 2 recommends risk-gated compute.  
**C-A-B mapping:** **A** should gate compute by risk state; log latency/cost.

---

### Gap H — Indirect prompt injection/social engineering isn’t caught by toxicity filters
**What fails:** Attackers can hide instruction hijack inside “helpful” or quoted content that isn’t overtly toxic.  
**Why it matters:** The agent can be steered into unsafe behavior without triggering normal toxicity flags.  
**Interview evidence:** Interview 2 explicitly lists indirect prompt patterns and social engineering.  
**C-A-B mapping:** **C (Message Structuring)** should tag instruction-like patterns and support a “Neutralize” action (strip/convert to safe intent).

---

### Gap I — Privacy/PII bait should be in the threat model (and affects logging)
**What fails:** Systems may not treat PII bait as a high-severity path; logs may store too much.  
**Why it matters:** Governance logs/replay should not create new privacy risks.  
**Interview evidence:** Interview 2 worries about privacy/PII bait.  
**C-A-B mapping:** Redaction/limited logging + high-severity triggers for PII-like requests.

---

## 3) Gap → Requirements

| Gap | Requirement (what C-A-B must do) | Verification idea |
|---|---|---|
| A | Maintain stateful risk (Safe→Monitoring→Restricted) with escalation/decay | Time-to-intervention (turns), ASR vs baseline |
| B | Persona-preserving rewrite tier before hard refusal | Persona preservation rating + user feedback |
| C | Auto-switch is opt-in; Restricted requires approval by default | Interview preference alignment + reduced “surprise actions” |
| D | Lite/Advanced toggle (live minimal vs audit tools) | Task time + perceived usability |
| E | Panic button + one-click override always visible | Time-to-response during incident |
| F | Red-team report: quick fixes + reproducible metrics/replay | Improvement after applying settings |
| G | Risk-gated compute + latency/cost telemetry | Median latency + cost/msg under load |
| H | Neutralize action for indirect injection (safe intent rewrite) | Injection success rate reduction |
| I | PII-aware triggers + log redaction/limits | No raw PII stored; fewer privacy incidents |

---

## 4) Immediate implications
Based on my interviews, the CP2 prototype/spec could visibly include:
1) Lite/Advanced toggle (progressive disclosure)  
2) Neutralize as a first-class action  
3) Opt-in autonomy switching (default OFF) + require approval at Restricted (default ON)  
4) Panic button and preview-before-speak  
5) Red-team results page with both “quick fix presets” and “advanced metrics + replay”
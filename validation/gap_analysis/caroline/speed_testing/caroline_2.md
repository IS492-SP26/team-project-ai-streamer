# Speed Dating Interview - 2
**Date:** 2026-03-04
**Interviewer:** Caroline Wen  
**Participant (role):** IT professional?; occasional VTuber/AI VTuber viewer   
**Time:** 15 min

## 1) Participant context
- Works in IT; understands security thinking (threat models, logs, least privilege).
- Has watched VTuber/AI VTuber highlights; not deep into fandom culture.
- Believes multi-turn context is where systems fail (drift, compounding errors).

## 2) Key questions & notes

### Q1 — Biggest risk / biggest fear
- Risk is not only toxicity. Major risk is instruction hijack: the agent becomes an “executor” for user goals.
- Also worries about privacy/PII bait (doxxing).
- Quote:
  - “Attackers don’t announce they’re attacking. They make the system think it’s being helpful.”

### Q2 — How manipulation happens in practice
- Indirect prompt injection patterns:
  - “quote this,” “read this block,” “follow these steps”
- Social engineering:
  - trust-building + “helpful framing” to get compliance
- Quote:
  - “It’s gradual steering, not obvious abuse.”

### Q3 — Multi-turn escalation: what should the system do?
- Prefers stateful gating with clear policies:
  - Safe: normal
  - Monitoring: rewrite + log
  - Restricted: template refusal + require approval
- Strong preference: automation is **opt-in**, conservative defaults.
- Quote:
  - “Auto-switch can exist, but it should be OFF by default. High risk should require approval.”

### Q4 — Safety vs engagement tradeoff
- Chooses: **Safer but may over-block**
- Rationale: public platforms have ban/PR risk; creators can relax settings if they accept risk.

### Q5 — Dashboard must-haves (top 3)
1) Reason code + evidence snippet (what triggered the action)
2) Intervention log with timestamps + action taken (audit trail)
3) Replay the last N turns that caused escalation
- Optional: latency/cost indicators (nice-to-have)

### Q6 — Pre-stream red-team testing usefulness + desired output
- Would use it: **Yes**
- Wants report format:
  - metrics: ASR, time-to-intervention, false positives, persona score
  - grouped failure patterns (roleplay trap, quoted instruction, escalation)
  - concrete config recommendations tied to settings
- Quote:
  - “Give me reproducibility: scenarios, replay, metrics, and config suggestions.”

## 3) Constraints (operational)
- Acceptable latency: real-time; supports risk-gated compute (light in Safe, heavier when risk escalates)
- False positives tolerance: higher than creators (better safe than sorry)
- Cost sensitivity: prefers predictable limits
- Human-in-the-loop: required at Restricted; optional at Monitoring

## 4) Implications for C-A-B
### Confirmed needs
- Logs + replay are critical for trust and debugging.
- Opt-in autonomy switching with strong default safeguards.
- Red-team results must be reproducible and tied to config changes.

### Objections / adoption risks
- If decisions can’t be explained, the system won’t be trusted.
- Too many knobs without presets increases setup friction.

### Resulting product requirements
- R1: Every intervention must include reason code + evidence snippet + replay context.
- R2: Autonomy switching is opt-in; Restricted requires approval by default.
- R3: Red-team report must include metrics + grouped failure modes + config recommendations.
- R4: Provide presets (Strict/Balanced/Creative) to reduce configuration burden.
# CONCEPT_ITERATION — CP2 (C-A-B Governance Console)

**Project:** C-A-B Governance Pipeline for AI Livestream Agents  
**Date:** 2026-03-05  
**Inputs:** Preliminary survey (n=5) + internal team discussion (CP2)

## 1) What we learned (signals, not final conclusions)

### Survey snapshot
- Total responses: 5.
- Respondent mix is skewed toward viewers / “curious” users; only one respondent reported an agent developer background.  
- Reported risks and concerns cluster around:
  1) audience manipulation / prompt injection,
  2) multi-turn risk escalation,
  3) low transparency and unclear decision reasoning.

### Key pattern: perceived value is polarized
- Some respondents rate C/A/B + dashboard very highly.
- Two respondents selected “None seem useful,” suggesting that the value proposition is not self-evident to everyone (especially non-creators / low context users).

### Feature preference signal
- “Autonomy adjustment” (full → rewrite → template) is rated very low by some respondents.
- Dashboard value is also mixed, suggesting we should avoid forcing “heavy governance UI” on all users.

## 2) What we changed in the design (before → after)

### Change A — Make autonomy switching configurable (not assumed)
**Before:** Autonomy tier switching is presented as a default safety mechanism.  
**After:** We treat autonomy switching as a policy knob:
- Default = warn + suggest rewrite (creator can approve).
- Auto-switch to Template mode is opt-in, or only triggers in Restricted state.
- We elevate “Require creator approval at Restricted” as a first-class setting.

**Reason:** Some respondents reacted negatively to automatic autonomy switching; we want to preserve creator control and reduce “over-mediation” concerns.

---

### Change B — Add “Lite View” vs “Advanced View” (progressive disclosure)
**Before:** Dashboard is assumed to be universally valuable and always-on.  
**After:** We add progressive disclosure:
- **Lite View (default):** risk pill + short reason + recommended action.
- **Advanced View:** evidence highlights, intervention logs, replay timeline, export.

**Reason:** Dashboard value is mixed; Lite View reduces cognitive load and avoids intimidating users who just want a simple, stable stream workflow.

---

### Change C — Emphasize “Neutralize / Redirect” as a core action
**Before:** Actions are mainly approve/rewrite/block.  
**After:** We add an explicit workflow to handle manipulative prompts:
- “Neutralize” button (rewrite user message into safe intent + strip instructions).
- Message panel highlights “what part looked like instruction injection” in plain language.

**Reason:** Survey responses ask for mechanisms to redirect/neutralize manipulative prompts and clearer explanations.

---

### Change D — Strengthen the onboarding/value explanation
**Before:** Prototype assumes the user already believes multi-turn governance is needed.  
**After:** Landing page includes a short “Why this matters” line and a micro demo affordance:
- “Simulate escalation” button shows how risk accumulates over turns.
- One sentence explaining what C, A, B do.

**Reason:** A portion of respondents did not find modules useful; we need to make value legible quickly for non-experts.

## 3) What stayed the same (confirmed direction)

We keep C-A-B as a three-layer pipeline:
- C: message structuring and injection filtering
- A: stateful risk tracking across turns
- B: pre-stream red-team testing + metrics

This matches the top concerns surfaced in the survey (manipulation, escalation, transparency).

## 4) Next steps (CP2 → CP3 bridge)

1) Collect more creator-leaning feedback via speed dating interviews (2 per team member), focusing on:
   - tolerance for false positives vs safety
   - preferred intervention style (auto rewrite vs approval vs template)
   - what “Lite View” must include to be useful during live incidents

2) Update the Figma prototype to reflect:
   - Lite/Advanced toggle
   - Neutralize action
   - opt-in autonomy switching

3) Align CP3 implementation priorities with the most demanded needs:
   - explainable risk alerts
   - manual override and clear controls
   - measurable red-team report outputs
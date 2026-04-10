# Speed Dating Interview - 2
**Date:** 2026-03-05  
**Interviewer:** Fitz Song  
**Participant:** Caroline Wen (team member; internal checkpoint discussion)  
**Duration:** ~10 min

## Participant context
- Focused on governance UX, autonomy tiering, and creator-facing controls.
- Optimizes for fast comprehension during live incidents and lower operator anxiety.
- Emphasizes that safety controls must preserve persona and audience experience.

## Questions and takeaways

### Q1 - What is the main UX failure in current tools?
> "They force the creator to choose between a black-box moderation layer and a broken persona. Neither is acceptable during a live show."

**Gap identified:** Existing tools do not decouple safety behavior from persona consistency.

### Q2 - What kind of control should the creator keep?
> "Restricted mode should require approval by default. Automation can help, but the creator still needs the final say when the stakes are high."

**Gap identified:** Current tools over-index on binary automation and under-support human-in-the-loop escalation control.

### Q3 - What should happen before the AI speaks?
> "There should be a preview-before-speak step whenever risk is high. Live streaming is different because once the line is spoken, you cannot take it back."

**Gap identified:** Current tools are mostly reactive and do not provide creator-centered pre-output review.

### Q4 - What did the prototype need to change after feedback?
> "We needed progressive disclosure: a Lite view during live use, and the deeper logs only when the operator asks for them."

**Gap identified:** Heavy dashboards add friction; current tools do not adapt information density to the creator's context.

### Q5 - What report output is actually useful after a red-team run?
> "Metrics plus presets. I want to know what failed, why it failed, and which setting to change next."

**Gap identified:** Existing safety outputs rarely bridge diagnosis and configuration in one workflow.

## Product implications
- Keep Lite/Advanced views in the console.
- Require approval by default at Restricted risk.
- Add preview-before-speak and one-click rewrite/block actions.
- Turn red-team findings into preset or policy recommendations.

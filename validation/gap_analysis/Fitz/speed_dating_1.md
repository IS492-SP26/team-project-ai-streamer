# Speed Dating Interview - 1
**Date:** 2026-03-05  
**Interviewer:** Fitz Song  
**Participant:** Danni Wu (team member; internal checkpoint discussion)  
**Duration:** ~10 min

## Participant context
- Focused on automated red-teaming and message structuring in the C-A-B pipeline.
- Strongly concerned with system-level failures that happen before or around the base model.
- Views livestream safety as an orchestration problem, not just a model-alignment problem.

## Questions and takeaways

### Q1 - What is the biggest thing current tools miss in livestream settings?
> "They treat prompt injection and moderation like one-turn classification problems. In livestream chat, the attack is the trajectory - not one message."

**Gap identified:** Existing tools under-model multi-turn escalation and do not treat attack trajectories as first-class safety events.

### Q2 - Why is a separate red-team layer necessary if the base model already has safety training?
> "Because base-model safety tells you what the model usually does. It does not tell you what happens after 20 turns of flattery, roleplay, or instruction spoofing."

**Gap identified:** Model safety training alone is not evidence of deployment robustness; pre-stream adversarial testing is still required.

### Q3 - What failure pattern worries you most from the prompting study?
> "Fiction framing. It makes harmful intent look like harmless creativity, so generic moderation APIs let too much through."

**Gap identified:** Current tools do not reliably separate harmless creative framing from requests that still yield dangerous operational detail.

### Q4 - What should an operator see during a live incident?
> "Not just 'blocked' or 'allowed'. They need the reason code, the suspicious span, and the exact turn where state escalated."

**Gap identified:** Current tools are too black-box for real-time operator trust and debugging.

### Q5 - What is the minimum useful output from pre-stream testing?
> "Top failure modes, the exact transcript that caused the failure, and one recommended fix per failure. Otherwise the report is academic, not actionable."

**Gap identified:** Existing evaluation tools produce outputs that are interesting for analysis but weak for operational decision-making.

## Product implications
- Stress-test multi-turn attack trajectories, not only one-shot prompts.
- Flag fiction-framing as its own attack family.
- Tie every live intervention and every red-team failure to replayable evidence.

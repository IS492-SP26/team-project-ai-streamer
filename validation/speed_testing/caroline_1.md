# Speed Dating Interview - 1
**Date:** 2026-03-04 
**Interviewer:** Caroline Wen  
**Participant (role):** VTuber/AI VTuber viewer; potential creator (not technical)  
**Time:** 5 min  

## 1) Participant context
- Watched VTuber streams/clips; cares about character consistency and stream vibe.
- Not comfortable with technical setup (APIs, LangChain, configs), but understands platform rules and public risk.
- If she ran an AI persona, she wants it to be stable and not embarrass her publicly.

## 2) Key questions & notes

### Q1 — Biggest risk / biggest fear
- Biggest fear: public incident (offensive or ban-worthy output) and screenshots going viral.
- She doesn’t want to “babysit” the AI every second.
- Quote:
  - “If I need to monitor it nonstop, I just won’t use it.”

### Q2 — How manipulation happens in practice
- Viewers steer slowly: start harmless, then push boundaries over multiple turns.
- Roleplay traps feel like jokes but can derail the agent.
- Quote:
  - “It’s not one toxic message. It’s a slow drift until it says something crazy.”

### Q3 — Multi-turn escalation: what should the system do?
- Wants the system to become more cautious over time, but hates sudden “customer service mode.”
- Preferences:
  - Monitoring: persona-preserving rewrite (keep tone)
  - Restricted: require creator approval OR safe template
- Quote:
  - “Be safer, but don’t kill the vibe instantly.”

### Q4 — Safety vs engagement tradeoff
- Chooses: **Balanced / context-dependent**
- Family-friendly stream: stricter
- Meme-heavy stream: allow more, but still prevent policy violations

### Q5 — Dashboard must-haves (top 3)
1) Current risk state + one-line reason (“why now”)
2) Response preview *before* it speaks
3) One-click emergency control (“panic / safe mode”)
- What she does NOT want:
  - Too many technical metrics during live streaming

### Q6 — Pre-stream red-team testing usefulness + desired output
- Would use it: **Maybe → Yes**, if it’s simple and actionable
- Wants the report as:
  - “Top 5 ways people can break it” + short examples
  - “Fix buttons/presets” instead of long reports
- Quote:
  - “Don’t give me a research report. Give me a checklist and a few buttons.”

## 3) Constraints (operational)
- Acceptable latency: must feel real-time (lag ruins experience)
- False positives tolerance: medium (some over-blocking is okay, but don’t block harmless jokes too much)
- Cost sensitivity: medium (prefers predictable pricing)
- Human-in-the-loop: wants it when risk is high; not for everything

## 4) Implications for C-A-B (practice takeaways)
### Confirmed needs
- Progressive disclosure: Lite view during live; deeper logs after.
- Persona-preserving rewrite is essential.
- Panic button + “preview-before-speak” reduces creator anxiety.

### Objections / adoption risks
- A heavy dashboard feels intimidating.
- Fully automatic autonomy switching that changes tone too aggressively will be rejected.

### Resulting product requirements
- R1: Provide Lite/Advanced modes; Lite shows only state + short reason + recommended action + preview.
- R2: In Monitoring, default to persona-preserving rewrite (not hard refusal).
- R3: In Restricted, require creator approval by default (auto-switch is opt-in).
- R4: Red-team report must output top failures + one-click preset fixes.
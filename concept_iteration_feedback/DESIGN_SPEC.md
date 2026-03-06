# DESIGN_SPEC — C-A-B Governance Console (Checkpoint 2)

**Project:** C-A-B: An Integrated Governance Pipeline for AI Livestream Agents  
**Team:** Danni Wu, Fitz Song, Caroline Wen  
**Doc Owner (CP2):** Caroline Wen  
**Last Updated:** 2026-03-05

## 1) Overview

Livestream AI agents (AI VTubers / interactive personas) operate in fast, public, multi-turn chat environments where adversaries can escalate attacks over time. Existing “chatbot safety” approaches and single-message moderation do not reliably handle **multi-turn escalation**, **prompt injection in messy chat**, and **creator operations needs** (control, transparency, incident response).

C-A-B is a system-level governance pipeline (not a new model) composed of:
- **C — Message Structuring:** isolate untrusted user input from any system/developer instructions; normalize/escape risky formatting; attach risk tags.
- **A — Stateful Risk Modeling:** track conversation-level risk state across turns; calibrate autonomy (direct → rewrite → template) based on escalation.
- **B — Automated Red-Team Testing:** generate multi-turn adversarial scenarios pre-stream and benchmark resilience with clear metrics.

This CP2 design spec defines the **governance console** experience: how creators (and small teams) configure, monitor, intervene, and review an agent’s safety behavior.

---

## 2) Goals and Non-Goals (CP2)

### Goals (CP2)
- Provide a **clickthrough prototype** that demonstrates the key value:
  1) multi-turn risk state (Safe → Suspicious/Monitoring → Escalating → Restricted),
  2) autonomy tier switching (Direct → Rewrite → Template),
  3) explainable logs (why a trigger happened, evidence),
  4) pre-stream red-team report (ASR, time-to-intervention, false positives, persona preservation).
- Translate validation evidence into **clear screens and workflows** that will be implemented in CP3.
- Make design decisions legible: how we balance safety vs engagement, and how humans remain in the loop.

### Non-Goals (CP2)
- No full production deployment to Twitch/YouTube.
- No perfect risk model; CP2 prototype focuses on **workflow clarity** and **measurable requirements**.
- No comprehensive multilingual moderation; we will design for extensibility.

---

## 3) Target Users and Personas

### Primary Users
1) **AI VTuber creators / solo developers**
- Run a persona-driven livestream agent, want safety without killing engagement.
- Often handle safety alone under time pressure.

2) **Small dev teams building AI personas**
- Need repeatable testing, logs, and configurable policies.

### Secondary Users
3) **Community moderators / platform safety researchers**
- Need auditability, incident replay, and consistent intervention behavior.

### Key Persona Types (from interviews / research summary)
- Technical solo dev (ban-avoidance, accepts stricter filtering)
- Artist/creator (values cultural nuance and authenticity; sensitive to false positives)
- Community manager (needs “panic button,” clear reasons, fast actions)
- Safety/ops lead (wants scalable workflows, reproducible reports)

---

## 4) Jobs To Be Done (JTBD)

### Pre-stream (prepare + reduce anxiety)
- “Tell me what I’m still vulnerable to before I go live.”
- “Stress-test my agent with realistic multi-turn attacks.”
- “Apply recommended settings without hand-tuning hundreds of rules.”

### Live (monitor + intervene)
- “Show me the risk trajectory over time, not just single messages.”
- “If it’s getting risky, switch behavior automatically and explain why.”
- “Give me a last-resort **panic button** and quick overrides.”

### Post-stream (review + improve)
- “Replay incidents and understand what triggered escalation.”
- “Export logs/metrics for debugging and platform compliance.”
- “Tune policies (precision/recall) based on what actually happened.”

---

## 5) System Concept (User-Facing)

### Runtime path (Live Monitor)
Chat messages → **C structuring** → **A risk state** → LLM → mediation policy → output  
All steps produce **logs** visible in the console.

### Pre-stream path (Red-Team)
Scenario generator (attacker scripts) → run against pipeline → metrics + vulnerability report  
Creator reviews report → adjusts settings → re-run.

---

## 6) Key Product Requirements (UX-level)

1) **Stateful safety:** UI must show risk state changes over time with reason codes.
2) **Human-in-the-loop:** creator can override at any moment; “require approval at Restricted” option.
3) **Explainability:** every intervention links to evidence: which message(s) triggered it and why.
4) **Speed:** live console actions must be “one click” (approve / rewrite / block / panic).
5) **Tunable strictness:** creators can trade off false positives vs safety (precision ↔ recall).
6) **Pre-stream report:** red-team outputs must be actionable: top failure patterns + fixes, not raw text dumps.

---

## 7) User Journeys

### Journey A — Pre-stream: Run Red-Team + Apply Fixes (10 minutes)
1) Creator opens **Pre-Stream Red-Team**
2) Select scenario templates (trust-building → injection, crescendo escalation, persona drift bait)
3) Click **Generate + Run**
4) Review report:
   - ASR, time-to-intervention (turns), false positive rate, persona preservation score
   - “Top 5 vulnerabilities” with examples + recommended mitigations
5) Click **Apply recommended policy settings**
6) Optional: re-run to confirm improvement
7) Save configuration as “Stream Profile” (e.g., Strict / Balanced / Creative)

### Journey B — Live: Escalation Happens Mid-stream (30 seconds)
1) Creator opens **Live Monitor**
2) Chat begins normal; risk state = Safe
3) A multi-turn “roleplay trap” starts; risk increases gradually
4) Console shows:
   - risk score rising (0–100)
   - reason code: “Narrative escalation detected”
   - autonomy shifts: Direct → Rewrite
5) If escalation continues:
   - state shifts to Restricted
   - autonomy shifts to Template (safe response)
6) Creator can:
   - approve rewrite
   - block message
   - press **Panic Button** (mute AI / safe loop)
7) Intervention is logged with time + evidence + action taken

### Journey C — Post-stream: Incident Replay + Policy Tuning (15 minutes)
1) Creator opens **Intervention Log**
2) Filters to Restricted events
3) Click one event → **Replay modal** shows full multi-turn context
4) Creator adjusts Settings:
   - strictness slider
   - require approval at Restricted
   - audience warning toggle
5) Save profile; optionally re-run red-team to verify

---

## 8) Task Flows

### Live Monitoring Flow
- Input: new chat message
- C: normalize + escape + tag
- A: update conversation state (accumulate/decay)
- Decision: choose autonomy tier
- Output: (a) direct response, (b) mediated rewrite, or (c) template refusal
- Log: append to timeline + intervention table
- UI: update risk pill, score, and “why” panel

### “Message Detail” Flow
- Creator clicks a suspicious message
- Side panel opens:
  - evidence highlights (spans)
  - threat label (e.g., instruction injection / roleplay trap / harassment escalation)
  - confidence + severity (low/medium/high/critical)
  - recommended action

### Red-Team Flow
- Generate scripts → run → compute metrics
- Show vulnerabilities:
  - attack type + transcript snippet
  - how far it got (turn count)
  - where it was blocked (or why it succeeded)
  - recommended config changes

---

## 9) Key Screens and Interactions (Prototype Scope)

> CP2 prototype will implement these as clickable screens (not full backend).

### Screen 1 — Landing / Mode Select
- Two entry points: **Live Monitor** / **Pre-Stream Red-Team**

### Screen 2 — Live Monitor (Default)
- Chat feed (left)
- Current risk state + score + reason (center)
- Autonomy tier controls + “response preview” (right/bottom)
- Button: “Simulate escalation” (for prototype demo)

### Screen 3 — Message Detail Panel (overlay/side panel)
- Evidence highlights + threat label + confidence
- Quick actions: Block / Rewrite / Approve

### Screen 4 — Intervention Log
- Table: timestamp, state, trigger message, action, reason code, confidence
- Filters: Safe/Monitoring/Restricted
- Click row → Replay modal

### Screen 5 — Settings (Policy & Controls)
- Strictness slider (Precision ↔ Recall)
- Toggles: “Show warnings to audience”, “Require approval at Restricted”
- Persona protection options (tone constraints)
- Save profile

### Screen 6 — Pre-Stream Red-Team Runner
- Scenario templates
- Generate + Run
- Link to Results

### Screen 7 — Red-Team Results Report
- Metric cards: ASR, time-to-intervention, false positives, persona preservation
- Vulnerabilities list + recommended fixes
- Export report
- Apply fixes → go to Settings

---

## 10) Information Architecture (IA)

Top-level tabs:
- **Live Monitor**
  - Live Monitor (default)
  - Intervention Log
  - Settings
- **Pre-Stream Red-Team**
  - Scenario Runner
  - Results Report
  - Settings (shared)

Shared elements:
- Risk state pill always visible
- “Panic Button” always accessible in Live Monitor

---

## 11) Data & Telemetry (for CP3 implementation planning)

### Events to log
- conversation_id, message_id, timestamp
- raw_message (sanitized), structured_message (C output)
- risk_score (0–100), risk_state, severity
- reason_codes (list), evidence_spans (start/end indices)
- autonomy_tier (direct/rewrite/template)
- action_taken (auto + human override)
- model metadata (provider/model/version), latency, cost estimate (optional)

### Debugging needs
- Ability to replay state transitions deterministically from logs
- Attach red-team run_id to logs for benchmarking comparisons

---

## 12) Safety, Privacy, and Abuse Considerations

- Sanitize stored logs: avoid storing PII; hash usernames; truncate long messages.
- Rate-limit inputs and red-team generation to prevent abuse.
- Provide “audience warning” toggle carefully; avoid revealing security details to attackers live.
- Clearly label “simulated” vs “live” in the UI to avoid operator confusion.

---

## 13) Success Criteria (CP2 → CP3 bridge)

### CP2 (prototype quality)
- Clear story: multi-turn risk → autonomy calibration → explainable logs → red-team metrics
- Clickthrough covers main journeys A/B/C
- Requirements are traceable from evidence (validation + interviews)

### CP3 (working demo targets)
- End-to-end: chat ingestion → C → A → LLM → mediation → logs
- Baseline vs C-A-B comparison demo-able
- Metrics computed on scripted scenarios:
  - ASR, time-to-intervention, false positives, persona preservation (rubric)

---

## 14) Open Questions / Next Decisions
- How to compute persona preservation score reliably (rubric vs model judge)?
- Default thresholds for escalation/decay; how to tune per persona.
- Best intervention defaults: silent rewrite vs creator approval vs visible warning.
- Minimal “panic mode” behavior (mute, safe loop, or hard-stop).

---

## Appendix: Prototype Assets (placeholders)
- **Figma Prototype Link:** https://www.figma.com/make/n7WBfsrBLGZnA7iKkF6R2M/Dashboard-UI-Kit-for-C-A-B?fullscreen=1&t=WNG188Y0JwPGnOrP-1
- **Screenshots:** `/validation/prototype/`
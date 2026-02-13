https://canvas.illinois.edu/courses/64886/pages/team-project-instructions-4-check-points
https://canvas.illinois.edu/courses/64886/discussion_topics/1075469

PPT link: https://docs.google.com/presentation/d/1h8GQLqgY-Ety_Xa1QWJT5ztmHAUtH6UDSk6nKjsvMLU/edit?usp=sharing

# C-A-B: An Integrated Governance Pipeline for AI Livestream Agents
Team Member: Danni Wu, Fitz Song, Caroline Wen

This repository implements a three-layer research prototype (C-A-B) designed to operationalize security and governance mechanisms for AI agents operating in high-tempo, adversarial livestream chat environments. Rather than proposing a new model architecture, this project focuses on system-level integration: translating ideas from prompt-injection defense, guardrails, and automated red-teaming into a deployable and evaluable pipeline for livestream contexts, which is a system-level integration and evaluation framework tailored to adversarial, multi-turn livestream environments.

---

# 🧠 Problem Statement and Why It Matters

Current LLM safety research is largely chatbot-centric, focusing on isolated prompt–response interactions. Livestream environments, however, involve continuous, multi-turn conversational trajectories under public visibility and adversarial pressure. Research shows that multi-turn adversarial interactions are significantly more effective than single-turn prompts, as safety guardrails weaken across extended dialogue. At the same time, increasing agent autonomy expands the potential risk surface when systems operate in open domains.

This creates a deployment gap in AI livestream settings:
- Existing defenses are often evaluated in static or developer-controlled contexts.
- Livestream chat is unstructured, fast-moving, and culturally situated.
- Multi-turn escalation is common and difficult to detect with single-message moderation.

The core challenge is not only filtering harmful content, but modeling conversational risk over time and calibrating autonomy accordingly. This project addresses that gap by implementing a structured, stateful, and evaluable governance pipeline tailored to adversarial livestream environments.

---

# 👥 Target Users and Core Tasks

## Target Users

Primary: AI VTuber creators，small development teams building autonomous digital personas

Secondary: AI entertainment startups，streaming platform safety researchers

## Core Tasks

1. Contextual Message Structuring (C)
Automatically structure raw livestream chat messages and isolate untrusted user content from internal system instructions. This module applies rule-based filtering and LLM-assisted parsing to reduce prompt injection risks in unstructured chat streams.

2. Stateful Risk Modeling (A)
Maintain a conversation-level risk state rather than evaluating each message independently. The system implements an interpretable finite-state escalation model that tracks risk accumulation across turns and dynamically adjusts mediation policies.

3. Automated Red-Team Evaluation (B)
Use LLM-driven multi-turn adversarial scenario generation to stress-test the system. This module benchmarks resilience under sustained conversational pressure and produces quantitative evaluation metrics.

4. Governance Interface
Provide visibility into system decisions, risk levels, mediation triggers, and intervention logs to support human oversight.

---

# 📊 Competitive Landscape

| System Type | What It Does Well | Gaps for Livestreaming |
| :--- | :--- | :--- |
| **Prompt Injection Defense Research (e.g., structured separation approaches)** | Separates instructions from data in structured applications; effective in controlled environments. | Assumes developer-controlled inputs; not directly adapted to open, multi-turn livestream dialogue; lacks integrated deployment pipelines. |
| **AI VTuber SDKs / Agent Frameworks** | Strong real-time integration (TTS, avatar rendering, game engines); supports autonomous interaction loops. | Focused on capability and immersion; limited stateful risk modeling; minimal governance-oriented mediation layers. |
| **Raw LLM + Moderation APIs** | Easy integration; strong general reasoning; standardized toxicity filtering. | Moderation is typically single-message and reactive; limited multi-turn escalation modeling; no autonomy calibration mechanism. |
| **C-A-B System (This Project)** | Integrates structuring, stateful modeling, and automated red-team evaluation into one coherent pipeline. | Research prototype; requires integration with specific livestream front-ends for deployment. |

---

# 🏗 Initial Concept and System Architecture

The C-A-B architecture separates concerns into three modules:

1. Input → C (Message Structuring)
User messages are parsed and structured. Untrusted user content is isolated from system-level instructions through rule-based filtering and LLM-assisted classification. Risk tags are generated for downstream processing.

2. C → A (Stateful Risk Engine)
The system maintains a conversation-level risk state implemented as an interpretable finite-state model. Risk accumulates or de-escalates based on recent interaction patterns. The current state determines the autonomy policy (e.g., direct generation, mediated rewrite, restricted response).

3. A → LLM → Mediation
The structured input is passed to the LLM. Outputs may be mediated (e.g., persona-aware rewrite) depending on the active autonomy tier.

4. Logs → B (Automated Red Team)
Interaction logs feed into an automated red-team harness. An attacker model generates multi-turn adversarial scripts, which are evaluated against the pipeline to measure attack success rate, time-to-intervention, and false positives.

The contribution of this project lies in integrating these modules into a reproducible, evaluable governance pipeline tailored to adversarial livestream environments.

---
## Project Milestones
# 📅 Milestones & Roles

## Milestone 1: System Design & Infrastructure Setup (Week 1–2)
- Finalize C-A-B architecture design
- Define risk states and autonomy tiers
- Set up LLM API integration and logging framework
- Implement baseline system (LLM + single-turn moderation API)

Owner:
- System & Backend Lead (Infrastructure + baseline pipeline)
- All members (architecture review)

---

## Milestone 2: Module C – Message Structuring & Injection Filtering (Week 3–4)

- Implement rule-based instruction/data separation
- Design delimiter and escape-character filtering logic
- Add LLM-assisted classification for suspicious prompts
- Output structured message format for downstream modules

Owner:
- Message Structuring Lead (Module C)
- Backend Lead (integration with main pipeline)

Deliverable:
- Structured message parser integrated into baseline system

---

## Milestone 3: Module A – Stateful Risk Modeling & Autonomy Calibration (Week 5–6)

- Design finite-state escalation model (e.g., Safe → Suspicious → Escalating → Restricted)
- Implement conversation-level state tracking
- Define risk accumulation and decay rules
- Map risk states to mediation tiers (direct pass-through / mediated rewrite / restricted template)
- Implement autonomy calibration logic

Owner:
- Stateful Governance Lead (Module A)
- Backend Lead (policy integration)

Deliverable:
- Fully working C → A → LLM → Mediation pipeline

---

## Milestone 4: Module B – Automated Red-Team Harness (Week 7–8)

- Develop LLM-based multi-turn adversarial script generator
- Design adversarial scenario templates (e.g., escalation, trust-building, indirect injection)
- Implement automated evaluation loop
- Define evaluation metrics:
  - Attack Success Rate (ASR)
  - Time-to-Intervention
  - False Positive Rate
  - Persona Preservation Score

Owner:
- Automated Evaluation Lead (Module B)
- Governance Lead (metric validation)

Deliverable:
- Automated adversarial testing pipeline

---

## Milestone 5: Final Evaluation & Demo Preparation (Week 9–10)

- Benchmark baseline vs. C-A-B system
- Run controlled multi-turn adversarial experiments
- Analyze performance trade-offs (safety vs. responsiveness)
- Prepare livestream-style demo scenario
- Conduct small usability test (if feasible)

Owner:
- All team members
- Evaluation Lead (experiment analysis)
- UX Lead (demo flow + presentation material)

Deliverable:
- Final comparative results
- Recorded demo showcasing system behavior under attack

## Team Roles
Message Structuring Lead (Module C)  
Designs parsing logic, instruction isolation rules, and risk tagging.

Stateful Governance Lead (Module A)  
Implements the escalation model, autonomy calibration logic, and mediation policies.

Automated Evaluation Lead (Module B)  
Develops red-team generation scripts, evaluation metrics, and benchmarking experiments.



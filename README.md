https://canvas.illinois.edu/courses/64886/pages/team-project-instructions-4-check-points
https://canvas.illinois.edu/courses/64886/discussion_topics/1075469

# Autonomy-Calibrated Governance for AI Livestream Agents
- Team Member: Danni Wu, Fitz Song, Caroline Wen

This project develops a research prototype that explores autonomy calibration and governance mechanisms for AI-driven livestream agents operating in open public environments. Rather than building another chatbot or VTuber engine, we focus on designing a governance layer that sits between a Large Language Model (LLM) and a livestream interface.

## 🧠 Problem Statement and Why It Matters
AI livestream agents—such as AI VTubers and autonomous digital personas—operate in environments that differ fundamentally from traditional chatbot settings. Livestream contexts are **real-time**, **public**, and **highly dynamic**. Audience interactions unfold over extended multi-turn conversations, often shaped by platform-specific slang, emotes, and financially incentivized prompts. These environments introduce reputational and platform-level risks that do not exist in closed, developer-controlled applications.

Recent research in LLM security shows that **multi-turn adversarial interactions are significantly more effective than single-turn attacks**, as models struggle to maintain safety guardrails across extended dialogue. At the same time, governance and agent literature highlights a structural pattern: as systems become more autonomous, the **risk surface expands**.

This creates a core tension between:
- **Autonomy**, which enables personality, improvisation, and engagement  
- **Safety**, which requires constraint, mediation, and oversight  

Most existing defenses assume structured input formats or developer-controlled contexts. These assumptions do not hold in open livestream chat, where inputs are:
- Unstructured natural language  
- Culturally situated (e.g., evolving emotes and slang)  
- Continuously interactive and multi-turn  

As a result, creators face a practical tradeoff. Restricting autonomy preserves safety but reduces expressiveness. Allowing greater autonomy increases engagement but raises the risk of adversarial steering, policy violations, or persona breakdown. We therefore frame this as an **autonomy calibration problem**. The challenge is not merely filtering harmful content, but dynamically adjusting the level of autonomy an AI agent is granted in response to contextual risk. This matters now because AI agents are transitioning from passive tools to semi-autonomous actors, livestream-based AI personas are increasing in scale and visibility, and accessible governance mechanisms remain underdeveloped for non-expert creators operating in adversarial public environments.

## 👥 Target Users and Core Tasks

### Primary Users
- AI VTuber creators, Small development teams building autonomous digital personas, AI entertainment startups
### Secondary Stakeholders
- Streaming platforms(Twitch, YouTube), Moderation team, Audiences interacting with AI agents  

### Core Tasks

1. Safe Deployment in Open Environments  
Deploy an AI agent that can interact with unpredictable audiences without leaking system instructions or generating harmful content.

2. Autonomy Calibration  
Adjust the level of mediation applied to model outputs in real time. In this prototype, autonomy refers to the degree of response mediation (direct pass-through, persona-aware rewrite, or restricted template).

3. Real-Time Monitoring and Intervention  
Provide visibility into risk scores and system decisions, and allow human operators to intervene when necessary.

## 📊 Competitive Landscape

| System Type | What It Does Well | UX Limitations | Reliability & Safety Gaps | Scope Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Raw LLM + Moderation APIs** | Strong general reasoning and instruction following; provides standardized toxicity filtering; easy integration through existing APIs. | Moderation decisions are typically binary (allow/block); limited transparency into decision logic; no built-in creator-facing governance interface. | Multi-turn interactions can weaken safety guardrails; moderation and generation often occur sequentially, increasing latency; no mechanism for dynamic autonomy adjustment. | Designed for general-purpose chat applications; not optimized for adversarial, high-volume livestream contexts; limited handling of platform-specific cultural signals (e.g., emotes, slang). |
| **AI VTuber SDKs / Agent Frameworks** | Strong real-time integration (TTS/STT, avatar rendering, game engines); supports continuous autonomous interaction loops; enables multimodal sensing and action. | Primarily developer-oriented; limited tools for non-expert creators to monitor or adjust system behavior; governance features are secondary to capability features. | Safety controls often rely on static rules or keyword filters; limited protection against sustained adversarial steering; high autonomy without structured mediation layers. | Focused on performance and immersion rather than accountability frameworks; lack standardized mechanisms for autonomy calibration in adversarial public environments. |
| **Prompt Injection Defense Research (e.g., structured query approaches)** | Clear separation between system instructions and user data in structured settings; demonstrates strong resilience in controlled benchmark environments; maintains task performance under tested conditions. | Assumes structured or developer-controlled inputs; not directly compatible with open, natural-language livestream dialogue; no real-time oversight interface for creators. | Primarily evaluated on static or single-turn benchmarks; limited treatment of adversarial escalation across extended multi-turn interactions. | Designed for programmatic applications (e.g., summarization, task agents) rather than persona-driven, publicly interactive livestream systems. |


## 🏗 Initial Concept and Value Proposition

We propose an Autonomy-Calibrated Orchestrator as a research prototype.

The system sits between the livestream chat and the LLM and includes:

1. Risk Scoring Layer  
Aggregates multiple signals (rule-based checks, moderation API outputs, and LLM-based evaluation) to produce a contextual risk score.

2. Persona-Aware Mediation  
When risk is elevated, the system rewrites or restricts outputs while preserving stylistic consistency.

3. Autonomy Slider  
Allows operators to adjust mediation thresholds in real time, shifting between direct generation, mediated generation, and restricted responses.

4. Decision Telemetry Dashboard  
Displays risk components, mediation decisions, and intervention logs to support human oversight.

This project does not claim to eliminate prompt injection. Instead, it explores how calibrated autonomy and transparent governance mechanisms can reduce risk while maintaining engagement.


## 🗺 Milestones and Roles

### Checkpoint 1
Problem framing and literature synthesis.

### Checkpoint 2
Prompt-based validation of risk scoring and mediation strategies using curated adversarial scenarios.

### Checkpoint 3
Implementation of a working prototype including:
- Risk scoring module  
- Autonomy slider  
- Mediation pipeline  
- Basic dashboard interface  

### Checkpoint 4
Evaluation including:
- System-level performance analysis  
- Controlled usability testing  

### Team Roles

Safety & Risk Modeling Lead  
Designs and implements the risk scoring and mediation logic.

System & Backend Orchestration Lead  
Builds the middleware layer and integrates LLM APIs and streaming inputs.

Interface & Governance UX Lead  
Designs the autonomy slider and decision telemetry dashboard.


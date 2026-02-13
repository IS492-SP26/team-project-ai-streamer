https://canvas.illinois.edu/courses/64886/pages/team-project-instructions-4-check-points
https://canvas.illinois.edu/courses/64886/discussion_topics/1075469
# team-project-ai-streamer
team-project-ai-streamer created by GitHub Classroom

# Autonomy-Calibrated Governance for AI Livestream Agents
- Team Member - Danni Wu, Fitz Song, Caroline Wen
This project develops a research prototype that explores autonomy calibration and governance mechanisms for AI-driven livestream agents operating in open public environments.

Rather than building another chatbot or VTuber engine, we focus on designing a governance layer that sits between a Large Language Model (LLM) and a livestream interface.


## Problem Statement and Why It Matters

AI livestream agents (e.g., AI VTubers or autonomous digital personas) operate in environments that are:

- Real-time and public  
- Multi-turn and highly dynamic  
- Influenced by financially incentivized prompts  
- Shaped by platform-specific slang and emotes  
- Subject to reputational and platform-level risk  

Recent LLM security research shows that multi-turn attacks are significantly more effective than single-turn prompts. At the same time, governance and agent literature highlights that increasing autonomy increases systemic risk.

Most existing solutions assume structured input or developer-controlled settings. These assumptions do not hold in livestream contexts.

Creators today face a tradeoff:

- Restrict autonomy to ensure safety, reducing personality and engagement  
- Allow autonomy and risk adversarial steering or policy violations  

We frame this as an autonomy calibration problem:

How can AI livestream agents dynamically adjust their level of autonomy in adversarial public environments while preserving persona consistency and audience engagement?

This matters now because:

- AI agents are moving from tools to semi-autonomous actors  
- Livestream AI personas are increasing in scale and visibility  
- Prompt injection vulnerabilities remain unresolved in real-world deployments  
- Non-expert creators lack accessible governance tools  


## Target Users and Core Tasks

### Primary Users

- AI VTuber creators  
- Small development teams building autonomous digital personas  
- AI entertainment startups  

### Secondary Stakeholders

- Streaming platforms  
- Moderation teams  
- Audiences interacting with AI agents  

### Core Tasks

1. Safe Deployment in Open Environments  
Deploy an AI agent that can interact with unpredictable audiences without leaking system instructions or generating harmful content.

2. Autonomy Calibration  
Adjust the level of mediation applied to model outputs in real time. In this prototype, autonomy refers to the degree of response mediation (direct pass-through, persona-aware rewrite, or restricted template).

3. Real-Time Monitoring and Intervention  
Provide visibility into risk scores and system decisions, and allow human operators to intervene when necessary.

### Definition of Success

- The agent maintains a consistent persona  
- High-risk prompts are detected and mediated  
- Human operators retain meaningful oversight  
- Audience engagement is preserved without policy violations  


## Competitive Landscape

### Raw LLM + Moderation APIs

Strengths:
- Easy to integrate  
- High language capability  

Limitations:
- Moderation is often reactive rather than contextual  
- Does not address multi-turn adversarial escalation  
- No autonomy calibration interface  

### Existing AI VTuber SDKs (e.g., Neuro SDK, Zerolan)

Strengths:
- Strong integration with game engines and avatars  
- Real-time interaction pipelines  

Limitations:
- Focused on capability rather than governance  
- Lack standardized mediation layers  
- No built-in autonomy control mechanism  

### Prompt Injection Defense Research (e.g., structured query approaches)

Strengths:
- Strong separation of instruction and data in structured systems  
- Theoretically robust against certain injection patterns  

Limitations:
- Assumes developer-controlled structured inputs  
- Not directly applicable to open chat livestream environments  
- Does not provide creator-facing governance interfaces  


## Initial Concept and Value Proposition

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


## Milestones and Roles

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


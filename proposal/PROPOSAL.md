# C-A-B: An Integrated Governance Pipeline for AI Livestream Agents

## 1. Problem & Importance
The deployment of Large Language Models (LLMs) in public-facing autonomous roles, such as AI VTubers and interactive livestream agents—introduces risks that traditional safety benchmarks do not fully capture. Most current LLM safety evaluations focus on static, single-turn prompt–response interactions. In contrast, livestream environments involve continuous, multi-turn conversations under public visibility and adversarial pressure.

Recent research demonstrates that multi-turn adversarial strategies are significantly more effective than single-turn attacks, as harmful intent can be introduced gradually through conversational escalation (Belaire et al., 2025; Anonymous, 2024). At the same time, increasing agent autonomy expands the potential risk surface, especially when creators rely on AI systems to manage high-volume, real-time interactions.

This creates a deployment gap: while guardrail techniques and injection defenses are actively studied, there is limited work translating these ideas into system-level governance pipelines tailored for adversarial, multi-turn livestream contexts. The core challenge is not only filtering harmful content, but modeling conversational risk over time and dynamically calibrating agent autonomy.

---

## 2. Prior Systems & Gaps
Several lines of research address components of this problem, yet gaps remain at the system-integration level:
- **Automatic LLM Red Teaming (Belaire et al., 2025):**  
  Reframes red teaming as a multi-turn, trajectory-based process and demonstrates the effectiveness of escalation strategies.  
  **Gap:** Focuses primarily on attack generation rather than deployable runtime governance mechanisms.

- **Design Patterns for Securing LLM Agents (Beurer-Kellner et al., 2025):**  
  Proposes architectural patterns (e.g., instruction/data separation, plan-then-execute) to reduce injection risk.  
  **Gap:** Many patterns assume structured inputs and developer-controlled contexts, which do not reflect unstructured livestream chat.

- **Uncovering Model Vulnerabilities with Multi-Turn Red Teaming (Anonymous, 2024):**  
  Shows that models appearing safe under single-turn benchmarks can be highly vulnerable in extended conversations.  
  **Gap:** Identifies the failure mode but does not provide an integrated mitigation pipeline.

- **LlamaFirewall (Chennabasappa et al., 2025):**  
  Introduces modular guardrails such as PromptGuard and alignment auditing.  
  **Gap:** Lacks explicit modeling of conversational state and escalation trajectories in livestream-style settings.

- **StruQ (Chen et al., 2024):**  
  Separates instructions from data at the API level to defend against prompt injection.  
  **Gap:** Assumes structured queries and limited user interaction; not directly adaptable to open chat environments.

- **ToxiTwitch (Ansari et al., 2025):**  
  Proposes emote-aware toxicity detection for livestream moderation.  
  **Gap:** Focuses on content classification rather than governance of agent autonomy or instructional hijacking.

Collectively, these works highlight the need for an integrated, stateful governance system designed specifically for adversarial, multi-turn livestream deployment.

---

## 3. Proposed Approach & Improvement Over Prior Art

We propose the **C-A-B Pipeline**, a system-level governance architecture composed of three modules:

### C: Message Structuring  
This module automatically parses unstructured livestream chat and separates trusted system-level instructions from untrusted audience input. It applies rule-based normalization and structured filtering to reduce injection risk in open chat streams.

### A: Stateful Risk Modeling  
Instead of evaluating each message independently, the system maintains a finite-state risk model that tracks escalation patterns across turns. Based on cumulative signals, the system dynamically adjusts autonomy tiers (e.g., direct generation, mediated rewrite, restricted response).

### B: Automated Red-Team Evaluation  
This module generates multi-turn adversarial scenarios to benchmark system resilience. By simulating escalation patterns, it provides quantitative metrics for evaluating the effectiveness of the integrated pipeline.

The key contribution is not a new model architecture, but a reproducible system-level integration that combines structuring, stateful modeling, and automated evaluation into a unified governance framework for livestream agents.

---

## 4. Plan for Checkpoint 2 Validation
For Checkpoint 2, we will implement a prompt-based validation using existing LLM APIs and simulated livestream conversations.

- **Simulation Setup:**  
  Construct adversarial multi-turn scenarios inspired by documented escalation tactics (Belaire et al., 2025; Anonymous, 2024).

- **Baseline Comparison:**  
  Compare:
  1. Baseline system (single-turn moderation only)  
  2. Integrated C-A-B pipeline

- **Evaluation Metrics:**  
  - **Attack Success Rate (ASR):** Percentage of successful jailbreaks.  
  - **Time-to-Intervention:** Number of turns before escalation is restricted.  
  - **False Positive Rate:** Rate of unnecessary mediation.  
  - **Persona Preservation Score:** Qualitative and rubric-based evaluation of stylistic consistency under mediation.

This evaluation will assess whether stateful governance improves resilience without excessively degrading conversational quality.

---

## 5. Initial Risks & Mitigation
- **Privacy Risk:**  
  Livestream chat may contain personally identifiable information (PII).  
  *Mitigation:* Apply automated redaction and restrict data storage to controlled experimental environments.

- **Over-Mediation Risk:**  
  Excessive restriction may reduce engagement and perceived authenticity.  
  *Mitigation:* Implement tiered mediation policies and persona-aware rewriting.

- **Latency Risk:**  
  Additional governance layers may introduce delay.  
  *Mitigation:* Use lightweight classifiers for initial filtering and limit complex checks to high-risk states.

- **Bias Risk:**  
  Risk modeling may overflag certain linguistic styles.  
  *Mitigation:* Perform error analysis and adjust thresholds based on controlled evaluation.

---

## 6. Open Issues & Milestones

- **Module C:** Finalize parsing logic and instruction isolation strategy.  
- **Module A:** Define escalation states and autonomy transition thresholds.  
- **Module B:** Implement automated red-team scenario generator and benchmarking scripts.  
- **Integration:** Conduct end-to-end testing and baseline comparison.

---

## 7. References
Ansari, B., Martin, E., & Mashhadi, A. (2025). *ToxiTwitch: Toward emote-aware hybrid moderation for live streaming platforms.*

Belaire, R., Sinha, A., & Varakantham, P. (2025). *Automatic LLM red teaming.*

Beurer-Kellner, L., et al. (2025). *Design patterns for securing LLM agents against prompt injections.*

Chen, S., Piet, J., Sitawarin, C., & Wagner, D. (2024). *StruQ: Defending against prompt injection with structured queries.*

Chennabasappa, S., et al. (2025). *LlamaFirewall: An open source guardrail system for building secure AI agents.*

Xu, W., & Parhi, K. K. (2025). *A survey of attacks on large language models.*

Anonymous. (2024). *Uncovering model vulnerabilities with multi-turn red teaming.*


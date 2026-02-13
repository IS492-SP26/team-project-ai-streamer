# Personal Literature Reflection – Danni Wu

## 1. Automatic LLM Red Teaming  
Belaire, R., Sinha, A., & Varakantham, P. (2025). *Automatic LLM Red Teaming*. arXiv.https://arxiv.org/abs/2508.04451

### Summary
This paper reframes red teaming as a multi-turn, trajectory-based process rather than a single prompt test. The authors model adversarial dialogue as a Markov Decision Process (MDP) and use Hierarchical Reinforcement Learning (HRL) to generate attack strategies over extended conversations. Their findings show that multi-turn attacks are significantly more successful than single-turn prompts because attackers can gradually build trust and escalate intent.

### Insights
- Multi-turn adversarial interactions pose fundamentally greater risks than isolated prompts.
- Safety benchmarks that test only single responses can give a false sense of robustness.
- Effective red teaming must evaluate conversational trajectories rather than final outputs alone.

### Limitations / Risks
- HRL-based red teaming may require significant computational resources.
- Defining harm or success metrics for conversational attacks can be subjective.

### Concrete Idea for My Project
This paper directly informed **Module B (Automated Red Teaming)** in our C-A-B pipeline. Instead of relying only on static test prompts, we design multi-turn adversarial scripts to systematically evaluate resilience under escalation scenarios.

---
## 2. Design Patterns for Securing LLM Agents  
Beurer-Kellner, L., et al. (2025). *Design Patterns for Securing LLM Agents against Prompt Injection*. ETH Zurich.https://arxiv.org/abs/2506.08837

### Summary
This paper proposes system-level design patterns to defend LLM agents against prompt injection attacks. Rather than attempting to retrain the model itself, the authors emphasize architectural solutions such as separating trusted instructions from untrusted user input and controlling execution flow. The work highlights how vulnerabilities often arise from improper system integration rather than model capability alone.

### Insights
- Security is fundamentally an information flow problem, not just a toxicity detection problem.
- Instruction/data separation is a structural safeguard against injection attacks.
- Many vulnerabilities emerge from orchestration design rather than the LLM itself.

### Limitations / Risks
- Strict separation patterns may reduce flexibility or reasoning efficiency.
- Some proposed patterns assume structured inputs, which livestream chat does not provide.

### Concrete Idea for My Project
This paper shaped **Module C (Message Structuring)** in our system. We implement automatic input normalization and instruction isolation to prevent raw livestream chat from interfering with internal system-level prompts.

---
## 3. A Survey of Attacks on Large Language Models  
Xu, W., & Parhi, K. K. (2025). *A survey of attacks on large language models.* IEEE. [https://arxiv.org/abs/2307.06435  ](https://arxiv.org/abs/2505.12567)


### Summary
This paper provides a comprehensive taxonomy of security threats across the lifecycle of large language models. The authors categorize attacks into three primary phases: training-time (e.g., data poisoning and backdoors), inference-time (e.g., jailbreaking and prompt injection), and availability & integrity attacks. A key finding is that vulnerabilities do not exist at a single stage but are distributed across the full deployment pipeline. The survey also highlights how embedding LLMs into agentic systems expands the attack surface, particularly through tool usage and multi-agent interactions. Overall, the work argues that many failures attributed to “model misalignment” are in fact system-level weaknesses.

### 3 Insights I Learned
- **The vulnerability of agency.** I initially assumed that agent-based systems might be more robust because of their planning capabilities. This survey changed that view by showing that tool invocation and inter-agent communication introduce new attack vectors, such as shadow process attacks and peer collusion. Governance must therefore monitor the action layer, not only generated text.

- **Syntactic vs. semantic triggers.** Adversarial manipulation does not always rely on obviously harmful language. Structural patterns and formatting tricks can activate undesirable behaviors without triggering toxicity classifiers. This insight highlights the limitations of traditional keyword-based moderation systems.

- **The “arrow and shield” dynamic.** The survey frames security as an ongoing arms race. As attack methods evolve toward automation and iterative refinement, defenses must also become adaptive rather than static rule sets.

### Limitations / Risks
- **Lack of unified benchmarking.** The survey notes the absence of standardized evaluation frameworks across attack categories, making it difficult to objectively compare robustness claims.
- **Defensive over-specialization.** Many mitigation strategies target narrow threat types, which may leave systems exposed to cross-phase or adaptive attacks.

### Concrete Idea for My Project
This survey directly informed Module C (Message Structuring) in the C-A-B pipeline. Inspired by the discussion of syntactic backdoors and escape-character manipulation, I will implement recursive input normalization and delimiter protection to prevent structural spoofing in livestream chat. This ensures that untrusted user input cannot interfere with internal system-level instructions in high-tempo conversational settings.
---

## Overall Reflection
Across these papers, a consistent theme emerges: LLM failures in real-world deployments are often system-level failures rather than purely model-level weaknesses. Static moderation and single-turn evaluation are insufficient in adversarial, multi-turn environments like livestream chat.

This literature shifted my perspective from building a “safer model” to designing a safer orchestration pipeline. The C-A-B framework reflects this shift:

- **C** enforces structural separation of untrusted input  
- **A** models conversational risk over time  
- **B** continuously stress-tests the system under adversarial pressure  

The goal is not to eliminate risk entirely, but to calibrate autonomy dynamically in high-risk public environments.






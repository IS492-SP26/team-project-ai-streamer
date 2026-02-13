# Personal Literature Reflection – Danni Wu

## 1. Automatic LLM Red Teaming  
Belaire, R., Sinha, A., & Varakantham, P. (2025). *Automatic LLM Red Teaming*. arXiv.

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
Beurer-Kellner, L., et al. (2025). *Design Patterns for Securing LLM Agents against Prompt Injection*. ETH Zurich.

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
## 3. Uncovering Model Vulnerabilities with Multi-Turn Red Teaming  
Anonymous. (2025). *Uncovering Model Vulnerabilities with Multi-Turn Red Teaming*.  

### Summary
This work demonstrates that models appearing safe under single-turn benchmarks can be highly vulnerable during multi-turn conversations. The authors show that persistent adversarial strategies—such as gradual reframing and escalation—can bypass defenses that report low attack success rates in static evaluations. The study reveals a significant gap between benchmark safety and real-world deployment conditions.

### Insights
- Single-turn safety evaluations underestimate real-world conversational risk.
- Attackers can embed harmful intent within benign conversational framing.
- Conversational memory increases capability but also expands the attack surface.

### Limitations / Risks
- Human red teaming does not scale easily for continuous evaluation.
- Overly defensive responses may reduce system responsiveness and engagement.

### Concrete Idea for My Project
This paper motivated **Module A (Stateful Risk Modeling)**. Instead of evaluating each message independently, our system maintains a finite-state risk model that tracks escalation patterns across turns and adjusts autonomy levels accordingly.

---

## Overall Reflection
Across these papers, a consistent theme emerges: LLM failures in real-world deployments are often system-level failures rather than purely model-level weaknesses. Static moderation and single-turn evaluation are insufficient in adversarial, multi-turn environments like livestream chat.

This literature shifted my perspective from building a “safer model” to designing a safer orchestration pipeline. The C-A-B framework reflects this shift:

- **C** enforces structural separation of untrusted input  
- **A** models conversational risk over time  
- **B** continuously stress-tests the system under adversarial pressure  

The goal is not to eliminate risk entirely, but to calibrate autonomy dynamically in high-risk public environments.




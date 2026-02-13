# Wen_Caroline.md — Paper Reflections (CP1)

---

## Paper 1
World Economic Forum. (2025). *AI Agents in Action: Foundations for Evaluation and Governance.*

**Summary (problem, method, findings)**  
This report argues that agentic AI changes the risk profile compared to single-turn chatbots because agents operate continuously, use tools, and may act with varying autonomy. It organizes agent systems into layers and emphasizes that governance must be system-level (not only model-level). It proposes evaluating agents using dimensions like autonomy, authority, predictability, and operating context. The report recommends progressive governance: safeguards should scale up as an agent becomes more autonomous and higher impact. Overall, it frames governance as an ongoing lifecycle process, including monitoring, logging, and continuous evaluation.

**Insights**  
1) “Autonomy tiering” is a practical governance knob: you can reduce capability when risk rises instead of only blocking outputs.  
2) Evaluation needs to be continuous; one-time safety checks are not enough for deployed agents.  
3) Governance is multi-layered (data, tools, orchestration), matching our idea that defenses should exist before and after the LLM.

**Limitations/risks**  
1) The guidance is high-level and doesn’t directly specify designs for adversarial livestream chat.  
2) Some governance practices assume org resources that small creators may not have.

**Idea inspired by this paper**  
Use “progressive governance” to justify Module A: implement an interpretable risk-state machine and map each state to an autonomy policy (direct → rewrite → restricted templates), and log every autonomy change as a governance event.

---

## Paper 2
Cheng, E. C., Cheng, J., & Siu, A. (2026). *Toward Safe and Responsible AI Agents: A Three-Pillar Model for Transparency, Accountability, and Trustworthiness.* arXiv preprint arXiv:2601.06223.

**Summary**  
This paper argues that safe agents require operational controls beyond prompt design or alignment, because agents interact with tools, environments, and long-running contexts. It discusses principles like transparency, accountability, and controllability, and proposes concrete mechanisms such as logging, decision traces, monitoring, and human oversight thresholds. The paper emphasizes that agent risks involve both content harms and action harms, so governance should consider how systems behave over time. It also points toward standard evaluation protocols and benchmarks as a way to make safety claims measurable and comparable.

**Insights**  
1) “Decision journaling” (logging why an agent did something) is essential for debugging and post-incident review.  
2) Human oversight can be triggered by risk thresholds, which fits a stateful escalation model.  
3) A benchmark mindset matters: without repeatable tests, safety is just narrative.

**Limitations/risks**  
1) It focuses more on principles than detailed defenses against prompt injection escalation.  
2) Logging and monitoring can create privacy risks in public chat settings.

**Idea inspired by this paper**  
Add a governance console that shows (a) current risk state, (b) which rule/policy triggered, (c) what mediation happened (rewrite/deflect/block), and (d) a replayable timeline.

---

## Paper 3
Chen, S., Piet, J., Sitawarin, C., & Wagner, D. (2025). *{StruQ}: Defending against prompt injection with structured queries.* In 34th USENIX Security Symposium (USENIX Security 25) (pp. 2383-2400).

**Summary**  
This paper treats prompt injection as a systems security problem where untrusted user text can be mixed with trusted instructions. It proposes structuring the input so the model can distinguish between “instructions” and “data,” reducing the chance that user content overrides system intent. Instead of relying only on the LLM to follow rules, it uses external formatting and separation to constrain how instructions are interpreted. The main finding is that structural separation can meaningfully reduce injection success in settings where developers can enforce the input format.

**Insights**  
1) Instruction/data separation is the LLM analogue of treating user input as untrusted in software security.  
2) Defenses should be designed for adversarial users, not average users.  
3) Hybrid solutions (rules + model-assisted classification) are realistic for messy inputs like livestream chat.

**Limitations/risks**  
1) Over-structuring can reduce conversational naturalness and hurt user experience.  
2) Attackers adapt, so separation is not “one and done” without ongoing red-team evaluation.

**Idea inspired by this paper**  
Implement Module C as a “message compiler” that outputs a fixed schema (trusted system goals + untrusted chat + tags). Any message that tries to embed meta-instructions gets flagged or routed to stricter autonomy tiers.

---

## Paper 4
Yeo, A., & Choi, D. (2025). *Multimodal Prompt Injection Attacks: Risks and Defenses for Modern LLMs.* arXiv preprint arXiv:2509.05883.

**Summary**  
This paper studies how prompt injection can occur through multimodal channels, such as images or UI screenshots that contain hidden instructions. It shows that models may follow instructions embedded in visual content even when those instructions are untrusted. The paper discusses defenses such as isolating untrusted content, restricting tool use, and adding verification steps before executing model outputs. The key takeaway is that safety pipelines should assume non-text inputs can also be adversarial.

**Insights**  
1) In livestream contexts, “inputs” may include images, overlays, or copied content — all can be attack vectors.  
2) Tool-using agents are especially vulnerable because injection can lead to real actions, not just bad text.  
3) Defenses should include both input-side filtering and action-side gating.

**2 limitations/risks**  
1) Many defenses are still immature and may reduce usability when applied too aggressively.  
2) Attack detection in multimodal content can be noisy, increasing false positives.

**Idea inspired by this paper**  
Extend Module C to treat any external content (links, pasted text blocks, image-derived text) as untrusted, and tag it so Module A can raise risk state when “suspicious channels” appear.

---

## Paper 5
Ansari, B., Ali, S., Martin, E., Sivachenko, M., & Mashhadi, A. (2026). *ToxiTwitch: Toward Emote-Aware Hybrid Moderation for Live Streaming Platforms.* arXiv preprint arXiv:26

**Summary**  
This paper argues that live-stream moderation is hard because meaning is highly contextual and community-specific, with emotes, slang, and fast-paced dynamics. It proposes moderation approaches that incorporate platform-specific signals rather than generic toxicity detectors. The findings suggest that standard moderation can miss harmful content or over-flag benign content because it lacks cultural context. It motivates designing moderation as a hybrid system: rules + learned models + human oversight.

**Insights**  
1) “Livestream language” is not standard text; emotes and context carry meaning.  
2) False positives matter more in livestreaming because they interrupt flow and audience experience.  
3) Moderation should be stateful and context-aware, not message-by-message.

**Limitations/risks**  
1) Platform-specific moderation may not transfer across communities.  
2) Collecting community signals can raise privacy and fairness concerns.

**Idea inspired by this paper**  
Use a livestream-aware risk feature set in Module A (e.g., repeated baiting, escalating patterns, emote-heavy harassment cues), and evaluate false-positive cost explicitly as part of the trade-off analysis.

# Personal Literature Reflection – Fitz Song

## 1. ReAct: Synergizing reasoning and acting in language models. 

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K. R., & Cao, Y. (2023). ICLR. https://arxiv.org/abs/2210.03629


### Summary
ReAct addresses the problem that LLMs either “think” (chain-of-thought) or “act” (tool calls) but often fail when these are separated, leading to hallucinations and brittle plans. The paper proposes prompting the model to interleave reasoning traces with actions, allowing it to retrieve information, update plans, and recover from mistakes. They show improved performance on tasks like QA and interactive environments by letting the model consult external tools (e.g., Wikipedia search) during generation. An additional benefit is interpretability: the trace reveals why the model chose actions and how it corrected itself. For our project, ReAct is a template for the “director” agent that plans topics, calls tools (persona memory / banned-topic lists), and keeps the on-stream dialogue coherent.
### Insights
Interleaving reason → act → observe is a practical pattern for reducing hallucinations in live systems.
Tool calls can be lightweight (retrieval, memory lookup) yet still drastically improve consistency.
Trace based structure gives us hooks for guardrails

### Limitations / Risks
Reasoning traces can leak sensitive info or policy-violating content if shown/logged carelessly.
More steps can increase latency, dangerous for real-time VTuber responses.

### Concrete Idea 

Implement a director loop where planning happens in a hidden channel (not shown on stream), with only the final “spoken” line passing through the guardrail layer.


---

## 2. CAMEL: Communicative agents for “mind” exploration of large language model society. 
Li, G., Hammoud, H. A. A. K., Itani, H., Khizbullin, D., & Ghanem, B. (2023). NeurIPS. https://arxiv.org/abs/2303.17760

### Summary

CAMEL explores how to reduce human burden in complex task conversations by enabling autonomous cooperation among multiple LLM agents. The authors propose “role-playing” agents guided by inception prompting, where each agent has a defined role and goal that shapes the conversation trajectory. They use these structured interactions to study cooperation and to generate conversational data for instruction-following settings. The key idea is that role constraints can create more consistent, goal-directed dialogues than a single generic assistant. For our middleware, CAMEL supports splitting responsibilities: the VTuber persona agent can focus on character voice while the director and safety critic enforce constraints.

### Insights

Role definitions can stabilize behavior on “who you are” and “what you must do” is an effective control lever.
Multi agent setups can generate training/eval data tailored to our constraints (persona + safety rules)
Conversation structure (turn-taking rules) is a form of safety/control, not just content filtering.

### Limitations / Risks

Role prompts can still be overridden by adversarial user input if not isolated properly.
Multi-agent interactions can drift if goals conflict or are underspecified.

### Concrete Idea
  Define three explicit roles with separate system prompts and memory scopes: (1) Persona Actor, (2) Director/Planner, (3) Safety Critic—then enforce a fixed conversation protocol between them

---

## 3. Uncovering Model Vulnerabilities with Multi-Turn Red Teaming  
Llama Guard: LLM-based input-output safeguard for human-AI conversations  
Inan, H., Upasani, K., Chi, J., Rungta, R., Iyer, K., Mao, Y., … Khabsa, M.(2023)https://arxiv.org/abs/2312.06674
### Summary

Llama Guard tackles the need for robust safety filtering of both user prompts and model responses in conversational systems. The paper introduces an LLM-based classifier tuned to a safety taxonomy, enabling multi-class safety decisions and customizable output formats. A major point is that an instruction-tuned LLM can serve as a moderation model that generalizes across categories and benchmarks rather than relying only on keyword rules. They show strong results on existing moderation datasets and emphasize that taxonomy design is central for controllable safety behavior. For our middleware, this supports using a dedicated “guardrail model” (or guardrail prompting) as a modular step before text reaches the live stream.

### Insights

A safety taxonomy is an interface: it defines what the system can detect and how decisions are explained.
Classifying both prompt and response helps defend against “unsafe echoing,” not just bad user inputs.
Instruction-tuned models can return structured decisions (labels + rationales), making automation easier.


### Limitations / Risks

An LLM-based guard can be attacked (adversarial phrasing, jailbreak-style content) and may need defense-in-depth.
Overblocking risk: false positives could harm streamer experience and reduce creativity.


### Concrete Idea

Design our web console around a configurable taxonomy (toxicity/NSFW/political sensitivity/persona drift), then generate a consistent JSON decision schema that downstream apps can rely on for real-time blocking or rewrites.

## AI disclosure
GPT5 helped with the paper application related wide search, help summarized and filtered the papers for selection, brainstorm ideas realted to the topic, all paper and output has been manually read.






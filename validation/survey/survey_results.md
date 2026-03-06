# Survey Results: AI Livestream Governance Study
Survey Result spreedshe link: https://docs.google.com/spreadsheets/d/1uQVZx98DeQgjvFga7LH90V9s6pRng4OP6JJBDGDK-zQ/edit?usp=sharing

# Validation Results – Survey Findings

## Overview

We collected **6 responses** from participants with different levels of experience with AI systems and livestream environments.

Respondent backgrounds include:

- AI agent / LLM developers
- Researchers or students working with LLMs
- Viewers interested in AI-powered content
- Curious users with little technical experience

Most respondents reported **direct experience observing AI failures or manipulations**, especially in conversational systems.

---

# Respondent Background

| Respondent | Background | Tools Used |
|---|---|---|
| R1 | AI agent developer / viewer / researcher | AI VTuber tools, ChatGPT, Claude, Gemini |
| R2 | Viewer (non-technical) | ChatGPT, Claude, Gemini |
| R3 | Researcher/student working with LLMs | ChatGPT, Claude, Gemini |
| R4 | Viewer (non-technical) | ChatGPT, Claude, Gemini |
| R5 | Curious user | Custom AI agents |
| R6 | Researcher/student working with LLMs | Custom AI agents, ChatGPT, Claude, Gemini |

Observation:

- Most respondents have interacted with **LLM-based conversational systems**
- Some participants also have experience with **custom AI agents or developer tools**

---

# Observed AI Failures

Participants were asked whether they had seen AI behave incorrectly due to chat messages.

| Response | Count |
|---|---|
| Yes — manipulated or tricked | 4 |
| Yes — lost character/personality | 1 |
| Yes — became unsafe over multiple turns | 1 |
| Not really | 1 |

Key takeaway:

> Most participants have **observed AI manipulation or unintended behavior in conversational systems**.

This confirms that **prompt manipulation and multi-turn conversational risks are real concerns in AI livestream environments.**

---

# Frequency of Exploitation Attempts

Participants rated how often viewers try to **trick or exploit AI agents** (1–5 scale).

| Rating | Meaning |
|---|---|
| 1 | Very rarely |
| 5 | Very frequently |

Observed responses: 4, 3, 5, 2, 1, 3
Average score: 3.0 / 5


Interpretation:

> Exploitation attempts occur **occasionally to moderately often**, indicating that AI livestream systems must be prepared for adversarial interactions.

---

# Most Serious Problems in AI Livestreams

Participants could select multiple options.

Most frequently mentioned concerns:

- **AI being manipulated by viewers** (prompt injection / role-play traps)
- **AI responses becoming riskier over multiple turns**
- **AI drifting away from its persona or character**
- **Difficulty understanding why the AI made a certain decision**
- **Not knowing when a conversation is becoming risky**
- **Moderation systems reacting too slowly or inconsistently**

Key insight:

> Respondents emphasized **lack of transparency and difficulty understanding AI behavior** as major concerns.

---

# Perceived Value of the Proposed Modules

Participants rated the usefulness of several governance modules (1–5 scale).

| Module | Description | Avg Score |
|---|---|---|
| Module C | Message structuring & injection filtering | 4.0 |
| Module A | Stateful conversation risk detection | 3.5 |
| Module B | Automated red-team testing | 3.2 |
| Governance Dashboard | Monitoring and transparency interface | 3.5 |

Interpretation:

- **Message-level filtering (Module C)** was rated highly
- **Conversation-level risk modeling (Module A)** was also valued
- Automated evaluation tools (Module B) were considered useful but slightly less critical for end users

---

# Preferred Module

Participants selected the **most useful module**.

| Module | Votes |
|---|---|
| A — Stateful Risk Modeling | 2 |
| B — Automated Red-Team Evaluation | 1 |
| C — Message Structuring & Injection Filtering | 1 |
| None | 2 |

Interpretation:

> While opinions vary, **stateful risk modeling** received the most support, suggesting that users value systems that track **risk across entire conversations rather than single messages**.

---

# Main Concerns About AI Livestream Agents

Participants expressed several concerns about deploying AI agents in livestream settings.

Common concerns included:

- **Being manipulated by viewers**
- **Harmful or offensive outputs**
- **Loss of control or transparency**
- **AI drifting away from its intended persona**

These concerns highlight the need for **strong governance and monitoring mechanisms**.

---

# Desired Safety Features

Participants suggested several features that would improve trust and safety:

- Stronger **conversation steering mechanisms**
- Improved **moderation and filtering of adversarial prompts**
- Systems that **prevent audience manipulation**
- More **control and transparency** for creators and developers

---

# Key Takeaways

From the survey results, several themes emerge:

1. **Prompt manipulation is a common concern** among both technical and non-technical users.
2. Many participants worry about **multi-turn risk escalation**, where conversations gradually become unsafe.
3. Users want **better transparency and control** over AI behavior.
4. Systems that monitor **conversation-level risk (not just individual messages)** are perceived as valuable.

These findings support the motivation for the proposed **C-A-B governance pipeline**, which combines:

- **Contextual message filtering (C)**
- **Stateful risk modeling (A)**
- **Automated adversarial evaluation (B)**

to improve the safety and reliability of AI livestream agents.


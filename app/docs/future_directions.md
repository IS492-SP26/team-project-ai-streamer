# Future Directions — C-A-B Pipeline

Expansion ideas based on research into open-source AI safety projects (NeMo Guardrails, LlamaFirewall, Guardrails AI, Rebuff, LangGraph). These build on top of the current Module C + A + B implementation and are ordered by estimated effort.

---

## 1. Canary Token for Prompt Leakage Detection

**Inspired by:** Rebuff (ProtectAI)

Embed a unique random string in the system prompt each session. If the AI's output contains that string, it means the system prompt was leaked.

```python
canary = f"CANARY-{uuid4().hex[:8]}"
system_prompt = f"{base_prompt}\n[Internal canary: {canary}]"

# In output_scanner:
if canary in ai_response:
    # system prompt leaked — block immediately
```

**Effort:** ~30 lines of code in output_scanner.py
**Value:** Extra defense layer against S3-type attacks (prompt leak requests)

---

## 2. Config-Driven Policy System

**Inspired by:** NeMo Guardrails (YAML config + Colang DSL)

Move all detection patterns, thresholds, and autonomy policies from hardcoded Python into `prompts/config.yaml`. Allow creators to adjust rules via a Settings page in the Streamlit UI without touching code.

Possible features:
- Toggle individual detection pattern groups on/off
- Slider for fiction_detector thresholds (stricter ↔ more lenient)
- Custom cultural whitelist entries
- Preset profiles: Strict / Balanced / Creative

**Effort:** Medium (config loader + Settings UI page)
**Value:** Makes the tool usable by non-technical creators — key for adoption

---

## 3. Conversation Replay & Time-Travel Debug

**Inspired by:** LangGraph Checkpointer

Save every turn's state snapshot to SQLite (via Caroline's logger). Add a Replay mode in the frontend:
- Select a past session
- Step through turns one by one
- See Module C output, Module A state transition, AI response at each step
- Highlight the exact turn where risk escalated

**Effort:** Medium-high (SQLite persistence + Replay UI)
**Value:** Critical for CP4 user study's "post-stream incident review" journey (Design Spec Journey C)

---

## 4. LLM-Assisted Semantic Classification (Two-Layer Detection)

**Inspired by:** LlamaFirewall (PromptGuard + Alignment Audit)

Current Module C is entirely rule-based (regex). Add a second layer that uses a small LLM (e.g., Haiku) for semantic risk classification — but only when Module A is in Suspicious or Escalating state (to save cost).

```
Turn arrives
  → Module C (regex, <1ms)     ← always runs
  → Module A state check
  → if state >= Suspicious:
      → LLM classifier (~200ms) ← only runs when needed
      → merge score with Module C tags
```

**Effort:** Medium (LLM call + scoring merge logic)
**Value:** Catches semantic attacks that regex misses (indirect allusions, metaphors, coded language that isn't in the pattern list)

---

## 5. Streaming Token-Level Guardrails

**Inspired by:** NeMo Guardrails Streaming Mode

In livestream, AI output is typically streamed token-by-token. Current output_scanner waits for the complete response. If the first 3 sentences are safe but sentence 4 is harmful, the audience has already seen sentences 1–3.

Fix: Buffer output in ~200-token chunks, run output_scanner on each chunk, truncate immediately if any chunk is flagged.

**Effort:** High (streaming integration + buffer management)
**Value:** Essential for real livestream deployment where latency and partial-output safety both matter

---

## 6. Vector Similarity Attack Memory

**Inspired by:** Rebuff (VectorDB layer)

Store embeddings of past blocked attack messages. When a new message arrives, compute similarity against the attack database. High similarity → elevate risk even if the exact pattern doesn't match regex.

**Effort:** High (embedding model + vector store + similarity search)
**Value:** Adaptive defense — learns from past attacks without manual pattern updates

---

## Implementation Priority (suggested)

| # | Direction | Effort | CP4 Value | Production Value |
|---|-----------|--------|-----------|-----------------|
| 1 | Canary Token | Low | Medium | High |
| 2 | Config-Driven Policy | Medium | Low | Very High |
| 3 | Conversation Replay | Medium | High | High |
| 4 | LLM Semantic Layer | Medium | Medium | Very High |
| 5 | Streaming Guardrails | High | Low | Critical |
| 6 | Vector Attack Memory | High | Low | High |

For CP4 user study, priorities 1 and 3 have the best effort-to-value ratio.
For a real product, priorities 2 and 5 are most important.

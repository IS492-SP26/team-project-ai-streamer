# Future Directions — C-A-B Pipeline

Expansion ideas based on research into open-source AI safety projects (NeMo Guardrails, LlamaFirewall, Guardrails AI, Rebuff, LangGraph). All directions build on top of Module C + A + B after teammates complete their respective implementations.

---

## Already Implemented

### Baseline Toggle (A/B Comparison Mode)

**Status:** Done (fitz branch)

Sidebar toggle switches between C-A-B pipeline (ON) and raw LLM baseline (OFF). Events are tagged with `pipeline_mode: "cab"` or `"baseline"` for quantitative comparison.

**Why it matters:** CP4 user study requires a control condition. With the toggle, participants can send the same attack message in both modes and directly observe the difference — C-A-B blocks it, baseline lets it through. This is the core of evaluation credibility.

---

## Direction 1: Canary Token for Prompt Leakage Detection

**Inspired by:** Rebuff (ProtectAI)

Embed a unique random string in the system prompt each session. If the AI's output contains that string, the system prompt was leaked.

```python
canary = f"CANARY-{uuid4().hex[:8]}"
system_prompt = f"{base_prompt}\n[Internal canary: {canary}]"

# In output_scanner:
if canary in ai_response:
    # system prompt leaked — block immediately
```

**Effort:** ~30 lines in output_scanner.py
**Value:** Extra defense layer against S3-type attacks (prompt leak requests). Our test results showed that Gemini partially leaked injected rules at S3 Turn 27 — a canary would catch this instantly even if the regex patterns miss the specific leak format.

---

## Direction 2: Config-Driven Policy System

**Inspired by:** NeMo Guardrails (YAML config + Colang DSL)

Move all detection patterns, thresholds, and autonomy policies from hardcoded Python into `prompts/config.yaml`. Allow creators to adjust rules via a Settings page in the Streamlit UI without touching code.

```yaml
# Example: creator adjusts via UI sliders
rules:
  injection_filter:
    enabled: true
    patterns:
      system_override: { enabled: true, severity: high }
      rule_injection: { enabled: true, severity: high }
      prompt_leak: { enabled: true, severity: high }
  fiction_detector:
    threshold_medium: 2.5    # ← slider
    threshold_high: 5.0      # ← slider
    history_window: 15
  content_tagger:
    cultural_whitelist:
      - "yyds"
      - "tang ping"
      # creator can add custom entries
  presets:
    strict: { threshold_medium: 1.5, threshold_high: 3.0 }
    balanced: { threshold_medium: 2.5, threshold_high: 5.0 }
    creative: { threshold_medium: 4.0, threshold_high: 8.0 }
```

**Effort:** Medium (config loader + Settings UI page)
**Value:** Makes the tool usable by non-technical creators — the CP2 interviews showed that creators want "a checklist and a few buttons" (Interview 1 Q6), not a code editor. NeMo's Colang DSL is the ultimate version of this, but YAML + UI sliders is sufficient for our scope.

---

## Direction 3: Conversation Replay & Time-Travel Debug

**Inspired by:** LangGraph Checkpointer

Save every turn's state snapshot to SQLite (via Caroline's logger). Add a Replay mode in the frontend:
- Select a past session from a dropdown
- Step through turns one by one with forward/back buttons
- See Module C output, Module A state transition, AI response at each step
- Highlight the exact turn where risk escalated
- Compare "what happened" vs "what would happen with different thresholds"

**Effort:** Medium-high (SQLite persistence + Replay UI)
**Value:** Critical for CP4 user study's "post-stream incident review" journey (Design Spec Journey C). Both CP2 interviewees independently asked for this — Interview 2 wanted "scenarios, replay, metrics, and config suggestions" and Interview 1 wanted "Top 5 ways people can break it + short examples."

---

## Direction 4: LLM-Assisted Semantic Classification (Two-Layer Detection)

**Inspired by:** LlamaFirewall (PromptGuard + Alignment Audit)

Current Module C is entirely rule-based (regex). It's fast (<1ms) but can only match patterns it's been explicitly programmed for. Semantic attacks — indirect allusions, metaphors, coded references not in the pattern list — slip through.

Add a second detection layer that uses a small LLM (e.g., Claude Haiku) for semantic risk classification, but only when Module A is in Suspicious or Escalating state (to control cost).

```
Turn arrives
  → Module C (regex, <1ms)         ← always runs, zero cost
  → Module A state check
  → if state >= Suspicious:
      → LLM classifier (~200ms)    ← only when risk is elevated
      → merge LLM score with Module C tags
      → update risk_score accordingly
```

**Effort:** Medium (LLM call + scoring merge logic + prompt engineering for classifier)
**Value:** Catches what regex can't — our S1 scenario showed that fiction-framing attacks often use novel phrasing that no fixed pattern list will fully cover. This is LlamaFirewall's core insight: rule-based fast filtering first, LLM-based semantic understanding second.

---

## Direction 5: Streaming Token-Level Guardrails

**Inspired by:** NeMo Guardrails Streaming Mode

In livestream, AI output is typically streamed token-by-token to minimize perceived latency. Current output_scanner waits for the complete response before scanning. If the first 3 sentences are safe but sentence 4 is harmful, the audience has already seen sentences 1–3 by the time the scanner runs.

Fix: Buffer output in ~200-token chunks, run output_scanner on each chunk, truncate the stream immediately if any chunk is flagged.

```
LLM streaming output:
  token token token [200 tokens accumulated]
    → output_scanner.scan_chunk()
    → if flagged: truncate stream, insert safe message
    → else: flush chunk to frontend
  token token token [next 200 tokens]
    → scan again...
```

**Effort:** High (streaming API integration + buffer management + frontend partial rendering)
**Value:** Essential for real livestream deployment. NeMo's latest version does exactly this. Without it, there's always a window where harmful content reaches the audience before the scanner can act. Our S1 test results showed OpenAI delivered 5 consecutive turns of harmful content — streaming guardrails would have cut that off mid-sentence on the first harmful turn.

---

## Direction 6: Vector Similarity Attack Memory

**Inspired by:** Rebuff (VectorDB layer)

Store embeddings of past blocked attack messages in a vector database. When a new message arrives, compute cosine similarity against the attack database. High similarity → elevate risk score even if the exact pattern doesn't match any regex.

```python
# On block:
attack_db.store(embed(blocked_message), metadata={"turn": ..., "tags": ...})

# On new message:
similar = attack_db.query(embed(new_message), top_k=3)
if max(similar.scores) > 0.85:
    risk_tags.append("manipulation_attempt")
    severity = max(severity, "medium")
```

**Effort:** High (embedding model + vector store like Chroma/FAISS + similarity search)
**Value:** Adaptive defense that learns from past attacks without manual pattern updates. If an attacker tries a variation of a previously blocked message, the vector similarity catches it even though the words are different. This is the "self-hardening" property that Rebuff demonstrates.

---

## Direction 7: Multi-Model Consensus Voting

**Inspired by:** CP2 test results (16-turn detection gap between best and worst model)

Our CP2 testing showed Claude detected threats at ~Turn 14, OpenAI at ~Turn 24, Gemini at ~Turn 30. No single model is reliable across all attack types. A consensus approach would query 2-3 models in parallel and require majority agreement before passing a response through.

```
User message → Module C
  → if state >= Suspicious:
      → query Claude + OpenAI + Gemini in parallel
      → majority vote on safety
      → if 2/3 flag it: block
      → if 1/3 flags it: elevate risk score
```

**Effort:** Medium (parallel API calls + voting logic)
**Value:** Reduces the chance that a single model's blind spot becomes a pipeline-wide failure. Our empirical data shows each model has different failure patterns — consensus smooths this out.

---

## Direction 8: Audience Warning System

**Inspired by:** Design Spec Section 6 ("Show warnings to audience" toggle)

When risk state reaches Escalating, optionally display a visible warning overlay on the livestream (e.g., "This conversation is being moderated") without revealing internal detection logic. This was a Design Spec requirement (Settings Screen 5) that hasn't been implemented.

**Effort:** Low-medium (Streamlit banner + toggle in Settings)
**Value:** Transparency to viewers that safety is active, which can deter attackers. Interview 2 specifically noted this should be configurable — some creators want visible warnings, others prefer silent mediation.

---

## Implementation Priority

| # | Direction | Effort | CP4 Value | Production Value |
|---|-----------|--------|-----------|-----------------|
| — | Baseline Toggle | Done | High | Medium |
| 1 | Canary Token | Low | Medium | High |
| 8 | Audience Warning | Low-Med | Medium | Medium |
| 2 | Config-Driven Policy | Medium | Low | Very High |
| 7 | Multi-Model Consensus | Medium | Medium | High |
| 3 | Conversation Replay | Medium-High | High | High |
| 4 | LLM Semantic Layer | Medium | Medium | Very High |
| 5 | Streaming Guardrails | High | Low | Critical |
| 6 | Vector Attack Memory | High | Low | High |

**For CP4 user study:** Baseline Toggle (done) + Direction 3 (Replay) have the best effort-to-value ratio.
**For production deployment:** Directions 2 (Config), 4 (LLM Layer), and 5 (Streaming) are most critical.
**Quick wins:** Directions 1 (Canary) and 8 (Audience Warning) can be implemented in a few hours each.

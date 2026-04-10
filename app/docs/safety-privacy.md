# Safety & Privacy Documentation — Module C

**Owner:** Fitz Song (Person B)
**Last Updated:** 2026-03-29

---

## What Module C Does

Module C is the first line of defense in the C-A-B governance pipeline. It analyzes raw user messages from livestream chat and produces structured risk assessments for Module A's state machine.

### Components

| Component | Purpose | In `process_message()` contract? |
|-----------|---------|:---:|
| `injection_filter.py` | Deterministic prompt injection detection | Yes |
| `fiction_detector.py` | Multi-turn fiction-framing & reassurance tracking | Yes |
| `content_tagger.py` | Persona drift & harmful content detection | Yes |
| `output_scanner.py` | Pre-delivery AI response safety check | No (separate hook) |

### What Module C Does NOT Do

- Does NOT call any LLM/AI model — all detection is rule-based for speed
- Does NOT make final block/pass decisions — that is Module A's responsibility
- Does NOT store any data — logging is Module B/C (Caroline's) responsibility
- Does NOT manage conversation state — that is Module A's state machine

---

## Risk Tag Categories

Module C outputs exactly 4 risk tag categories (per INTERFACE_SPECIFICATION_v2.md):

| Tag | Meaning | Detector |
|-----|---------|----------|
| `manipulation_attempt` | Prompt injection, fiction framing, flattery, authority impersonation | injection_filter, fiction_detector |
| `escalating_harm` | Progressive shift toward harmful content across turns | fiction_detector |
| `persona_drift` | Attempts to break VTuber character or reveal AI identity | content_tagger |
| `harmful_content` | Direct harmful/unsafe requests | content_tagger |

---

## Privacy Commitments

### No PII Storage
Module C does not store, log, or persist any user messages. All processing is stateless within a single function call. Conversation history is passed as an argument and not retained.

### No External Calls
Module C makes zero network requests. All detection runs locally using compiled regex patterns.

### Log Redaction Guidance
When Module A or the Logger records Module C outputs:
- `block_reason` may contain quoted snippets of user input — these should be truncated to ≤60 characters
- User messages in logs should have PII (emails, phone numbers) redacted before storage
- Session IDs should not be linkable to real user identities

---

## Cultural Awareness

Module C includes an explicit cultural whitelist to prevent false positives on legitimate expressions common in VTuber and gaming communities:

### Whitelisted Expressions (will NOT be flagged)

| Expression | Language | Meaning |
|-----------|----------|---------|
| yyds / 永远的神 | CN | "Forever a legend" — highest praise |
| tang ping / 躺平 | CN | "Lie flat" — opting out of hustle culture |
| 打call | CN | "Cheer/support someone" |
| aiya / 哎呀 | CN | Mild exclamation |
| "I'm dead" | EN | Laughing very hard |
| "I'm gonna explode" | EN | Very excited |
| "commit arson on the todo list" | EN | Burn through tasks quickly |
| "murder this deadline" | EN | Work hard on deadline |
| "killing it" | EN | Doing very well |
| "chat you're trash" | EN | Twitch-style friend banter |
| sheesh, bussin, no cap | EN | Gen-Z slang |

### Why This Matters
Our S2 (Cultural & Bilingual Nuance) test scenario confirmed that all three tested LLMs correctly handled these expressions. A keyword-based system that flags "murder," "dead," or "explode" would produce unacceptable false positives in livestream contexts.

---

## Pattern Update Process

1. New attack patterns observed in red-team testing (Module B) should be added to the appropriate detector
2. New cultural expressions should be added to `content_tagger._CULTURAL_SAFE_PATTERNS`
3. All pattern changes require corresponding test cases
4. Pattern updates do not require retraining any model — just code changes

---

## False Positive Mitigation

### Design Principles
- **Conservative blocking:** Only `injection_blocked=True` for high-confidence deterministic patterns (regex match on known injection formats)
- **Probabilistic signals go to Module A:** Fiction framing, escalation patterns, and ambiguous content are tagged but NOT blocked — Module A's state machine makes the final decision
- **Cultural whitelist:** Explicit safe-list for expressions that would otherwise false-positive

### If False Positives Occur
1. Check if the expression should be added to the cultural whitelist
2. Check if the regex pattern is too broad
3. Add a test case reproducing the false positive
4. Fix the pattern and verify no existing tests break

---

## Performance

- Target: <10ms per `process_message()` call
- All patterns are compiled regex (compiled once at module load)
- No network calls, no file I/O, no model inference
- Memory: minimal — only the compiled regex patterns are held in memory

# Safety, Privacy & Reliability notes (short)

This document explains the team's approach to handling safety, privacy, and reliability for the demo and evaluation.

1) Personal Data (PII) handling
- Telemetry should not contain raw PII (names, emails, precise payment info).
- `user_id` field must be a platform-provided opaque id or a hashed/anonymized value.
- If the frontend provides PII inadvertently, the ingestion connector must redact or hash before insertion.

2) Secrets & Keys
- Never commit API keys or secrets. Use `.env` files (not committed).
- `.env.example` contains placeholder names; real keys loaded from environment.

3) Rate limits & model API safety
- For production or demo with real LLMs, apply client-side rate limiting and concurrency caps.
- Heavy semantic checks (LLM-based intent classifiers) must be risk-gated (only called when `risk_state` >= Suspicious).

4) Jailbreak / Abuse mitigation
- Multi-layered defenses:
  - Fast deterministic filters (regex prompt injections) in Module C — zero API cost, immediate block.
  - Hardened system prompts to reduce compliance.
  - State-machine (Module A) to track escalation patterns.
  - Output scanner (Module C) to scan model output before delivery.
- Logging: store both `ai_response_original` and `ai_response_final` (for audit), but do not expose raw logs publicly.

5) Reliability
- Telemetry writes are synchronous and idempotent (PRIMARY KEY on `(session_id, turn_number)`) to avoid duplicates.
- For high-load streams, we recommend:
  - Upstream message selection (only selected messages go through full LLM path)
  - Asynchronous risk-gated semantic checks
  - Buffering & batching telemetry writes to a durable backend (e.g., write-ahead queue)

6) Responsibilities
- Frontend: generate `session_id`, anonymize `user_id` where required.
- Module C: perform immediate deterministic blocking and tag messages.
- Module A: implement state-machine thresholds and expose `risk_state`, `risk_score`, `action`.
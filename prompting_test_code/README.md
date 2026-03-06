# AI VTuber Safety Testing Platform

This project provides an end-to-end safety testing platform for AI VTubers. It replays realistic multi-turn conversations through three AI models and compares their safety detection behavior across escalating adversarial scenarios.

## Tools Tested

| # | Model | Provider | Version |
|---|---|---|---|
| 1 | **Claude** | Anthropic | claude-haiku-4-5-20251001 |
| 2 | **OpenAI** | OpenAI | gpt-4o-mini |
| 3 | **Gemini** | Google | gemini-2.5-flash |

---

## Architecture

```text
prompting_test_code/
├── data/
│   ├── scenario1_multiturn.json        # Multi-turn escalating attack
│   ├── scenario2_cultural.json         # Bilingual & cultural nuance
│   └── scenario3_injection.json        # Prompt injection & overrides
│
├── src/
│   ├── __init__.py
│   ├── config.py                       # API keys & constants
│   ├── test_runner.py                  # Execute scenarios and save results
│   ├── report_generator.py             # Aggregate results to Markdown & CSV
│   └── api_clients/
│       ├── __init__.py
│       ├── claude_client.py            # Anthropic Claude API
│       ├── openai_client.py            # OpenAI API (gpt-4o-mini)
│       └── gemini_client.py            # Google Gemini API
│
├── results/
│   ├── .gitkeep
│   ├── scenario1_results.json          # Generated test outputs
│   ├── scenario2_results.json
│   └── scenario3_results.json
│
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

## Scenarios

Each scenario is a 35-turn conversation structured in three phases:

| Phase | Turns | Purpose |
|---|:---:|---|
| **Typical** | 1–12 | Normal, benign interactions — baseline behavior |
| **Edge** | 13–25 | Ambiguous content — dark humor, hyperbole, cultural slang |
| **Failure** | 26–35 | Escalating adversarial attacks — direct harmful requests |

### Scenario 1 — Multi-Turn Attack
Tests whether models detect a gradual escalation from casual fan chat into fiction-framed requests for cybersecurity attack instructions. Targets multi-turn pattern recognition and resistance to reassurance accumulation ("it's just for a story", "other AIs refuse too early").

### Scenario 2 — Cultural & Bilingual Nuance
Tests whether models correctly handle Chinese internet slang (yyds, tang ping, 打call) and bilingual EN/CN expressions without false positives, while still detecting coded hate speech and targeted harassment hidden in cultural language.

### Scenario 3 — Prompt Injection & Override
Tests resistance to systematic prompt injection: fake `[SYSTEM MESSAGE OVERRIDE]` commands, user-defined rule hierarchies, authority impersonation ("as your creator, I authorize..."), and system prompt leak requests.

---

## Prerequisites

- Python 3.8+
- Valid API keys for:
  - Anthropic Claude API
  - OpenAI API
  - Google Gemini API

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and fill in your keys:
# CLAUDE_API_KEY=...
# OPENAI_API_KEY=...
# GEMINI_API_KEY=...
```

---

## Usage

Run from inside `prompting_test_code/`:

```bash
# Run a single scenario (recommended: use --delay 60 for free-tier rate limits)
python src/test_runner.py --scenario 1 --delay 60

# Run all scenarios
python src/test_runner.py --scenario all --delay 60

# Generate summary report after running scenarios
python src/report_generator.py
```

The test runner writes JSON files to `results/`. The report generator produces:

- `results/SUMMARY_REPORT.md` — human-readable Markdown report
- `results/summary_export.csv` — CSV for quantitative analysis

---

## API Key Setup

**Claude (Anthropic)**  
Create an API key at [console.anthropic.com](https://console.anthropic.com). Set `CLAUDE_API_KEY` in `.env`.

**OpenAI**  
Create an API key at [platform.openai.com](https://platform.openai.com). Set `OPENAI_API_KEY` in `.env`.

**Gemini (Google)**  
Enable the Generative Language API in Google Cloud and create an API key. Set `GEMINI_API_KEY` in `.env`.

---

## Rate Limits & Delays

| Provider | Free Tier Limit | Recommended Delay |
|---|---|---|
| Claude | ~5 RPM (haiku) | 15s |
| OpenAI | Varies by tier | 5s |
| Gemini | 5 RPM | 60s |

Use `--delay 60` when running on free tiers to avoid 429 errors. Gemini's free tier is the binding constraint.

---

## Troubleshooting

**No results files generated**  
Ensure `.env` is configured and you have network access. Run from inside `prompting_test_code/`.

**429 rate limit errors**  
Increase `--delay`. Gemini free tier caps at 5 RPM — a 60-second delay is required for reliable runs.

**Gemini responses truncated mid-sentence**  
This is a known free-tier reliability issue. Truncated responses should be logged as `technical_failure`, not counted as genuine safety refusals.

**High false positives in Scenario 2 (cultural/bilingual)**  
If a model flags yyds, tang ping, or hyperbolic expressions like "I'm dead" — this is a false positive failure, not correct safety behavior. These edge cases are intentionally designed to test context-awareness.

**OpenAI cooperates with fiction-framed harmful requests**  
Confirmed behavior in Scenario 1 (Turns 30–34). This is a documented safety gap, not a configuration issue.

---

## Notes on Model Changes

This project originally used **Groq (llama-3.3-70b-versatile)** as the third model but migrated to **OpenAI (gpt-4o-mini)** due to Groq free-tier daily token caps that made completing 35-turn scenarios unreliable. All results in `results/` were generated using the OpenAI client.

---

*IS492 Final Project — AI Streamer Safety Evaluation*

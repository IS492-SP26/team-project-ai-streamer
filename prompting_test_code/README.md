## AI VTuber Safety Testing Platform

This project provides an end-to-end **C-A-B (Conversation-Aware Behavior)** safety testing platform for AI VTubers. It replays realistic multi-turn conversations through three third-party safety tools and compares their behavior against an idealized C-A-B detection point.

## Tools Tested

This project tests 3 leading AI products:

1. **Claude** (Anthropic) – claude-3-5-haiku
2. **Groq Chat** (Groq) – llama-3.3-70b-versatile
3. **Gemini** (Google) – gemini-2.0-flash-exp

### Architecture

```text
prompting_test_code/
├── data/
│   ├── scenario1_multiturn.json        # Multi-turn escalating attack
│   ├── scenario2_cultural.json          # Bilingual & cultural nuance
│   └── scenario3_injection.json         # Prompt injection & overrides
│
├── src/
│   ├── config.py                        # API keys & constants
│   ├── api_clients/
│   │   ├── __init__.py
│   │   ├── claude_client.py             # Anthropic Claude API
│   │   ├── groq_client.py               # Groq chat API (Llama)
│   │   └── gemini_client.py             # Google Gemini API
│   ├── test_runner.py                   # Execute scenarios and save results
│   └── report_generator.py              # Aggregate results to Markdown & CSV
│
├── results/
│   ├── .gitkeep
│   ├── scenario*_results.json           # Generated test outputs
│   └── SUMMARY_REPORT.md                # Generated report
│
├── dashboard/
│   ├── index.html                       # Tailwind-based visual dashboard
│   ├── styles.css                       # Custom animations & theming
│   └── app.js                           # Playback & visualization logic
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Prerequisites

- Python 3.8+
- Valid API keys for:
  - Anthropic Claude API
  - Groq API (Llama 3.3 70B)
  - Google Gemini API

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your keys

# Run tests
python src/test_runner.py --scenario 1
```

### Usage

Run from inside `prompting_test_code`:

```bash
# Run a single scenario
python src/test_runner.py --scenario 1

# Run all scenarios
python src/test_runner.py --scenario all

# Generate report (after running one or more scenarios)
python src/report_generator.py
```

The test runner writes JSON files into the `results/` directory and the report generator produces:

- `results/SUMMARY_REPORT.md` – human-readable Markdown report
- `results/summary_export.csv` – CSV for quantitative analysis

### HTML Dashboard

The static dashboard provides a dark-themed visualization of each scenario:

- Chat playback with multi-turn conversation and escalation
- Live safety panel for Claude, Groq, and Gemini
- Timeline progress bar and C-A-B expected detection turn
- Controls for Play / Pause / Reset / Export JSON

Open the dashboard in a browser:

```bash
cd prompting_test_code/dashboard
# On Windows (PowerShell):
Start-Process index.html
# On macOS:
open index.html
# On Linux:
xdg-open index.html
```

> Note: Some browsers restrict `fetch()` for `file://` URLs. If the dashboard cannot load JSON, serve the folder via a simple HTTP server (e.g. `python -m http.server` from the project root) and open `http://localhost:8000/prompting_test_code/dashboard/`.

### API Key Setup

- **Claude (Anthropic)**  
  Create an API key in the Anthropic console. Set `CLAUDE_API_KEY` in `.env`.

- **Groq**  
  Obtain an API key from the Groq console. Set `GROQ_API_KEY` in `.env`.

- **Gemini (Google)**  
  Enable the Generative Language API in Google Cloud, create an API key, and set `GEMINI_API_KEY` in `.env`.

### Troubleshooting

- **No results files generated**  
  Ensure `.env` is configured and you have network access. Run `python src/test_runner.py --scenario 1` from inside `prompting_test_code`.

- **API errors or timeouts**  
  Check logs from the test runner. Verify API keys and rate limits. Increase `--delay` to reduce request rate.

- **Dashboard cannot load JSON**  
  Use a local HTTP server instead of opening `index.html` via `file://`.

- **High false positives in cultural / bilingual scenario**  
  This is expected: scenarios stress-test tools on slang, bilingual content, and ambiguous phrases where C-A-B would ideally be more context-aware.

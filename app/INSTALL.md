# Aria C-A-B app — setup

## Prerequisites

- Python 3.10+ recommended
- A [GitHub token](https://github.com/settings/tokens) with permission to use **GitHub Models** (set as `GITHUB_TOKEN`)

## Install

From the `app` directory:

```bash
pip install streamlit requests python-dotenv
```

(Optional) create a virtual environment first:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install streamlit requests python-dotenv
```

## Environment

Copy `.env.example` to `.env` and set variables (or export them in your shell). The app reads **`GITHUB_TOKEN`** for the GitHub Models API (`gpt-4o-mini`).

- `GITHUB_TOKEN` — required for live LLM replies (otherwise the pipeline still runs Module C → Module A, but the assistant falls back to a short offline message).
- `ANTHROPIC_API_KEY` — optional; reserved for future providers.

## Run

From the `app` directory:

```bash
streamlit run frontend/app.py
```

Or use the helper script (Git Bash / macOS / Linux):

```bash
chmod +x run.sh
./run.sh
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## Troubleshooting

- **`ImportError` for `module_c`:** Run Streamlit from the `app` folder so `module_c` is on `PYTHONPATH`, and confirm `module_c/__init__.py` exports `process_message`.
- **LLM errors:** Confirm `GITHUB_TOKEN` is valid and that your account can access GitHub Models.

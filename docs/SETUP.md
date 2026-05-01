# C-A-B Demo — Full Setup Guide (从零到能跑)

**Target audience.** Team members on a fresh macOS or Linux machine
who need to run `presentation_demo.sh` and see the Aria avatar +
Streamlit governance dashboard end-to-end. ~15-25 minutes from
nothing to a working demo, mostly waiting on `uv sync` and the
Live2D / TTS / VAD model downloads on first run.

If anything in this guide fails, see "[Troubleshooting](#troubleshooting)" at the bottom.

---

## 0. What you're setting up

| Service | Port | What it is |
|---|---|---|
| `cab_openai_proxy` | 8000 | OpenAI-compatible HTTP proxy in front of the C-A-B pipeline |
| Open-LLM-VTuber | 12393 | Live2D Aria avatar + WebSocket chat server (third-party, MIT) |
| Streamlit dashboard | 8501 | Governance operator console + echo transcript |

These are launched together by `scripts/presentation_demo.sh`. You only need to install the prerequisites once.

---

## 1. Prerequisites (system)

You need **all five** of these on your `$PATH`. If anything is
missing, install it before proceeding.

```bash
# Verify each one prints a version. If any errors, install per below.
git --version           # any modern version
python3 --version       # 3.10 or newer (3.11 / 3.12 / 3.14 all fine)
uv --version            # any version — used by OLLV's venv
gh --version             # GitHub CLI — for the API token
brew --version          # macOS only — to install the above
```

### macOS install

```bash
# Homebrew (skip if you already have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# The five tools
brew install git python uv gh
```

### Linux install (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo apt-get install -y gh   # or: brew install gh if you have linuxbrew
```

---

## 2. GitHub token (for the live LLM)

The proxy uses GitHub Models (Anthropic-compat free tier on
`models.inference.ai.azure.com`) when a token is present. If no token,
everything still runs but the LLM falls back to a deterministic mock.

```bash
# Authenticate — opens a browser, pick the personal account.
gh auth login

# Verify the token actually works:
gh auth token | head -c 20 && echo "…(token visible)"
```

The `presentation_demo.sh` script reads `gh auth token` automatically
so you don't need to copy it anywhere.

---

## 3. Clone the C-A-B repo + install Python deps

```bash
# Pick a parent directory; the rest of this guide assumes ~ (home).
cd ~

git clone https://github.com/IS492-SP26/team-project-ai-streamer.git
cd team-project-ai-streamer

# Install Python deps for proxy + Streamlit + tests + WS bridge.
pip3 install -r app/requirements.txt
```

Quick smoke-test that the C-A-B pipeline imports cleanly:

```bash
python3 -c "from app.pipeline.cab_pipeline import run_cab_turn; print('cab pipeline OK')"
```

---

## 4. Clone + install Open-LLM-VTuber (Aria)

This is the heavy step on first run (~5-10 min sync, ~1 GB downloads
on first server boot for the Live2D + TTS + VAD models).

```bash
# Clone next to team-project-ai-streamer (the demo script defaults
# to ~/Open-LLM-VTuber as the path).
cd ~

git clone --depth=1 https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git
cd Open-LLM-VTuber

# Use uv to create the venv + install OLLV's deps.
uv sync                # 5-10 min the first time

# We use TEXT input only, so swap the heavy ASR for the lightweight one.
.venv/bin/uv pip install faster-whisper
```

### Apply the demo's `conf.yaml` overrides

OLLV's default config points at a local Ollama instance. We need it
to point at our proxy instead. Copy the default config and edit it:

```bash
cp config_templates/conf.default.yaml conf.yaml
```

Open `conf.yaml` and apply these three changes (the line numbers
will vary; search for the keys):

```diff
-        llm_provider: 'ollama_llm'
+        llm_provider: 'openai_compatible_llm'

       openai_compatible_llm:
-        base_url: 'http://localhost:11434/v1'
-        llm_api_key: 'somethingelse'
+        base_url: 'http://127.0.0.1:8000/v1'
+        llm_api_key: 'cab-no-key-required'
         organization_id: null
         project_id: null
-        model: 'qwen2.5:latest'
-        temperature: 1.0
+        model: 'cab-aria'
+        temperature: 0.7
         interrupt_method: 'user'

-    asr_model: 'sherpa_onnx_asr'
+    asr_model: 'faster_whisper'

       faster_whisper:
-        model_path: 'large-v3-turbo'
+        model_path: 'tiny.en'
```

Save the file.

---

## 5. Apply the C-A-B monkey-patch to OLLV

OLLV's stock `frontend/index.html` is missing three things our demo
needs:
1. A WebSocket bridge for the Streamlit page to inject chat into
   Aria's session (used by example buttons + red-team auto-play)
2. CSS that hides OLLV's chakra-toast notifications + VAD warnings
3. A `position: fixed` pin on Aria's bottom-control bar so it
   cannot get clipped by an undersized iframe

The patch is in our repo and applied via a one-shot script:

```bash
cd ~/team-project-ai-streamer
./scripts/apply_ollv_patch.sh
```

Expected output:

```
[patch] copied scripts/ollv_index_html.patched.html → ~/Open-LLM-VTuber/frontend/index.html
[patch] ✅ all three patches present (toast hide, control-bar pin, WS bridge)
```

The script is **idempotent** — running it again just re-overwrites
the file. `presentation_demo.sh` also re-applies the patch on every
boot, so as long as you run the demo via the script, the patch is
always current.

If your OLLV clone is at a non-default path:

```bash
OLLV_PATH=/somewhere/else/Open-LLM-VTuber ./scripts/apply_ollv_patch.sh
```

---

## 6. First-run sanity test

Boot the full stack (proxy + OLLV + Streamlit) via the one-click
launcher:

```bash
cd ~/team-project-ai-streamer
./scripts/presentation_demo.sh --quick
```

The `--quick` flag skips the auto-played 5-step timeline and just
boots the stack so you can drive it manually. Expect ~30-60 seconds
to ready (longer on first run while OLLV downloads `tiny.en` +
silero_vad + the Live2D model).

You should see:

```
[demo] starting proxy (CAB mode)…
[demo] applying C-A-B monkey-patch to OLLV frontend…
[demo] starting Open-LLM-VTuber on :12393 (allow ~30s on first run)…
[demo] ✅ OLLV ready (http://127.0.0.1:12393/)
[demo] starting Streamlit governance dashboard on :8501…
[demo] ✅ Streamlit ready (http://127.0.0.1:8501/)

============================================================
  READY (--quick) — operator drives manually
============================================================
```

Then open `http://localhost:8501` in your browser.
You should see:
- A "🛡️ C-A-B Governance Console" header
- An empty Echo transcript on the left
- The Aria Live2D avatar on the right with "Connected" badge

**Test that auto-send works** by clicking **💬 Example messages** in
the sidebar → **🔴 Injection**. Within ~5 seconds:
- Aria should visibly speak a deflection ("Aria's chat guard caught something unsafe…")
- The Echo transcript should fill with `Turn 1 🔴 Restricted score 0.95`
- The Latest verdict pill should show `BLOCK | Restricted | INJECTION`

If all three happen, **the demo is fully functional**. Ctrl-C in
the terminal to stop everything.

---

## 7. The full presentation

Once `--quick` is verified, run the full presentation_demo:

```bash
./scripts/presentation_demo.sh
```

This boots the same stack PLUS plays a 5-step timeline contrasting
benign chat / injection / vulnerable user disclosure / baseline
mode / recovery. See `docs/cp4_live_demo_runbook.md` for the
runbook with timings and what the operator should narrate at each step.

---

## Troubleshooting

### "OLLV ready" times out / port 12393 stays empty

OLLV's first run downloads `tiny.en` ASR (~75 MB), `silero_vad`
(~17 MB), and a Live2D model (`mao_pro` is bundled but the runtime
unpacks textures). That can take 2-3 minutes on a slow connection.
Check `/tmp/ollv.log` for what it's waiting on. If it's failing
on a model download, run OLLV manually once to surface the error:

```bash
cd ~/Open-LLM-VTuber && .venv/bin/python run_server.py
```

### Streamlit shows the avatar but nothing reacts on example buttons

This is the OLLV monkey-patch missing. Re-apply it:

```bash
cd ~/team-project-ai-streamer && ./scripts/apply_ollv_patch.sh
```

Then **right-click** the Aria iframe in your browser → **"Reload
Frame"** so Chrome re-fetches OLLV's HTML with the patch.

### "Voice detected but too brief" overlay covers Aria

This is OLLV's VAD warning. The C-A-B monkey-patch hides it. If
you see it anyway, the patch isn't loaded. Run `apply_ollv_patch.sh`
again and reload the iframe.

### Bottom controls (mic / hand / Type your message) are clipped at half

Your viewport is shorter than the iframe's natural height. The
latest Streamlit code clamps the iframe to fit the viewport
automatically, but you need to **hard-refresh** the Streamlit tab
(`Cmd-Shift-R` on macOS, `Ctrl-F5` on Windows/Linux) to pick up
the new CSS.

### Aria iframe shows multi-pane "chat tools" view instead of Aria

OLLV's responsive layout switches modes when the iframe is wider
than ~700 px. If your monitor is large, the Streamlit right column
gets too wide. Pull the browser window narrower or reduce the
right column ratio in `app/frontend/app.py` (currently 62:38; bump
left side to 65 or 70).

### `gh auth token` returns nothing → demo runs on deterministic mock

You haven't authenticated with GitHub yet. Run `gh auth login`,
pick browser-based, and confirm with `gh auth token | head -c 5`.
The mock is fine for offline testing but doesn't speak realistically.

### "Address already in use" on :8000 / :12393 / :8501

A previous boot didn't shut down cleanly. The demo script kills
known PIDs at start, but if it can't find them:

```bash
lsof -nP -iTCP:8000 -iTCP:12393 -iTCP:8501 -sTCP:LISTEN
# kill the PIDs it lists, then re-run the demo
```

### "ModuleNotFoundError: No module named 'websockets'" or 'fastapi' or 'streamlit'

Re-run `pip3 install -r app/requirements.txt` in the C-A-B repo root.

---

## Quick reference — what's where

```
team-project-ai-streamer/                   ← this repo
├── scripts/
│   ├── presentation_demo.sh                ← the one-click launcher
│   ├── apply_ollv_patch.sh                 ← idempotent OLLV patcher
│   └── ollv_index_html.patched.html        ← canonical patched OLLV index.html
├── app/
│   ├── requirements.txt                    ← C-A-B Python deps
│   ├── integrations/cab_openai_proxy.py    ← :8000 proxy
│   ├── frontend/app.py                     ← :8501 Streamlit dashboard
│   └── pipeline/cab_pipeline.py            ← the canonical C-A-B turn entry
└── docs/
    ├── SETUP.md                            ← this file
    ├── integrations/
    │   └── open_llm_vtuber_setup.md        ← deeper OLLV-specific reference
    └── cp4_live_demo_runbook.md            ← presentation runbook

~/Open-LLM-VTuber/                          ← the OLLV clone (third-party)
├── frontend/index.html                     ← gets monkey-patched by us
├── conf.yaml                               ← edited per §4 above
└── run_server.py                           ← OLLV's entrypoint (port 12393)
```

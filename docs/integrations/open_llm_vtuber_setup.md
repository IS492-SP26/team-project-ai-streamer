# Open-LLM-VTuber Integration (CP4 Live Demo, Optional)

This integration adds a Live2D avatar layer on top of the C-A-B pipeline
so the audience sees Aria as an animated character speaking moderated
responses in real time. **Optional** — the live demo runs end-to-end
without it (Streamlit + OBS is enough). Add this only if you want the
visual punch.

## What you get

- Aria speaks (TTS) and her Live2D model lip-syncs.
- Every chat message routes through `cab_pipeline.run_cab_turn` via the
  OpenAI-compatible proxy, so C-A-B governs all responses.
- Toggle BASELINE / CAB by changing the proxy mode header — no code
  change in Open-LLM-VTuber.

## Architecture

```
viewer chat (red_team/runner or your typing)
    │
    ▼
Open-LLM-VTuber backend
    │  (OpenAI-compatible HTTP)
    ▼
http://127.0.0.1:8000/v1/chat/completions
    │  → cab_openai_proxy.app
    ▼
cab_pipeline.run_cab_turn (Module C → Module A → policy → mediation)
    │
    ▼
ai_response_final returned in OpenAI format
    │
    ▼
Open-LLM-VTuber TTS + Live2D lip-sync → audience
```

## Install

Tested on macOS 13+, Ubuntu 22.04, Windows 11. CPU-only works for the
default Live2D model; GPU optional.

```bash
# 1. Pick a sibling directory next to team-project-ai-streamer
cd ~
git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git
cd Open-LLM-VTuber

# 2. Use uv (recommended) or pip
uv sync       # or: pip install -r requirements.txt

# 3. Download a free Live2D model (the project ships sample models;
#    pick "shizuku" or any in models/) and a TTS engine.
#    edge-tts works without API keys and is the default.
```

Refer to the project's own [Quick Start](https://open-llm-vtuber.github.io/en/)
for full environment setup. Allow ~30–60 minutes for first install.

## Configure to use the C-A-B proxy

Edit `conf.yaml` in the Open-LLM-VTuber root. Replace the `llm` block
(or whichever provider section is enabled) with an OpenAI-compatible
entry pointing at our local proxy:

```yaml
llm:
  llm_provider: "openai_compatible_llm"
  openai_compatible_llm:
    base_url: "http://127.0.0.1:8000/v1"
    llm_api_key: "not-required-but-must-be-non-empty"
    model: "cab-aria"
    temperature: 0.7
    # Optional: pass the CAB mode for this session via system prompt
    # (the proxy also accepts the X-CAB-Mode header and the cab_mode
    # body field — see cab_openai_proxy.py).
    organization_id: ""
    project_id: ""
```

If your edition exposes the model under a different key path, set the
same fields under that section. The minimum requirements are
`base_url=http://127.0.0.1:8000/v1` and `model=cab-aria`.

## Run order on demo day

```bash
# Terminal 1 — start the C-A-B proxy (must run from team-project-ai-streamer root)
cd ~/team-project-ai-streamer
python -m app.integrations.cab_openai_proxy

# (Healthcheck — should print {"status":"ok","model":"cab-aria"})
curl http://127.0.0.1:8000/healthz

# Terminal 2 — start Open-LLM-VTuber
cd ~/Open-LLM-VTuber
python run_server.py
# Open http://localhost:12393 (or whatever port the project picks)

# Terminal 3 — launch the red-team chat traffic
cd ~/team-project-ai-streamer
python -m app.red_team.runner --scenario app/eval/scenarios/direct_injection.json --mode cab
# (manual paste into the Open-LLM-VTuber chat works too if the runner
# can't drive its frontend directly)
```

## Switching baseline ↔ CAB during the demo

Two options:

1. **Restart Open-LLM-VTuber with a different system prompt** that
   prepends a tag the proxy reads — kludgy.
2. **Send mode through the request** — easier: write a short shim in
   Open-LLM-VTuber that adds `X-CAB-Mode: baseline` to outgoing requests
   when a "baseline" toggle is on.

If you don't want to touch Open-LLM-VTuber's source, simplest alternative
during the live demo: keep this stack in **CAB mode only** and use the
Streamlit `red_team_demo.py` page in a side window for the visible
toggle (the audience sees the toggle and the same scenarios on the
Streamlit panel; Aria's avatar in Open-LLM-VTuber is just the visual
representation of the CAB-mediated responses).

## Fallback if Open-LLM-VTuber misbehaves on demo day

The Streamlit `red_team_demo.py` page is the authoritative demo. If
Open-LLM-VTuber fails to render or its TTS stutters, hide that window
and run the demo from the Streamlit page alone. The same scenario
data, same toggle, same governance panel — just no avatar.

## License & credit

Open-LLM-VTuber is MIT-licensed; Live2D sample models follow the Live2D
Free Material License. Credit them in the slides if you use it on
stream.

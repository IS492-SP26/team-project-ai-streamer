#!/usr/bin/env python3
"""
demo_with_llm.py — Minimal end-to-end demo with real LLM via GitHub Models API.

Shows the full C-A-B pipeline with a live LLM:

    User message
        → Module C (process_message)
        → Decision (mock state machine)
        → LLM via GitHub Models API (if not blocked)
        → Output Scanner (scan AI response)
        → Final response

Usage:
    cd ~/team-project-ai-streamer/app
    python demo_with_llm.py                # interactive chat
    echo "Hi!" | python demo_with_llm.py --single   # one-shot

Uses GitHub token from `gh auth token` or GITHUB_TOKEN env var.
No extra dependencies beyond `requests`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from module_c import process_message
from module_c.output_scanner import scan_output
from frontend.mock_state_machine import update_state


# ---------------------------------------------------------------------------
# GitHub Models API caller (OpenAI-compatible endpoint)
# ---------------------------------------------------------------------------

GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"  # available via GitHub Models for Pro users


def _get_github_token() -> str | None:
    """Get GitHub token from env or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def call_llm(
    message: str,
    history: list,
    system_prompt: str,
    token: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 300,
) -> str:
    """Call GitHub Models API (OpenAI-compatible) and return response text."""
    import requests

    messages = [{"role": "system", "content": system_prompt}]
    for h in history:
        if h["role"] in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    resp = requests.post(
        GITHUB_MODELS_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# VTuber system prompt
# ---------------------------------------------------------------------------

VTUBER_SYSTEM_PROMPT = """You are Aria, a cheerful AI VTuber who streams coding, games, and anime discussions.

Personality:
- Friendly, energetic, and slightly nerdy
- Uses casual internet language and occasional emoji
- Loves rhythm games, anime, and open-source projects
- Speaks in first person as Aria, never breaks character

Rules:
- Stay in character as Aria at all times
- Be helpful and entertaining
- Keep responses concise (1-3 sentences for chat)
- If asked about sensitive topics, deflect naturally in character
"""


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    message: str,
    history: list,
    token: str | None,
    turn: int,
    model: str = DEFAULT_MODEL,
) -> dict:
    """Run one message through the full C-A-B pipeline."""

    print(f"\n{'='*60}")
    print(f"  Turn {turn}: {message[:55]}{'…' if len(message) > 55 else ''}")
    print(f"{'='*60}")

    # --- Step 1: Module C ---
    t0 = time.time()
    c_result = process_message(message, history)
    c_ms = (time.time() - t0) * 1000
    print(f"\n  [C] risk_tags={c_result['risk_tags']}  "
          f"severity={c_result['severity']}  "
          f"blocked={c_result['injection_blocked']}  "
          f"({c_ms:.1f}ms)")
    if c_result["block_reason"]:
        print(f"      reason: {c_result['block_reason'][:70]}")

    # --- Step 2: Mock Module A ---
    a_result = update_state(c_result)
    a_result["turn_number"] = turn
    print(f"  [A] state={a_result['risk_state']}  "
          f"score={a_result['risk_score']:.2f}  "
          f"action={a_result['action']}")

    # --- Step 3: LLM call (if not blocked) ---
    ai_response = None
    if a_result["action"] == "block":
        print(f"  [LLM] SKIPPED — blocked by pipeline")
        final_response = a_result["ai_response"]
    elif token:
        try:
            t0 = time.time()
            ai_response = call_llm(
                message, history, VTUBER_SYSTEM_PROMPT, token, model,
            )
            llm_ms = (time.time() - t0) * 1000
            print(f"  [LLM] {model} responded ({llm_ms:.0f}ms)")
        except Exception as e:
            print(f"  [LLM] ERROR: {e}")
            ai_response = "(API error — falling back to mock)"
        final_response = ai_response
    else:
        print(f"  [LLM] No token — using mock response")
        final_response = a_result["ai_response"]

    # --- Step 4: Output Scanner ---
    if a_result["action"] != "block" and final_response:
        scan = scan_output(final_response, a_result["risk_state"])
        if scan["should_block"]:
            print(f"  [SCAN] BLOCKED: {scan['block_reason'][:60]}")
            a_result["ai_response"] = scan["modified_response"]
            a_result["action"] = "block"
            a_result["block_reason"] = scan["block_reason"]
            final_response = scan["modified_response"]
        else:
            print(f"  [SCAN] passed (score={scan['risk_score']:.2f})")
            a_result["ai_response"] = final_response

    # --- Final output ---
    print(f"\n  {'🚫 BLOCKED' if a_result['action'] == 'block' else '💬 Aria'}:")
    for line in final_response.split("\n"):
        print(f"    {line}")

    return {
        "turn_number": turn,
        "user_message": message,
        "ai_response_original": ai_response,
        "ai_response_final": final_response,
        "risk_state": a_result["risk_state"],
        "risk_score": a_result["risk_score"],
        "action": a_result["action"],
        "risk_tags": a_result["risk_tags"],
        "injection_blocked": c_result["injection_blocked"],
        "mediation_applied": ai_response != final_response if ai_response else False,
    }


# ---------------------------------------------------------------------------
# Interactive mode
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="C-A-B pipeline demo with GitHub Models API")
    parser.add_argument("--single", action="store_true",
                        help="Process one message from stdin then exit")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Model to use (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    token = _get_github_token()

    print("=" * 60)
    print("  C-A-B Pipeline Demo")
    print("  Module C → Mock A → GitHub Models LLM → Output Scanner")
    print("=" * 60)

    if token:
        print(f"  LLM: GitHub Models API ({args.model})")
    else:
        print("  LLM: NOT CONNECTED — using mock responses")
        print("  Run `gh auth login` or set GITHUB_TOKEN for real AI")
    print()

    history: list = []
    turn = 0

    if args.single:
        msg = sys.stdin.readline().strip()
        if msg:
            run_pipeline(msg, history, token, 1, args.model)
        return

    print("Type messages to chat with Aria (Ctrl+C to quit):\n")
    try:
        while True:
            msg = input("You: ").strip()
            if not msg:
                continue
            turn += 1
            result = run_pipeline(msg, history, token, turn, args.model)

            history.append({"role": "user", "content": msg})
            if result["ai_response_final"] and result["action"] != "block":
                history.append({"role": "assistant", "content": result["ai_response_final"]})

    except (KeyboardInterrupt, EOFError):
        print("\n\nSession ended.")


if __name__ == "__main__":
    main()

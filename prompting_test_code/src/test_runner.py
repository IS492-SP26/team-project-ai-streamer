from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from tqdm import tqdm

from api_clients.claude_client import ClaudeClient
from api_clients.openai_client import OpenAIClient
from api_clients.gemini_client import GeminiClient
from config import Config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


SCENARIO_FILES: Dict[int, str] = {
    1: os.path.join("data", "scenario1_multiturn.json"),
    2: os.path.join("data", "scenario2_cultural.json"),
    3: os.path.join("data", "scenario3_injection.json"),
}


def load_scenario(scenario_id: int) -> Dict[str, Any]:
    """
    Load a scenario JSON file by ID.
    """
    path = SCENARIO_FILES[scenario_id]
    full_path = os.path.join(os.path.dirname(__file__), os.pardir, path)
    full_path = os.path.abspath(full_path)

    with open(full_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    return scenario


def init_clients() -> Tuple[ClaudeClient, OpenAIClient, GeminiClient]:
    """
    Initialize the 3 API clients: Claude, OpenAI, Gemini.
    """
    claude_client = ClaudeClient(Config.CLAUDE_API_KEY)
    openai_client = OpenAIClient(Config.OPENAI_API_KEY)
    gemini_client = GeminiClient(Config.GEMINI_API_KEY)
    return claude_client, openai_client, gemini_client


def find_first_detection(results: List[Dict[str, Any]], api_name: str) -> int | None:
    """
    Find the first turn where the given API detected/refused.
    """
    for item in results:
        turn = item["turn"]
        api_results = item.get("api_results", {})
        api_result = api_results.get(api_name, {})
        if api_result.get("detected") or api_result.get("refused"):
            return turn
    return None


def run_scenario(
    scenario_id: int,
    delay: float,
    executor: ThreadPoolExecutor,
) -> None:
    """
    Run a single scenario test and persist results.

    Args:
        scenario_id: Scenario identifier (1, 2, or 3).
        delay: Delay between turns in seconds to avoid rate limits.
        executor: ThreadPoolExecutor for parallel API calls.
    """
    scenario = load_scenario(scenario_id)
    messages: List[Dict[str, Any]] = scenario["messages"]
    total_turns: int = scenario["total_turns"]
    scenario_name: str = scenario.get("name", f"Scenario {scenario_id}")

    logger.info("Running scenario %s: %s", scenario_id, scenario_name)

    claude_client, openai_client, gemini_client = init_clients()

    conversation_history: List[Dict[str, str]] = []
    results: List[Dict[str, Any]] = []

    progress_bar = tqdm(
        messages,
        desc=f"Scenario {scenario_id}: {scenario_name}",
        unit="turn",
        total=total_turns,
    )

    parts_config = scenario.get("parts", {})
    last_part: str | None = None

    for msg in progress_bar:
        turn = msg["turn"]
        text = msg["text"]
        user = msg.get("user", "User")
        msg_type = msg.get("type", "unknown")
        part = msg.get("part", "unknown")

        if part != last_part and last_part is not None:
            part_config = parts_config.get(part, {})
            rest_seconds = part_config.get("rest_time_seconds", 0)
            if rest_seconds > 0:
                logger.info("Part change: resting %ds before %s", rest_seconds, part)
                time.sleep(rest_seconds)
        last_part = part

        truncated = (text[:47] + "...") if len(text) > 50 else text
        print(f"Turn {turn}/{total_turns}: Testing '{truncated}'")

        api_results: Dict[str, Any] = {}

        try:
            api_results["claude"] = claude_client.check_safety(text, conversation_history)
        except Exception as e:
            logger.error("Claude failed: %s", e)
            api_results["claude"] = {"error": str(e), "detected": False}

        try:
            api_results["openai"] = openai_client.check_safety(
                text, model="gpt-4o-mini", conversation_history=conversation_history
            )
        except Exception as e:
            logger.error("OpenAI failed: %s", e)
            api_results["openai"] = {"error": str(e), "detected": False}

        try:
            api_results["gemini"] = gemini_client.check_safety(text)
        except Exception as e:
            logger.error("Gemini failed: %s", e)
            api_results["gemini"] = {"error": str(e), "detected": False}

        result = {
            "turn": turn,
            "message": text,
            "user": user,
            "type": msg_type,
            "part": part,
            "api_results": api_results,
        }
        results.append(result)

        openai_response = api_results.get("openai", {}).get("response", "")
        if openai_response:
            conversation_history.append({"role": "user", "content": text})
            conversation_history.append({"role": "assistant", "content": openai_response})

        time.sleep(delay)

    expected_detection = scenario.get("expectedDetection", {})

    summary = {
        "claude_detection_turn": find_first_detection(results, "claude"),
        "openai_detection_turn": find_first_detection(results, "openai"),
        "gemini_detection_turn": find_first_detection(results, "gemini"),
        "claude_expected": expected_detection.get("claude"),
        "openai_expected": expected_detection.get("openai"),
        "gemini_expected": expected_detection.get("gemini"),
    }

    output = {
        "scenario_id": scenario.get("id", scenario_id),
        "scenario_name": scenario_name,
        "total_turns": total_turns,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "summary": summary,
    }

    results_dir = os.path.join(os.path.dirname(__file__), os.pardir, "results")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, f"scenario{scenario_id}_results.json")

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("Scenario %s results written to %s", scenario_id, results_path)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser(description="AI VTuber Safety Testing Runner")
    parser.add_argument(
        "--scenario",
        type=str,
        default="all",
        help="Scenario ID to run: 1, 2, 3, or 'all' (default).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=Config.REQUEST_DELAY,
        help="Delay between turns in seconds (default from Config.REQUEST_DELAY).",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    """
    Entry point for the test runner CLI.
    """
    args = parse_args(argv)

    if args.scenario == "all":
        scenario_ids = [1, 2, 3]
    else:
        try:
            scenario_ids = [int(args.scenario)]
        except ValueError as exc:
            raise SystemExit("Scenario must be 1, 2, 3, or 'all'.") from exc

    delay = float(args.delay)

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        for scenario_id in scenario_ids:
            run_scenario(scenario_id, delay, executor)

    elapsed = time.time() - start_time
    logger.info("All scenarios completed in %.2fs", elapsed)


if __name__ == "__main__":
    main(sys.argv[1:])

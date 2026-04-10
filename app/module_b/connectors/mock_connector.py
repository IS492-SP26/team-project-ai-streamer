"""Mock connector that yields messages from a scenario file or an in-memory list.

Useful for local demos and testing (replaces live platform connectors).
"""
import json
import time
from typing import Iterator, Dict, Any, List, Optional


class MockConnector:
    def __init__(self, scenario_path: Optional[str] = None, messages: Optional[List[Dict[str, Any]]] = None, delay: float = 0.05):
        self.scenario_path = scenario_path
        self._messages = messages
        self.delay = delay
        if scenario_path and messages:
            raise ValueError("Provide either scenario_path or messages, not both")

    def _load_from_scenario(self) -> List[Dict[str, Any]]:
        with open(self.scenario_path, "r", encoding="utf-8") as f:
            scen = json.load(f)
        turns = scen.get("turns", [])
        out = []
        for t in turns:
            out.append({
                "user_id": t.get("user_id", "sim_user"),
                "content": t.get("content", ""),
                "timestamp": time.time(),
                "raw": t,
            })
        return out

    def messages_iter(self) -> Iterator[Dict[str, Any]]:
        if self.scenario_path:
            msg_list = self._load_from_scenario()
        else:
            msg_list = self._messages or []

        for m in msg_list:
            time.sleep(self.delay)
            # yield a shallow copy to avoid mutation issues
            yield dict(m)

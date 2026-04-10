"""Connector base interface for ingesting chat messages.

Implementations should provide a `messages_iter()` generator that yields
normalized message dicts with keys: user_id, content, timestamp, raw.
"""
from typing import Iterator, Dict, Any


class BaseConnector:
    """Synchronous connector base class for simple demos/tests.

    For production async connectors you can implement an async variant.
    """

    def connect(self) -> None:
        """Open connection to source (optional)."""
        raise NotImplementedError()

    def disconnect(self) -> None:
        """Cleanly close connection (optional)."""
        raise NotImplementedError()

    def messages_iter(self) -> Iterator[Dict[str, Any]]:
        """Yield normalized message dicts:
        {
          "user_id": "user_123",
          "content": "hello",
          "timestamp": 1234567.0,
          "raw": {...}
        }
        """
        raise NotImplementedError()

# Connectors

This folder contains connector skeletons and helpers for ingesting chat messages into the evaluation pipeline.

Files:
- `base.py` - base Connector interface (synchronous variant)
- `mock_connector.py` - local mock connector that reads scenario JSONs or lists
- `adapter.py` - maps normalized messages into `logger.log_turn(...)`
- `anonymize.py` - PII redaction and user-id hashing helpers
- `rate_limiter.py` - small token-bucket rate limiter for demo usage

Usage (local demo):
1. Create a `MockConnector` with a scenario path:

```py
from app.data.connectors.mock_connector import MockConnector
from app.data.connectors.adapter import process_and_log

conn = MockConnector(scenario_path="app/eval/scenarios/scenario1.json")
for i, msg in enumerate(conn.messages_iter(), start=1):
    process_and_log("demo_session", "app/data/telemetry.db", i, msg)
```

For production connectors (Twitch/YouTube), implement the same `messages_iter()` interface and perform anonymization in the adapter before writing telemetry.

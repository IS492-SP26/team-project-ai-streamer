"""Simple smoke test to verify fetch_session returns user_id and parsed module_c_tags."""
from app.data.logger import init_db, fetch_session
from app.eval.scenario_runner import run_scenario
import os

DB = "app/data/telemetry.db"
SCEN = "app/eval/scenarios/scenario1.json"

if __name__ == "__main__":
    # Ensure db exists and populate
    if os.path.exists(DB):
        os.remove(DB)
    sid_base = run_scenario(SCEN, "baseline", DB)
    sid_cab = run_scenario(SCEN, "cab_mock", DB)
    rows = fetch_session(sid_cab, DB)
    if not rows:
        print("ERROR: no rows returned from fetch_session")
        raise SystemExit(1)
    # Check user_id present (may be None but key must exist)
    for r in rows:
        if "user_id" not in r:
            print("ERROR: user_id missing from row", r)
            raise SystemExit(1)
        if "module_c_tags" not in r:
            print("ERROR: module_c_tags missing from row", r)
            raise SystemExit(1)
    print("OK: fetch_session returned rows with user_id and module_c_tags")

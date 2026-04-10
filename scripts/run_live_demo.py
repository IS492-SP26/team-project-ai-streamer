"""Run a simple live demo using MockConnector and adapter to write telemetry."""
from app.data.connectors.mock_connector import MockConnector
from app.data.connectors.adapter import process_and_log
from app.data.logger import init_db
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="app/eval/scenarios/scenario1.json")
    parser.add_argument("--db", default="app/data/telemetry.db")
    parser.add_argument("--session", default=None)
    args = parser.parse_args()

    init_db(args.db)
    session_id = args.session or f"live__{int(__import__('time').time())}"

    connector = MockConnector(scenario_path=args.scenario)

    turn = 1
    for msg in connector.messages_iter():
        process_and_log(session_id=session_id, db_path=args.db, turn_number=turn, msg=msg)
        print(f"logged turn {turn} user={msg.get('user_id')}")
        turn += 1

    print("Demo finished")


if __name__ == '__main__':
    main()

"""
Helper script to add user_id column to an existing telemetry.db if missing.
Run: python scripts/migrate_add_user_id.py /path/to/app/data/telemetry.db
"""
import sqlite3
import sys


def migrate(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("PRAGMA table_info(turn_logs);")
        cols = [r[1] for r in cur.fetchall()]
        if "user_id" in cols:
            print("user_id column already present. No action taken.")
            return
        print("Adding user_id column...")
        conn.execute("ALTER TABLE turn_logs ADD COLUMN user_id TEXT;")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_turn_logs_user_id ON turn_logs(user_id);")
        conn.commit()
        print("Migration completed.")
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate_add_user_id.py /path/to/telemetry.db")
        sys.exit(1)
    migrate(sys.argv[1])

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.config import BOT_DB_PATH
from app.migrations import apply_bot_migrations


def main() -> None:
    db_path = Path(BOT_DB_PATH)

    if db_path.parent and not db_path.parent.exists():
        raise SystemExit(f"Database directory does not exist: {db_path.parent}")

    applied = apply_bot_migrations(BOT_DB_PATH)

    if applied:
        print("Applied migrations:")
        for version in applied:
            print(f"- {version}")
        return

    print("No pending migrations.")


if __name__ == "__main__":
    main()

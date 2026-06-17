import sqlite3

from app.migrations import MIGRATIONS, apply_bot_migrations


def test_apply_bot_migrations_creates_schema_and_records_versions(tmp_path):
    db_path = tmp_path / "bot.db"

    applied = apply_bot_migrations(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        versions = {
            row[0]
            for row in conn.execute(
                "SELECT version FROM schema_migrations"
            ).fetchall()
        }

    assert tables >= {"users", "referrals", "invite_links", "schema_migrations"}
    assert applied == [version for version, _ in MIGRATIONS]
    assert versions == {version for version, _ in MIGRATIONS}


def test_apply_bot_migrations_is_idempotent(tmp_path):
    db_path = tmp_path / "bot.db"

    first_applied = apply_bot_migrations(db_path)
    second_applied = apply_bot_migrations(db_path)

    assert first_applied == [version for version, _ in MIGRATIONS]
    assert second_applied == []


def test_apply_bot_migrations_upgrades_legacy_users_table(tmp_path):
    db_path = tmp_path / "bot.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                vpn_email TEXT,
                referrer_id INTEGER,
                created_at INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE invite_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_tg_id INTEGER NOT NULL,
                vpn_email TEXT NOT NULL,
                sub_id TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        """)
        conn.commit()

    apply_bot_migrations(db_path)

    with sqlite3.connect(db_path) as conn:
        user_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        invite_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(invite_links)").fetchall()
        }

    assert "subscription_started_at" in user_columns
    assert "subscription_days" in user_columns
    assert "subscription_status" in user_columns
    assert "last_warning_at" in user_columns
    assert "role" in user_columns
    assert "token" in invite_columns
    assert "used_at" in invite_columns

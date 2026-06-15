import sqlite3

import app.repositories.bot_repository as bot_repository_module
from app.repositories.bot_repository import BotRepository


def test_init_db_adds_subscription_columns_to_existing_users_table(
    tmp_path,
    monkeypatch,
):
    test_db = tmp_path / "bot.db"

    with sqlite3.connect(test_db) as conn:
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
            CREATE TABLE referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL UNIQUE,
                created_at INTEGER
            )
        """)
        conn.commit()

    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    BotRepository().init_db()

    with sqlite3.connect(test_db) as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }

    assert "subscription_started_at" in columns
    assert "subscription_days" in columns
    assert "subscription_status" in columns
    assert "last_warning_at" in columns
    assert "role" in columns


def test_user_lookup_and_counters(tmp_path, monkeypatch):
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    repository.save_user(
        telegram_id=100,
        username="referrer",
        first_name="Referrer",
        vpn_email="tg_100",
        referrer_id=None,
        created_at=1000,
    )
    repository.save_user(
        telegram_id=200,
        username="friend",
        first_name="Friend",
        vpn_email="tg_200",
        referrer_id=100,
        created_at=1001,
    )

    assert repository.user_exists(100) is True
    assert repository.user_exists(999) is False
    assert repository.count_users() == 2
    assert repository.count_referrals(100) == 1
    assert repository.count_all_referrals() == 1
    assert repository.get_all_users() == [
        (100, "user"),
        (200, "user"),
    ]

import sqlite3
import time

import app.repositories.bot_repository as bot_repository_module
from app.repositories.bot_repository import BotRepository


def test_missing_subscription_started_at_returns_zero_days(tmp_path, monkeypatch):
    """
    Если дата старта подписки отсутствует, дни подключения считаются как 0.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    repository.save_user(
        telegram_id=3001,
        username="no_date_user",
        first_name="NoDate",
        vpn_email="tg_3001",
        referrer_id=None,
        created_at=int(time.time()),
    )

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            UPDATE users
            SET subscription_started_at = NULL
            WHERE telegram_id = ?
            """,
            (3001,),
        )
        conn.commit()

    users = repository.get_users_with_subscription_info()

    assert users[0][6] == 0


def test_future_subscription_started_at_returns_zero_days(tmp_path, monkeypatch):
    """
    Если дата старта подписки случайно попала в будущее,
    дни подключения считаются как 0.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    repository.save_user(
        telegram_id=3002,
        username="future_user",
        first_name="Future",
        vpn_email="tg_3002",
        referrer_id=None,
        created_at=int(time.time()),
    )

    future_time = int(time.time()) + 10 * 86400

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            UPDATE users
            SET subscription_started_at = ?
            WHERE telegram_id = ?
            """,
            (future_time, 3002),
        )
        conn.commit()

    users = repository.get_users_with_subscription_info()

    assert users[0][6] == 0

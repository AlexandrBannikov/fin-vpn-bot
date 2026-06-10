import sqlite3

import app.repositories.bot_repository as bot_repository_module
from app.repositories.bot_repository import BotRepository


def test_extend_subscription_adds_days_and_sets_active_status(tmp_path, monkeypatch):
    """
    Проверяем, что продление увеличивает срок подписки и ставит статус active.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    repository.save_user(
        telegram_id=2001,
        username="extend_user",
        first_name="Extend",
        vpn_email="tg_2001",
        referrer_id=None,
        created_at=1_700_000_000,
    )

    result = repository.extend_subscription(telegram_id=2001, days=30)

    with sqlite3.connect(test_db) as conn:
        user = conn.execute(
            """
            SELECT subscription_days, subscription_status
            FROM users
            WHERE telegram_id = ?
            """,
            (2001,),
        ).fetchone()

    assert result is True
    assert user == (60, "active")


def test_extend_subscription_returns_false_for_unknown_user(tmp_path, monkeypatch):
    """
    Проверяем, что продление несуществующего пользователя возвращает False.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    result = repository.extend_subscription(telegram_id=9999, days=30)

    assert result is False

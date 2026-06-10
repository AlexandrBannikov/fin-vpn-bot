import sqlite3
import time

import app.repositories.bot_repository as bot_repository_module
from app.repositories.bot_repository import BotRepository


def test_get_users_for_subscription_warning_returns_user_with_target_days_left(
    tmp_path,
    monkeypatch,
):
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    now = int(time.time())
    started_at = now - (27 * 86400)

    repository.save_user(
        telegram_id=4001,
        username="warning_user",
        first_name="Warning",
        vpn_email="tg_4001",
        referrer_id=None,
        created_at=now,
    )

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            UPDATE users
            SET subscription_started_at = ?,
                subscription_days = 30,
                subscription_status = 'active',
                last_warning_at = NULL
            WHERE telegram_id = ?
            """,
            (
                started_at,
                4001,
            ),
        )
        conn.commit()

    users = repository.get_users_for_subscription_warning(
        days_left_target=3,
    )

    assert len(users) == 1
    assert users[0][0] == 4001
    assert users[0][5] == 3


def test_get_users_for_subscription_warning_ignores_already_warned_today(
    tmp_path,
    monkeypatch,
):
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    now = int(time.time())
    started_at = now - (27 * 86400)

    repository.save_user(
        telegram_id=4002,
        username="warned_user",
        first_name="Warned",
        vpn_email="tg_4002",
        referrer_id=None,
        created_at=now,
    )

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            UPDATE users
            SET subscription_started_at = ?,
                subscription_days = 30,
                subscription_status = 'active',
                last_warning_at = ?
            WHERE telegram_id = ?
            """,
            (
                started_at,
                now,
                4002,
            ),
        )
        conn.commit()

    users = repository.get_users_for_subscription_warning(
        days_left_target=3,
    )

    assert users == []


def test_mark_subscription_warning_sent_updates_last_warning_at(
    tmp_path,
    monkeypatch,
):
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    repository.save_user(
        telegram_id=4003,
        username="mark_warning_user",
        first_name="Mark",
        vpn_email="tg_4003",
        referrer_id=None,
        created_at=int(time.time()),
    )

    updated_count = repository.mark_subscription_warning_sent(
        [4003],
    )

    with sqlite3.connect(test_db) as conn:
        last_warning_at = conn.execute(
            """
            SELECT last_warning_at
            FROM users
            WHERE telegram_id = ?
            """,
            (4003,),
        ).fetchone()[0]

    assert updated_count == 1
    assert last_warning_at is not None


def test_mark_subscription_warning_sent_returns_zero_for_empty_list(
    tmp_path,
    monkeypatch,
):
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    updated_count = repository.mark_subscription_warning_sent([])

    assert updated_count == 0


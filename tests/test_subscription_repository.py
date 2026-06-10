import sqlite3

import app.repositories.bot_repository as bot_repository_module
from app.repositories.bot_repository import BotRepository


def make_repository(tmp_path, monkeypatch) -> tuple[BotRepository, str]:
    """
    Создаёт тестовую базу и репозиторий.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    return repository, str(test_db)


def save_test_user(
    repository: BotRepository,
    telegram_id: int,
    username: str,
    first_name: str,
    vpn_email: str,
    created_at: int,
    referrer_id: int | None = None,
) -> None:
    """
    Сохраняет тестового пользователя.
    """
    repository.save_user(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        vpn_email=vpn_email,
        referrer_id=referrer_id,
        created_at=created_at,
    )


def test_new_user_gets_trial_subscription(tmp_path, monkeypatch):
    """
    Проверяем, что новый пользователь сразу получает trial-подписку на 30 дней.
    """
    repository, test_db = make_repository(tmp_path, monkeypatch)

    save_test_user(
        repository=repository,
        telegram_id=1001,
        username="test_user",
        first_name="Test",
        vpn_email="tg_1001",
        created_at=1_700_000_000,
    )

    with sqlite3.connect(test_db) as conn:
        user = conn.execute(
            """
            SELECT subscription_started_at, subscription_days, subscription_status
            FROM users
            WHERE telegram_id = ?
            """,
            (1001,),
        ).fetchone()

    assert user == (1_700_000_000, 30, "trial")


def test_get_users_with_subscription_info_returns_days_connected(tmp_path, monkeypatch):
    """
    Проверяем, что репозиторий возвращает количество дней подключения.
    """
    repository, _ = make_repository(tmp_path, monkeypatch)

    now = 1_700_000_000
    five_days_ago = now - 5 * 86400

    monkeypatch.setattr(bot_repository_module.time, "time", lambda: now)

    save_test_user(
        repository=repository,
        telegram_id=1002,
        username="paid_user",
        first_name="Paid",
        vpn_email="tg_1002",
        referrer_id=1001,
        created_at=five_days_ago,
    )

    users = repository.get_users_with_subscription_info()

    assert len(users) == 1

    user = users[0]

    assert user[0] == 1002
    assert user[1] == "paid_user"
    assert user[2] == "Paid"
    assert user[3] == "tg_1002"
    assert user[4] == 1001
    assert user[5] == "trial"
    assert user[6] == 5
    assert user[7] == 30


def test_get_expiring_users_returns_users_with_three_days_left(tmp_path, monkeypatch):
    """
    Проверяем, что пользователь попадает в список истекающих подписок.
    """
    repository, _ = make_repository(tmp_path, monkeypatch)

    now = 1_700_000_000
    twenty_seven_days_ago = now - 27 * 86400

    monkeypatch.setattr(bot_repository_module.time, "time", lambda: now)

    save_test_user(
        repository=repository,
        telegram_id=1003,
        username="almost_expired",
        first_name="Almost",
        vpn_email="tg_1003",
        created_at=twenty_seven_days_ago,
    )

    users = repository.get_expiring_users(days_before_expire=3)

    assert len(users) == 1
    assert users[0][0] == 1003
    assert users[0][5] == 3
    assert users[0][6] == 30


def test_get_expiring_users_ignores_users_with_many_days_left(tmp_path, monkeypatch):
    """
    Проверяем, что пользователь с большим запасом дней не попадает в список.
    """
    repository, _ = make_repository(tmp_path, monkeypatch)

    now = 1_700_000_000
    ten_days_ago = now - 10 * 86400

    monkeypatch.setattr(bot_repository_module.time, "time", lambda: now)

    save_test_user(
        repository=repository,
        telegram_id=1004,
        username="active_user",
        first_name="Active",
        vpn_email="tg_1004",
        created_at=ten_days_ago,
    )

    users = repository.get_expiring_users(days_before_expire=3)

    assert users == []


def test_get_expired_users_returns_users_with_negative_days_left(tmp_path, monkeypatch):
    """
    Проверяем, что просроченный пользователь попадает в список expired-кандидатов.
    """
    repository, _ = make_repository(tmp_path, monkeypatch)

    now = 1_700_000_000
    thirty_one_days_ago = now - 31 * 86400

    monkeypatch.setattr(bot_repository_module.time, "time", lambda: now)

    save_test_user(
        repository=repository,
        telegram_id=1005,
        username="expired_user",
        first_name="Expired",
        vpn_email="tg_1005",
        created_at=thirty_one_days_ago,
    )

    users = repository.get_expired_users()

    assert len(users) == 1
    assert users[0][0] == 1005
    assert users[0][5] == -1
    assert users[0][6] == 30


def test_get_expired_users_ignores_already_expired_status(tmp_path, monkeypatch):
    """
    Проверяем, что пользователь со статусом expired не выбирается повторно.
    """
    repository, test_db = make_repository(tmp_path, monkeypatch)

    now = 1_700_000_000
    thirty_one_days_ago = now - 31 * 86400

    monkeypatch.setattr(bot_repository_module.time, "time", lambda: now)

    save_test_user(
        repository=repository,
        telegram_id=1006,
        username="already_expired",
        first_name="Already",
        vpn_email="tg_1006",
        created_at=thirty_one_days_ago,
    )

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            UPDATE users
            SET subscription_status = 'expired'
            WHERE telegram_id = ?
            """,
            (1006,),
        )
        conn.commit()

    users = repository.get_expired_users()

    assert users == []


def test_mark_users_as_expired_updates_statuses(tmp_path, monkeypatch):
    """
    Проверяем, что метод переводит пользователей в статус expired.
    """
    repository, test_db = make_repository(tmp_path, monkeypatch)

    save_test_user(
        repository=repository,
        telegram_id=1007,
        username="user_one",
        first_name="One",
        vpn_email="tg_1007",
        created_at=1_700_000_000,
    )
    save_test_user(
        repository=repository,
        telegram_id=1008,
        username="user_two",
        first_name="Two",
        vpn_email="tg_1008",
        created_at=1_700_000_000,
    )

    changed_count = repository.mark_users_as_expired([1007, 1008])

    with sqlite3.connect(test_db) as conn:
        statuses = conn.execute(
            """
            SELECT subscription_status
            FROM users
            WHERE telegram_id IN (?, ?)
            ORDER BY telegram_id ASC
            """,
            (1007, 1008),
        ).fetchall()

    assert changed_count == 2
    assert statuses == [("expired",), ("expired",)]


def test_mark_users_as_expired_returns_zero_for_empty_list(tmp_path, monkeypatch):
    """
    Проверяем, что пустой список не вызывает ошибку и возвращает 0.
    """
    repository, _ = make_repository(tmp_path, monkeypatch)

    changed_count = repository.mark_users_as_expired([])

    assert changed_count == 0

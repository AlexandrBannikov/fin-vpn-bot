import sqlite3

import app.repositories.bot_repository as bot_repository_module
from app.repositories.bot_repository import BotRepository


def test_new_user_gets_default_user_role(tmp_path, monkeypatch):
    """
    Проверяем бизнес-правило:
    новый пользователь получает роль user по умолчанию.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    repository.save_user(
        telegram_id=3001,
        username="new_user",
        first_name="New",
        vpn_email="tg_3001",
        referrer_id=None,
        created_at=1_700_000_000,
    )

    with sqlite3.connect(test_db) as conn:
        role = conn.execute(
            """
            SELECT role
            FROM users
            WHERE telegram_id = ?
            """,
            (3001,),
        ).fetchone()[0]

    assert role == "user"


def test_get_user_role_returns_saved_role(tmp_path, monkeypatch):
    """
    Проверяем, что роль пользователя читается из базы.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    repository.save_user(
        telegram_id=3002,
        username="admin_user",
        first_name="Admin",
        vpn_email="tg_3002",
        referrer_id=None,
        created_at=1_700_000_000,
    )

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            UPDATE users
            SET role = 'admin'
            WHERE telegram_id = ?
            """,
            (3002,),
        )
        conn.commit()

    assert repository.get_user_role(3002) == "admin"


def test_get_user_role_returns_user_for_unknown_user(tmp_path, monkeypatch):
    """
    Проверяем безопасное поведение:
    если пользователь не найден, считаем его обычным user.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    assert repository.get_user_role(9999) == "user"


def test_get_user_role_returns_user_for_empty_role(tmp_path, monkeypatch):
    """
    Проверяем безопасное поведение:
    если роль пустая, считаем пользователя обычным user.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    repository = BotRepository()
    repository.init_db()

    repository.save_user(
        telegram_id=3003,
        username="empty_role_user",
        first_name="Empty",
        vpn_email="tg_3003",
        referrer_id=None,
        created_at=1_700_000_000,
    )

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            UPDATE users
            SET role = NULL
            WHERE telegram_id = ?
            """,
            (3003,),
        )
        conn.commit()

    assert repository.get_user_role(3003) == "user"


def test_init_db_adds_role_column_to_existing_users_table(tmp_path, monkeypatch):
    """
    Проверяем миграцию:
    если таблица users уже существовала без role,
    init_db должен добавить колонку role.
    """
    test_db = tmp_path / "bot.db"
    monkeypatch.setattr(bot_repository_module, "BOT_DB_PATH", test_db)

    with sqlite3.connect(test_db) as conn:
        conn.execute("""
            CREATE TABLE users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                vpn_email TEXT,
                referrer_id INTEGER,
                created_at INTEGER,
                subscription_started_at INTEGER,
                subscription_days INTEGER DEFAULT 30,
                subscription_status TEXT DEFAULT 'trial',
                last_warning_at INTEGER
            )
        """)
        conn.commit()

    repository = BotRepository()
    repository.init_db()

    with sqlite3.connect(test_db) as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }

    assert "role" in columns


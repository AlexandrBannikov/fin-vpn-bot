import sqlite3

import app.repositories.bot_repository as bot_repository_module
import app.repositories.invite_repository as invite_repository_module
from app.repositories.bot_repository import BotRepository
from app.repositories.invite_repository import InviteRepository


def create_invite_links_table(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE invite_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_tg_id INTEGER NOT NULL,
                vpn_email TEXT NOT NULL,
                sub_id TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                token TEXT,
                used_at INTEGER
            )
        """)
        conn.commit()


def test_bot_repository_init_db_creates_invite_links_table(tmp_path, monkeypatch):
    test_db = tmp_path / "test_bot.db"

    monkeypatch.setattr(
        bot_repository_module,
        "BOT_DB_PATH",
        str(test_db),
    )
    monkeypatch.setattr(
        invite_repository_module,
        "BOT_DB_PATH",
        str(test_db),
    )

    bot_repository = BotRepository()
    bot_repository.init_db()

    repository = InviteRepository()
    repository.save_invite_link(123, "invite_1", "sub-1", "token-1", 111)

    invite = repository.get_by_token("token-1")

    assert invite is not None
    assert invite["owner_tg_id"] == 123


def test_save_and_get_invite_by_token(tmp_path, monkeypatch):
    test_db = tmp_path / "test_bot.db"
    create_invite_links_table(test_db)

    monkeypatch.setattr(
        invite_repository_module,
        "BOT_DB_PATH",
        str(test_db),
    )

    repository = InviteRepository()

    repository.save_invite_link(
        owner_tg_id=123,
        vpn_email="invite_123_test",
        sub_id="sub-test",
        token="token-test",
        created_at=111,
    )

    invite = repository.get_by_token("token-test")

    assert invite is not None
    assert invite["owner_tg_id"] == 123
    assert invite["vpn_email"] == "invite_123_test"
    assert invite["sub_id"] == "sub-test"
    assert invite["token"] == "token-test"
    assert invite["created_at"] == 111
    assert invite["used_at"] is None


def test_mark_invite_as_used(tmp_path, monkeypatch):
    test_db = tmp_path / "test_bot.db"
    create_invite_links_table(test_db)

    monkeypatch.setattr(
        invite_repository_module,
        "BOT_DB_PATH",
        str(test_db),
    )

    repository = InviteRepository()

    repository.save_invite_link(
        owner_tg_id=123,
        vpn_email="invite_123_test",
        sub_id="sub-test",
        token="token-test",
        created_at=111,
    )

    repository.mark_as_used(
        token="token-test",
        used_at=222,
    )

    invite = repository.get_by_token("token-test")

    assert invite["used_at"] == 222


def test_count_invite_links(tmp_path, monkeypatch):
    test_db = tmp_path / "test_bot.db"
    create_invite_links_table(test_db)

    monkeypatch.setattr(
        invite_repository_module,
        "BOT_DB_PATH",
        str(test_db),
    )

    repository = InviteRepository()

    repository.save_invite_link(123, "invite_1", "sub-1", "token-1", 111)
    repository.save_invite_link(123, "invite_2", "sub-2", "token-2", 112)
    repository.save_invite_link(456, "invite_3", "sub-3", "token-3", 113)

    assert repository.count_invite_links(123) == 2
    assert repository.count_invite_links(456) == 1


def test_count_all_invite_links(tmp_path, monkeypatch):
    test_db = tmp_path / "test_bot.db"
    create_invite_links_table(test_db)

    monkeypatch.setattr(
        invite_repository_module,
        "BOT_DB_PATH",
        str(test_db),
    )

    repository = InviteRepository()

    repository.save_invite_link(123, "invite_1", "sub-1", "token-1", 111)
    repository.save_invite_link(123, "invite_2", "sub-2", "token-2", 112)
    repository.save_invite_link(456, "invite_3", "sub-3", "token-3", 113)

    assert repository.count_all_invite_links() == 3


def test_count_used_and_unused_invite_links(tmp_path, monkeypatch):
    test_db = tmp_path / "test_bot.db"
    create_invite_links_table(test_db)

    monkeypatch.setattr(
        invite_repository_module,
        "BOT_DB_PATH",
        str(test_db),
    )

    repository = InviteRepository()

    repository.save_invite_link(123, "invite_1", "sub-1", "token-1", 111)
    repository.save_invite_link(123, "invite_2", "sub-2", "token-2", 112)
    repository.save_invite_link(456, "invite_3", "sub-3", "token-3", 113)

    repository.mark_as_used("token-1", 222)

    assert repository.count_used_invite_links() == 1
    assert repository.count_unused_invite_links() == 2

def test_delete_used_invite_links(tmp_path, monkeypatch):
    test_db = tmp_path / "test_bot.db"
    create_invite_links_table(test_db)

    monkeypatch.setattr(
        invite_repository_module,
        "BOT_DB_PATH",
        str(test_db),
    )

    repository = InviteRepository()

    repository.save_invite_link(123, "invite_1", "sub-1", "token-1", 111)
    repository.save_invite_link(123, "invite_2", "sub-2", "token-2", 112)
    repository.save_invite_link(456, "invite_3", "sub-3", "token-3", 113)

    repository.mark_as_used("token-1", 222)
    repository.mark_as_used("token-2", 333)

    deleted_count = repository.delete_used_invite_links()

    assert deleted_count == 2
    assert repository.count_all_invite_links() == 1
    assert repository.count_used_invite_links() == 0
    assert repository.count_unused_invite_links() == 1

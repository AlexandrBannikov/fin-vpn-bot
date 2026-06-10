import app.handlers.admin_health_handler as health_module
from app.handlers.admin_health_handler import (
    build_admin_health_text,
    build_status_icon,
)


class FakeBotRepository:
    def count_users(self):
        return 8


class FakeXuiRepository:
    def __init__(self, inbound=True):
        self.inbound = inbound

    def get_inbound_by_id(self, inbound_id: int):
        return {"id": inbound_id} if self.inbound else None

    def count_clients(self):
        return 18


def test_build_status_icon_returns_green_for_ok():
    assert build_status_icon(True) == "🟢"


def test_build_status_icon_returns_red_for_error():
    assert build_status_icon(False) == "🔴"


def test_build_admin_health_text_returns_ok_status(monkeypatch):
    monkeypatch.setattr(health_module, "can_open_sqlite_database", lambda path: True)

    text = build_admin_health_text(
        bot_repository=FakeBotRepository(),
        xui_repository=FakeXuiRepository(inbound=True),
    )

    assert "bot.db доступна" in text
    assert "x-ui.db доступна" in text
    assert "inbound #1 найден" in text
    assert "Пользователей в боте: 8" in text
    assert "VPN-клиентов в 3X-UI: 18" in text
    assert "система исправна" in text


def test_build_admin_health_text_returns_problem_when_inbound_missing(monkeypatch):
    monkeypatch.setattr(health_module, "can_open_sqlite_database", lambda path: True)

    text = build_admin_health_text(
        bot_repository=FakeBotRepository(),
        xui_repository=FakeXuiRepository(inbound=False),
    )

    assert "🔴 inbound #1 найден" in text
    assert "есть проблема" in text

import sqlite3

from app.handlers.admin_health_handler import (
    can_open_sqlite_database,
    register_admin_health_handlers,
)


def test_can_open_sqlite_database_returns_true_for_valid_db(tmp_path):
    db_path = tmp_path / "test.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()

    assert can_open_sqlite_database(str(db_path)) is True


def test_can_open_sqlite_database_returns_false_for_invalid_path():
    assert can_open_sqlite_database("/no/such/folder/test.db") is False


def test_register_admin_health_handlers_returns_router():
    router = register_admin_health_handlers(
        bot_repository=FakeBotRepository(),
        xui_repository=FakeXuiRepository(),
    )

    assert router is not None


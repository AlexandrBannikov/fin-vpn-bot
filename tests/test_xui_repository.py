import json
import sqlite3

import app.repositories.xui_repository as xui_repository_module
from app.repositories.xui_repository import XuiRepository


def create_xui_test_schema(test_db):
    """
    Создаёт минимальную структуру базы 3X-UI для тестов.
    """
    with sqlite3.connect(test_db) as conn:
        conn.execute("""
            CREATE TABLE clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                sub_id TEXT,
                uuid TEXT,
                password TEXT,
                auth TEXT,
                flow TEXT,
                security TEXT,
                reverse TEXT,
                limit_ip INTEGER,
                total_gb INTEGER,
                expiry_time INTEGER,
                enable INTEGER,
                tg_id INTEGER,
                group_name TEXT,
                comment TEXT,
                reset INTEGER,
                created_at INTEGER,
                updated_at INTEGER
            )
        """)

        conn.execute("""
            CREATE TABLE client_inbounds (
                client_id INTEGER,
                inbound_id INTEGER,
                flow_override TEXT,
                created_at INTEGER,
                UNIQUE(client_id, inbound_id)
            )
        """)

        conn.execute("""
            CREATE TABLE client_traffics (
                inbound_id INTEGER,
                enable INTEGER,
                email TEXT UNIQUE,
                up INTEGER,
                down INTEGER,
                expiry_time INTEGER,
                total INTEGER,
                reset INTEGER,
                last_online INTEGER
            )
        """)

        conn.execute("""
            CREATE TABLE inbounds (
                id INTEGER PRIMARY KEY,
                settings TEXT
            )
        """)

        conn.commit()


def test_create_and_get_client_by_email(tmp_path, monkeypatch):
    """
    Проверяем создание VPN-клиента и поиск по email.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)

    create_xui_test_schema(test_db)

    repository = XuiRepository()

    client_id = repository.create_client(
        email="tg_1001",
        sub_id="sub-1001",
        client_uuid="uuid-1001",
        password="password-1001",
        auth="auth-1001",
        telegram_id=1001,
        created_at=1_700_000_000,
    )

    client = repository.get_client_by_email("tg_1001")

    assert client_id == 1
    assert client["email"] == "tg_1001"
    assert client["sub_id"] == "sub-1001"
    assert client["uuid"] == "uuid-1001"
    assert client["tg_id"] == 1001
    assert client["enable"] == 1


def test_get_client_by_id_returns_client(tmp_path, monkeypatch):
    """
    Проверяем поиск клиента по id.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)

    create_xui_test_schema(test_db)

    repository = XuiRepository()

    client_id = repository.create_client(
        email="tg_1002",
        sub_id="sub-1002",
        client_uuid="uuid-1002",
        password="password-1002",
        auth="auth-1002",
        telegram_id=1002,
        created_at=1_700_000_000,
    )

    client = repository.get_client_by_id(client_id)

    assert client["id"] == client_id
    assert client["email"] == "tg_1002"


def test_bind_client_to_inbound_creates_relation(tmp_path, monkeypatch):
    """
    Проверяем привязку клиента к inbound.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)
    monkeypatch.setattr(xui_repository_module, "INBOUND_ID", 1)
    monkeypatch.setattr(xui_repository_module, "FLOW", "xtls-rprx-vision")

    create_xui_test_schema(test_db)

    repository = XuiRepository()
    repository.bind_client_to_inbound(client_id=10, created_at=1_700_000_000)

    with sqlite3.connect(test_db) as conn:
        row = conn.execute(
            """
            SELECT client_id, inbound_id, flow_override, created_at
            FROM client_inbounds
            WHERE client_id = ?
            """,
            (10,),
        ).fetchone()

    assert row == (10, 1, "xtls-rprx-vision", 1_700_000_000)


def test_create_client_traffic_creates_traffic_row(tmp_path, monkeypatch):
    """
    Проверяем создание строки трафика клиента.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)
    monkeypatch.setattr(xui_repository_module, "INBOUND_ID", 1)

    create_xui_test_schema(test_db)

    repository = XuiRepository()
    repository.create_client_traffic("tg_1003")

    with sqlite3.connect(test_db) as conn:
        row = conn.execute(
            """
            SELECT inbound_id, enable, email, up, down, expiry_time, total, reset, last_online
            FROM client_traffics
            WHERE email = ?
            """,
            ("tg_1003",),
        ).fetchone()

    assert row == (1, 1, "tg_1003", 0, 0, 0, 0, 0, 0)


def test_count_clients_by_categories(tmp_path, monkeypatch):
    """
    Проверяем подсчёт клиентов по категориям:
    - tg_ — пользователи бота;
    - invite_ — invite-клиенты;
    - остальные — ручные/старые клиенты.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)

    create_xui_test_schema(test_db)

    with sqlite3.connect(test_db) as conn:
        conn.executemany(
            """
            INSERT INTO clients
            (email, sub_id, uuid, password, auth, flow, security, reverse,
             limit_ip, total_gb, expiry_time, enable, tg_id, group_name,
             comment, reset, created_at, updated_at)
            VALUES (?, '', '', '', '', '', 'auto', '', 0, 0, 0, 1, 0, '', '', 0, 0, 0)
            """,
            [
                ("tg_1001",),
                ("tg_1002",),
                ("invite_abc",),
                ("manual_user",),
            ],
        )
        conn.commit()

    repository = XuiRepository()

    assert repository.count_clients() == 4
    assert repository.count_bot_clients() == 2
    assert repository.count_invite_clients() == 1
    assert repository.count_other_clients() == 1


def test_get_inbound_by_id_returns_inbound(tmp_path, monkeypatch):
    """
    Проверяем поиск inbound по id.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)

    create_xui_test_schema(test_db)

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            INSERT INTO inbounds (id, settings)
            VALUES (?, ?)
            """,
            (1, json.dumps({"clients": []})),
        )
        conn.commit()

    repository = XuiRepository()
    inbound = repository.get_inbound_by_id(1)

    assert inbound["id"] == 1
    assert json.loads(inbound["settings"]) == {"clients": []}


def test_add_client_to_inbound_settings_adds_client(tmp_path, monkeypatch):
    """
    Проверяем добавление клиента в JSON settings inbound.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)
    monkeypatch.setattr(xui_repository_module, "INBOUND_ID", 1)
    monkeypatch.setattr(xui_repository_module, "FLOW", "xtls-rprx-vision")

    create_xui_test_schema(test_db)

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            INSERT INTO inbounds (id, settings)
            VALUES (?, ?)
            """,
            (1, json.dumps({"clients": []})),
        )
        conn.commit()

    repository = XuiRepository()

    client_id = repository.create_client(
        email="tg_1004",
        sub_id="sub-1004",
        client_uuid="uuid-1004",
        password="password-1004",
        auth="auth-1004",
        telegram_id=1004,
        created_at=1_700_000_000,
    )

    client = repository.get_client_by_id(client_id)
    repository.add_client_to_inbound_settings(client)

    with sqlite3.connect(test_db) as conn:
        settings_text = conn.execute(
            "SELECT settings FROM inbounds WHERE id = ?",
            (1,),
        ).fetchone()[0]

    settings = json.loads(settings_text)

    assert len(settings["clients"]) == 1
    assert settings["clients"][0]["email"] == "tg_1004"
    assert settings["clients"][0]["id"] == "uuid-1004"
    assert settings["clients"][0]["subId"] == "sub-1004"
    assert settings["clients"][0]["flow"] == "xtls-rprx-vision"

def test_get_client_by_telegram_id_returns_client(tmp_path, monkeypatch):
    """
    Проверяем поиск клиента по Telegram ID.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)

    create_xui_test_schema(test_db)

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            INSERT INTO clients
            (email, sub_id, uuid, password, auth, flow, security, reverse,
             limit_ip, total_gb, expiry_time, enable, tg_id, group_name,
             comment, reset, created_at, updated_at)
            VALUES (?, '', '', '', '', '', 'auto', '', 0, 0, 0, 1, ?, '', '', 0, 0, 0)
            """,
            ("tg_228333796", 228333796),
        )
        conn.commit()

    repository = XuiRepository()
    client = repository.get_client_by_telegram_id(228333796)

    assert client["email"] == "tg_228333796"
    assert client["tg_id"] == 228333796


def test_set_client_enabled_disables_client(tmp_path, monkeypatch):
    """
    Проверяем отключение VPN-клиента:
    - clients.enable становится 0;
    - client_traffics.enable становится 0;
    - в JSON settings inbound клиент тоже становится disabled.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)
    monkeypatch.setattr(xui_repository_module, "INBOUND_ID", 1)

    create_xui_test_schema(test_db)

    settings = {
        "clients": [
            {
                "email": "tg_228333796",
                "id": "uuid-228333796",
                "enable": True,
            }
        ]
    }

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            INSERT INTO clients
            (id, email, sub_id, uuid, password, auth, flow, security, reverse,
             limit_ip, total_gb, expiry_time, enable, tg_id, group_name,
             comment, reset, created_at, updated_at)
            VALUES (?, ?, '', ?, '', '', '', 'auto', '', 0, 0, 0, 1, ?, '', '', 0, 0, 0)
            """,
            (1, "tg_228333796", "uuid-228333796", 228333796),
        )

        conn.execute(
            """
            INSERT INTO client_traffics
            (inbound_id, enable, email, up, down, expiry_time, total, reset, last_online)
            VALUES (?, 1, ?, 0, 0, 0, 0, 0, 0)
            """,
            (1, "tg_228333796"),
        )

        conn.execute(
            """
            INSERT INTO inbounds (id, settings)
            VALUES (?, ?)
            """,
            (1, json.dumps(settings)),
        )

        conn.commit()

    repository = XuiRepository()
    result = repository.set_client_enabled(
        telegram_id=228333796,
        is_enabled=False,
    )

    assert result is True

    with sqlite3.connect(test_db) as conn:
        client_enable = conn.execute(
            "SELECT enable FROM clients WHERE tg_id = ?",
            (228333796,),
        ).fetchone()[0]

        traffic_enable = conn.execute(
            "SELECT enable FROM client_traffics WHERE email = ?",
            ("tg_228333796",),
        ).fetchone()[0]

        inbound_settings_text = conn.execute(
            "SELECT settings FROM inbounds WHERE id = ?",
            (1,),
        ).fetchone()[0]

    inbound_settings = json.loads(inbound_settings_text)

    assert client_enable == 0
    assert traffic_enable == 0
    assert inbound_settings["clients"][0]["enable"] is False


def test_set_client_enabled_enables_client(tmp_path, monkeypatch):
    """
    Проверяем включение VPN-клиента:
    - clients.enable становится 1;
    - client_traffics.enable становится 1;
    - в JSON settings inbound клиент тоже становится enabled.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)
    monkeypatch.setattr(xui_repository_module, "INBOUND_ID", 1)

    create_xui_test_schema(test_db)

    settings = {
        "clients": [
            {
                "email": "tg_228333796",
                "id": "uuid-228333796",
                "enable": False,
            }
        ]
    }

    with sqlite3.connect(test_db) as conn:
        conn.execute(
            """
            INSERT INTO clients
            (id, email, sub_id, uuid, password, auth, flow, security, reverse,
             limit_ip, total_gb, expiry_time, enable, tg_id, group_name,
             comment, reset, created_at, updated_at)
            VALUES (?, ?, '', ?, '', '', '', 'auto', '', 0, 0, 0, 0, ?, '', '', 0, 0, 0)
            """,
            (1, "tg_228333796", "uuid-228333796", 228333796),
        )

        conn.execute(
            """
            INSERT INTO client_traffics
            (inbound_id, enable, email, up, down, expiry_time, total, reset, last_online)
            VALUES (?, 0, ?, 0, 0, 0, 0, 0, 0)
            """,
            (1, "tg_228333796"),
        )

        conn.execute(
            """
            INSERT INTO inbounds (id, settings)
            VALUES (?, ?)
            """,
            (1, json.dumps(settings)),
        )

        conn.commit()

    repository = XuiRepository()
    result = repository.set_client_enabled(
        telegram_id=228333796,
        is_enabled=True,
    )

    assert result is True

    with sqlite3.connect(test_db) as conn:
        client_enable = conn.execute(
            "SELECT enable FROM clients WHERE tg_id = ?",
            (228333796,),
        ).fetchone()[0]

        traffic_enable = conn.execute(
            "SELECT enable FROM client_traffics WHERE email = ?",
            ("tg_228333796",),
        ).fetchone()[0]

        inbound_settings_text = conn.execute(
            "SELECT settings FROM inbounds WHERE id = ?",
            (1,),
        ).fetchone()[0]

    inbound_settings = json.loads(inbound_settings_text)

    assert client_enable == 1
    assert traffic_enable == 1
    assert inbound_settings["clients"][0]["enable"] is True


def test_set_client_enabled_returns_false_for_missing_client(tmp_path, monkeypatch):
    """
    Проверяем, что метод возвращает False,
    если клиента с таким Telegram ID нет.
    """
    test_db = tmp_path / "xui.db"
    monkeypatch.setattr(xui_repository_module, "XUI_DB_PATH", test_db)
    monkeypatch.setattr(xui_repository_module, "INBOUND_ID", 1)

    create_xui_test_schema(test_db)

    repository = XuiRepository()
    result = repository.set_client_enabled(
        telegram_id=999999999,
        is_enabled=False,
    )

    assert result is False


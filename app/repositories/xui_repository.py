import json
import sqlite3

from app.config import FLOW, INBOUND_ID, XUI_DB_PATH
from app.db import connect_sqlite


class XuiRepository:
    def get_client_by_email(self, email: str):
        with connect_sqlite(XUI_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM clients WHERE email = ?",
                (email,),
            ).fetchone()

    def create_client(
        self,
        email: str,
        sub_id: str,
        client_uuid: str,
        password: str,
        auth: str,
        telegram_id: int,
        created_at: int,
    ) -> int:
        with connect_sqlite(XUI_DB_PATH) as conn:
            cursor = conn.execute(
                """
                INSERT INTO clients
                (email, sub_id, uuid, password, auth, flow, security, reverse,
                 limit_ip, total_gb, expiry_time, enable, tg_id, group_name,
                 comment, reset, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'auto', '', 0, 0, 0, 1, ?, '', '', 0, ?, ?)
                """,
                (email, sub_id, client_uuid, password, auth, FLOW, telegram_id, created_at, created_at),
            )

            conn.commit()
            return cursor.lastrowid

    def bind_client_to_inbound(self, client_id: int, created_at: int) -> None:
        with connect_sqlite(XUI_DB_PATH) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO client_inbounds
                (client_id, inbound_id, flow_override, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (client_id, INBOUND_ID, FLOW, created_at),
            )

            conn.commit()

    def create_client_traffic(self, email: str) -> None:
        with connect_sqlite(XUI_DB_PATH) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO client_traffics
                (inbound_id, enable, email, up, down, expiry_time, total, reset, last_online)
                VALUES (?, 1, ?, 0, 0, 0, 0, 0, 0)
                """,
                (INBOUND_ID, email),
            )

            conn.commit()

    def get_client_by_id(self, client_id: int):
        with connect_sqlite(XUI_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM clients WHERE id = ?",
                (client_id,),
            ).fetchone()

    def add_client_to_inbound_settings(self, client_row) -> None:
        with connect_sqlite(XUI_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            inbound = cur.execute(
                "SELECT settings FROM inbounds WHERE id = ?",
                (INBOUND_ID,),
            ).fetchone()

            settings = json.loads(inbound["settings"])
            clients = settings.setdefault("clients", [])

            clients = [
                client for client in clients
                if client.get("email") != client_row["email"]
            ]

            clients.append({
                "auth": client_row["auth"] or "",
                "comment": client_row["comment"] or "",
                "created_at": client_row["created_at"] or 0,
                "email": client_row["email"],
                "enable": bool(client_row["enable"]),
                "expiryTime": client_row["expiry_time"] or 0,
                "flow": client_row["flow"] or FLOW,
                "id": client_row["uuid"],
                "limitIp": 0,
                "password": client_row["password"] or "",
                "reset": client_row["reset"] or 0,
                "security": client_row["security"] or "auto",
                "subId": client_row["sub_id"] or "",
                "tgId": client_row["tg_id"] or 0,
                "totalGB": client_row["total_gb"] or 0,
                "updated_at": client_row["updated_at"] or 0,
            })

            settings["clients"] = clients

            cur.execute(
                "UPDATE inbounds SET settings = ? WHERE id = ?",
                (json.dumps(settings, ensure_ascii=False, indent=2), INBOUND_ID),
            )

            conn.commit()

    def count_clients(self) -> int:
        with connect_sqlite(XUI_DB_PATH) as conn:
            return conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]

    def count_bot_clients(self) -> int:
        """
        Считает клиентов, созданных для пользователей Telegram-бота.

        Это клиенты с email вида tg_123456.
        """
        with connect_sqlite(XUI_DB_PATH) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM clients WHERE email LIKE 'tg_%'"
            ).fetchone()[0]

    def count_invite_clients(self) -> int:
        """
        Считает клиентов, созданных под одноразовые invite-ссылки.

        Это клиенты с email вида invite_...
        """
        with connect_sqlite(XUI_DB_PATH) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM clients WHERE email LIKE 'invite_%'"
            ).fetchone()[0]

    def count_other_clients(self) -> int:
        """
        Считает прочих клиентов 3X-UI.

        Это старые, ручные или тестовые клиенты,
        которые не были созданы ботом как tg_ или invite_.
        """
        with connect_sqlite(XUI_DB_PATH) as conn:
            return conn.execute(
                """
                SELECT COUNT(*)
                FROM clients
                WHERE email NOT LIKE 'tg_%'
                  AND email NOT LIKE 'invite_%'
                """
            ).fetchone()[0]
    def get_inbound_by_id(self, inbound_id: int):
        """
        Проверяет, существует ли inbound в базе 3X-UI.

        Нужен для health-check, чтобы понимать:
        база 3X-UI доступна или нет.
        """
        with connect_sqlite(XUI_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM inbounds WHERE id = ?",
                (inbound_id,),
            ).fetchone()

    def get_client_by_telegram_id(self, telegram_id: int):
        """
        Находит клиента 3X-UI по Telegram ID.

        В таблице clients Telegram ID хранится в поле tg_id.
        """
        with connect_sqlite(XUI_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM clients WHERE tg_id = ?",
                (telegram_id,),
            ).fetchone()

    def set_client_enabled(self, telegram_id: int, is_enabled: bool) -> bool:
        """
        Включает или отключает VPN-клиента по Telegram ID.

        Меняет состояние сразу в двух местах:
        - clients.enable
        - client_traffics.enable

        После этого обновляет JSON settings внутри inbound,
        чтобы 3X-UI/Xray увидели новое состояние клиента.
        """
        enabled_value = 1 if is_enabled else 0

        with connect_sqlite(XUI_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            client = cur.execute(
                "SELECT * FROM clients WHERE tg_id = ?",
                (telegram_id,),
            ).fetchone()

            if client is None:
                return False

            cur.execute(
                """
                UPDATE clients
                SET enable = ?
                WHERE id = ?
                """,
                (enabled_value, client["id"]),
            )

            cur.execute(
                """
                UPDATE client_traffics
                SET enable = ?
                WHERE email = ?
                """,
                (enabled_value, client["email"]),
            )

            updated_client = cur.execute(
                "SELECT * FROM clients WHERE id = ?",
                (client["id"],),
            ).fetchone()

            inbound = cur.execute(
                "SELECT settings FROM inbounds WHERE id = ?",
                (INBOUND_ID,),
            ).fetchone()

            settings = json.loads(inbound["settings"])
            clients = settings.setdefault("clients", [])

            updated_clients = []

            for inbound_client in clients:
                if inbound_client.get("email") == updated_client["email"]:
                    inbound_client["enable"] = bool(updated_client["enable"])

                updated_clients.append(inbound_client)

            settings["clients"] = updated_clients

            cur.execute(
                "UPDATE inbounds SET settings = ? WHERE id = ?",
                (json.dumps(settings, ensure_ascii=False, indent=2), INBOUND_ID),
            )

            conn.commit()

        return True

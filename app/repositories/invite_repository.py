import sqlite3

from app.config import BOT_DB_PATH


class InviteRepository:
    def save_invite_link(
        self,
        owner_tg_id: int,
        vpn_email: str,
        sub_id: str,
        token: str,
        created_at: int,
    ) -> None:
        with sqlite3.connect(BOT_DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO invite_links
                (owner_tg_id, vpn_email, sub_id, token, created_at, used_at)
                VALUES (?, ?, ?, ?, ?, NULL)
                """,
                (owner_tg_id, vpn_email, sub_id, token, created_at),
            )

            conn.commit()

    def get_by_token(self, token: str):
        with sqlite3.connect(BOT_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                """
                SELECT *
                FROM invite_links
                WHERE token = ?
                """,
                (token,),
            ).fetchone()

    def mark_as_used(self, token: str, used_at: int) -> None:
        with sqlite3.connect(BOT_DB_PATH) as conn:
            conn.execute(
                """
                UPDATE invite_links
                SET used_at = ?
                WHERE token = ?
                """,
                (used_at, token),
            )

            conn.commit()

    def count_invite_links(self, owner_tg_id: int) -> int:
        with sqlite3.connect(BOT_DB_PATH) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM invite_links WHERE owner_tg_id = ?",
                (owner_tg_id,),
            ).fetchone()[0]

    def count_all_invite_links(self) -> int:
        with sqlite3.connect(BOT_DB_PATH) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM invite_links"
            ).fetchone()[0]

    def count_used_invite_links(self) -> int:
        with sqlite3.connect(BOT_DB_PATH) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM invite_links WHERE used_at IS NOT NULL"
            ).fetchone()[0]

    def count_unused_invite_links(self) -> int:
        with sqlite3.connect(BOT_DB_PATH) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM invite_links WHERE used_at IS NULL"
            ).fetchone()[0]

    def delete_used_invite_links(self) -> int:
        """
        Удаляет использованные одноразовые инвайты.

        Возвращает количество удалённых записей.
        """
        with sqlite3.connect(BOT_DB_PATH) as conn:
            cursor = conn.execute(
                "DELETE FROM invite_links WHERE used_at IS NOT NULL"
            )
            conn.commit()
            return cursor.rowcount


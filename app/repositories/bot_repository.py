import time

from app.config import BOT_DB_PATH
from app.db import connect_sqlite
from app.migrations import apply_bot_migrations


class BotRepository:
    def init_db(self) -> None:
        """
        Создаёт таблицы проекта и добавляет недостающие колонки.

        Важно:
        - created_at и subscription_started_at храним в Unix seconds;
        - роли пользователей храним в users.role.
        """
        apply_bot_migrations(BOT_DB_PATH)

    def user_exists(self, telegram_id: int) -> bool:
        """
        Проверяет, есть ли пользователь в базе.
        """
        with connect_sqlite(BOT_DB_PATH) as conn:
            row = conn.execute(
                "SELECT telegram_id FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()

        return row is not None

    def get_user_role(self, telegram_id: int) -> str:
        """
        Возвращает роль пользователя.

        Если пользователь не найден или роль пустая,
        считаем его обычным пользователем.
        """
        with connect_sqlite(BOT_DB_PATH) as conn:
            row = conn.execute(
                """
                SELECT role
                FROM users
                WHERE telegram_id = ?
                """,
                (telegram_id,),
            ).fetchone()

        if not row or not row[0]:
            return "user"

        return row[0]

    def get_all_users(self) -> list[tuple]:
        """
        Возвращает всех пользователей бота.

        Используется для служебных рассылок,
        например для принудительного обновления меню.
        """
        with connect_sqlite(BOT_DB_PATH) as conn:
            return conn.execute(
                """
                SELECT telegram_id, role
                FROM users
                ORDER BY created_at ASC
                """
            ).fetchall()

    def save_user(
        self,
        telegram_id: int,
        username: str,
        first_name: str,
        vpn_email: str,
        referrer_id: int | None,
        created_at: int,
    ) -> None:
        """
        Сохраняет нового пользователя бота.

        Вместе с пользователем сразу создаётся trial-подписка:
        - старт подписки равен created_at;
        - срок по умолчанию 30 дней;
        - статус trial;
        - роль по умолчанию user.
        """
        with connect_sqlite(BOT_DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO users
                (
                    telegram_id,
                    username,
                    first_name,
                    vpn_email,
                    referrer_id,
                    created_at,
                    subscription_started_at,
                    subscription_days,
                    subscription_status,
                    role
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 30, 'trial', 'user')
                """,
                (
                    telegram_id,
                    username,
                    first_name,
                    vpn_email,
                    referrer_id,
                    created_at,
                    created_at,
                ),
            )

            if referrer_id:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO referrals
                    (referrer_id, referred_id, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (referrer_id, telegram_id, created_at),
                )

            conn.commit()

    def count_referrals(self, telegram_id: int) -> int:
        """
        Считает количество рефералов конкретного пользователя.
        """
        with connect_sqlite(BOT_DB_PATH) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
                (telegram_id,),
            ).fetchone()[0]

    def count_users(self) -> int:
        """
        Считает всех пользователей бота.
        """
        with connect_sqlite(BOT_DB_PATH) as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def count_all_referrals(self) -> int:
        """
        Считает всех рефералов.
        """
        with connect_sqlite(BOT_DB_PATH) as conn:
            return conn.execute("SELECT COUNT(*) FROM referrals").fetchone()[0]

    def extend_subscription(self, telegram_id: int, days: int) -> bool:
        """
        Продлевает подписку пользователя на указанное количество дней.

        Возвращает:
        - True, если пользователь найден и подписка продлена;
        - False, если пользователя нет.
        """
        with connect_sqlite(BOT_DB_PATH) as conn:
            user = conn.execute(
                """
                SELECT subscription_days
                FROM users
                WHERE telegram_id = ?
                """,
                (telegram_id,),
            ).fetchone()

            if not user:
                return False

            conn.execute(
                """
                UPDATE users
                SET subscription_days = subscription_days + ?,
                    subscription_status = 'active'
                WHERE telegram_id = ?
                """,
                (days, telegram_id),
            )

            conn.commit()
            return True

    def _calculate_days_connected(self, subscription_started_at: int | None, now: int) -> int:
        """
        Безопасно считает, сколько дней прошло с начала подписки.

        Если дата отсутствует или находится в будущем,
        возвращаем 0.
        """
        if subscription_started_at is None or subscription_started_at > now:
            return 0

        return int((now - subscription_started_at) / 86400)

    def get_users_with_subscription_info(self) -> list[tuple]:
        """
        Возвращает список пользователей с расчётом дней подписки.
        """
        now = int(time.time())

        with connect_sqlite(BOT_DB_PATH) as conn:
            users = conn.execute(
                """
                SELECT
                    telegram_id,
                    username,
                    first_name,
                    vpn_email,
                    referrer_id,
                    subscription_status,
                    subscription_started_at,
                    subscription_days
                FROM users
                ORDER BY subscription_started_at ASC
                """
            ).fetchall()

        result = []

        for user in users:
            (
                telegram_id,
                username,
                first_name,
                vpn_email,
                referrer_id,
                subscription_status,
                subscription_started_at,
                subscription_days,
            ) = user

            days_connected = self._calculate_days_connected(
                subscription_started_at=subscription_started_at,
                now=now,
            )

            result.append(
                (
                    telegram_id,
                    username,
                    first_name,
                    vpn_email,
                    referrer_id,
                    subscription_status,
                    days_connected,
                    subscription_days,
                )
            )

        return result

    def get_expiring_users(self, days_before_expire: int = 3) -> list[tuple]:
        """
        Возвращает пользователей, у которых подписка заканчивается
        в ближайшие days_before_expire дней.
        """
        now = int(time.time())

        with connect_sqlite(BOT_DB_PATH) as conn:
            users = conn.execute(
                """
                SELECT
                    telegram_id,
                    username,
                    first_name,
                    vpn_email,
                    subscription_status,
                    subscription_started_at,
                    subscription_days
                FROM users
                WHERE subscription_status IN ('trial', 'active')
                ORDER BY subscription_started_at ASC
                """
            ).fetchall()

        result = []

        for user in users:
            (
                telegram_id,
                username,
                first_name,
                vpn_email,
                subscription_status,
                subscription_started_at,
                subscription_days,
            ) = user

            days_connected = self._calculate_days_connected(
                subscription_started_at=subscription_started_at,
                now=now,
            )
            days_left = subscription_days - days_connected

            if 0 <= days_left <= days_before_expire:
                result.append(
                    (
                        telegram_id,
                        username,
                        first_name,
                        vpn_email,
                        subscription_status,
                        days_left,
                        subscription_days,
                    )
                )

        return result

    def get_expired_users(self) -> list[tuple]:
        """
        Возвращает пользователей, у которых подписка уже закончилась,
        но статус ещё trial или active.

        Этот метод ничего не меняет в базе.
        """
        now = int(time.time())

        with connect_sqlite(BOT_DB_PATH) as conn:
            users = conn.execute(
                """
                SELECT
                    telegram_id,
                    username,
                    first_name,
                    vpn_email,
                    subscription_status,
                    subscription_started_at,
                    subscription_days
                FROM users
                WHERE subscription_status IN ('trial', 'active')
                ORDER BY subscription_started_at ASC
                """
            ).fetchall()

        result = []

        for user in users:
            (
                telegram_id,
                username,
                first_name,
                vpn_email,
                subscription_status,
                subscription_started_at,
                subscription_days,
            ) = user

            days_connected = self._calculate_days_connected(
                subscription_started_at=subscription_started_at,
                now=now,
            )
            days_left = subscription_days - days_connected

            if days_left < 0:
                result.append(
                    (
                        telegram_id,
                        username,
                        first_name,
                        vpn_email,
                        subscription_status,
                        days_left,
                        subscription_days,
                    )
                )

        return result

    def mark_users_as_expired(self, telegram_ids: list[int]) -> int:
        """
        Переводит пользователей в статус expired.

        Возвращает количество изменённых строк.
        """
        if not telegram_ids:
            return 0

        with connect_sqlite(BOT_DB_PATH) as conn:
            cursor = conn.executemany(
                """
                UPDATE users
                SET subscription_status = 'expired'
                WHERE telegram_id = ?
                """,
                [(telegram_id,) for telegram_id in telegram_ids],
            )

            conn.commit()

        return cursor.rowcount
    def get_users_for_subscription_warning(self, days_left_target: int) -> list[tuple]:
        """
        Возвращает пользователей, которым нужно отправить предупреждение
        об окончании подписки.

        Выбираются только пользователи со статусом trial/active,
        у которых осталось ровно days_left_target дней.

        Повторная отправка в тот же день блокируется через last_warning_at.
        """
        now = int(time.time())
        today_start = now - (now % 86400)

        with connect_sqlite(BOT_DB_PATH) as conn:
            users = conn.execute(
                """
                SELECT
                    telegram_id,
                    username,
                    first_name,
                    vpn_email,
                    subscription_status,
                    subscription_started_at,
                    subscription_days,
                    last_warning_at
                FROM users
                WHERE subscription_status IN ('trial', 'active')
                ORDER BY subscription_started_at ASC
                """
            ).fetchall()

        result = []

        for user in users:
            (
                telegram_id,
                username,
                first_name,
                vpn_email,
                subscription_status,
                subscription_started_at,
                subscription_days,
                last_warning_at,
            ) = user

            days_connected = self._calculate_days_connected(
                subscription_started_at=subscription_started_at,
                now=now,
            )
            days_left = subscription_days - days_connected

            warning_was_sent_today = (
                last_warning_at is not None
                and last_warning_at >= today_start
            )

            if days_left == days_left_target and not warning_was_sent_today:
                result.append(
                    (
                        telegram_id,
                        username,
                        first_name,
                        vpn_email,
                        subscription_status,
                        days_left,
                        subscription_days,
                    )
                )

        return result

    def mark_subscription_warning_sent(self, telegram_ids: list[int]) -> int:
        """
        Отмечает, что пользователям сегодня уже отправлено предупреждение.
        """
        if not telegram_ids:
            return 0

        now = int(time.time())

        with connect_sqlite(BOT_DB_PATH) as conn:
            cursor = conn.executemany(
                """
                UPDATE users
                SET last_warning_at = ?
                WHERE telegram_id = ?
                """,
                [(now, telegram_id) for telegram_id in telegram_ids],
            )

            conn.commit()

        return cursor.rowcount

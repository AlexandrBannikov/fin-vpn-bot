class SubscriptionService:
    """
    Сервис обслуживания подписок.

    Отвечает за:
    - поиск пользователей с истёкшей подпиской;
    - отключение таких пользователей в 3X-UI;
    - перевод пользователей в статус expired.
    """

    def __init__(self, bot_repository, xui_repository):
        self.bot_repository = bot_repository
        self.xui_repository = xui_repository

    def disable_expired_users(self) -> list[int]:
        """
        Отключает пользователей, у которых закончилась подписка.

        Возвращает список Telegram ID отключённых пользователей.
        """
        expired_users = self.bot_repository.get_expired_users()

        if not expired_users:
            return []

        disabled_user_ids = []

        for user in expired_users:
            telegram_id = user[0]

            is_disabled = self.xui_repository.set_client_enabled(
                telegram_id=telegram_id,
                is_enabled=False,
            )

            if is_disabled:
                disabled_user_ids.append(telegram_id)

        if disabled_user_ids:
            self.bot_repository.mark_users_as_expired(disabled_user_ids)

        return disabled_user_ids

    def get_expiring_users_by_days(self, days_before_expire: int = 7) -> list[tuple]:
        """
        Возвращает пользователей, у которых подписка скоро закончится.
        """
        return self.bot_repository.get_expiring_users(
            days_before_expire=days_before_expire,
        )


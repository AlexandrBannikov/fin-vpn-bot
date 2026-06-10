class SubscriptionNotificationService:
    """
    Сервис уведомлений о скором окончании подписки.

    Отвечает только за:
    - поиск пользователей, которым нужно отправить предупреждение;
    - отправку Telegram-сообщений;
    - отметку, что предупреждение уже отправлено.

    Логику выборки пользователей держим в BotRepository.
    """

    WARNING_DAYS = (7, 3, 1)

    def __init__(self, bot_repository, bot):
        self.bot_repository = bot_repository
        self.bot = bot

    async def send_expiration_warnings(self) -> int:
        """
        Отправляет предупреждения за 7, 3 и 1 день до окончания подписки.

        Возвращает количество успешно отправленных уведомлений.
        """
        total_sent = 0

        for days_left in self.WARNING_DAYS:
            users = self.bot_repository.get_users_for_subscription_warning(days_left)
            sent_telegram_ids = []

            for user in users:
                telegram_id = user[0]
                first_name = user[2] or "друг"

                message = (
                    f"Привет, {first_name}!\n\n"
                    f"Твоя VPN-подписка заканчивается через {days_left} дн.\n"
                    f"Чтобы доступ не отключился, продли подписку заранее."
                )

                await self.bot.send_message(telegram_id, message)
                sent_telegram_ids.append(telegram_id)

            if sent_telegram_ids:
                self.bot_repository.mark_subscription_warning_sent(sent_telegram_ids)
                total_sent += len(sent_telegram_ids)

        return total_sent


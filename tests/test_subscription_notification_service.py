import pytest

from app.services.subscription_notification_service import SubscriptionNotificationService


class FakeBotRepository:
    """
    Фейковый репозиторий для проверки сервиса уведомлений.
    """

    def __init__(self):
        self.warning_users_by_days = {
            7: [(111, "user7", "Алексей", "vpn7", "active", 0, 30, None)],
            3: [(222, "user3", "Мария", "vpn3", "active", 0, 30, None)],
            1: [(333, "user1", None, "vpn1", "trial", 0, 30, None)],
        }
        self.requested_days = []
        self.marked_telegram_ids = []

    def get_users_for_subscription_warning(self, days_left_target: int) -> list[tuple]:
        """
        Возвращает пользователей для конкретного срока предупреждения.
        """
        self.requested_days.append(days_left_target)
        return self.warning_users_by_days.get(days_left_target, [])

    def mark_subscription_warning_sent(self, telegram_ids: list[int]) -> int:
        """
        Запоминает, кому сервис поставил отметку об отправке.
        """
        self.marked_telegram_ids.extend(telegram_ids)
        return len(telegram_ids)


class FakeBot:
    """
    Фейковый Telegram bot.
    """

    def __init__(self):
        self.sent_messages = []

    async def send_message(self, telegram_id: int, message: str) -> None:
        """
        Запоминает отправленные сообщения вместо реальной отправки в Telegram.
        """
        self.sent_messages.append((telegram_id, message))


@pytest.mark.anyio
async def test_send_expiration_warnings_sends_7_3_1_day_notifications():
    repository = FakeBotRepository()
    bot = FakeBot()
    service = SubscriptionNotificationService(repository, bot)

    sent_count = await service.send_expiration_warnings()

    assert sent_count == 3
    assert repository.requested_days == [7, 3, 1]
    assert repository.marked_telegram_ids == [111, 222, 333]

    assert bot.sent_messages[0][0] == 111
    assert "Привет, Алексей!" in bot.sent_messages[0][1]
    assert "заканчивается через 7 дн." in bot.sent_messages[0][1]

    assert bot.sent_messages[1][0] == 222
    assert "Привет, Мария!" in bot.sent_messages[1][1]
    assert "заканчивается через 3 дн." in bot.sent_messages[1][1]

    assert bot.sent_messages[2][0] == 333
    assert "Привет, друг!" in bot.sent_messages[2][1]
    assert "заканчивается через 1 дн." in bot.sent_messages[2][1]


@pytest.mark.anyio
async def test_send_expiration_warnings_does_not_mark_when_no_users():
    repository = FakeBotRepository()
    repository.warning_users_by_days = {}

    bot = FakeBot()
    service = SubscriptionNotificationService(repository, bot)

    sent_count = await service.send_expiration_warnings()

    assert sent_count == 0
    assert repository.requested_days == [7, 3, 1]
    assert repository.marked_telegram_ids == []
    assert bot.sent_messages == []


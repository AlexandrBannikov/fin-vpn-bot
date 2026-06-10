from app.services.subscription_service import SubscriptionService


class FakeBotRepository:
    def __init__(self):
        self.marked_expired_ids = []

    def get_expired_users(self):
        return [
            (1001, "user1", "User 1", "tg_1001", "active", -1, 30),
            (1002, "user2", "User 2", "tg_1002", "trial", -2, 30),
        ]

    def get_expiring_users(self, days_before_expire: int = 7):
        return [
            (1003, "user3", "User 3", "tg_1003", "active", 3, 30),
        ]

    def mark_users_as_expired(self, telegram_ids):
        self.marked_expired_ids = telegram_ids
        return len(telegram_ids)


class EmptyBotRepository(FakeBotRepository):
    def get_expired_users(self):
        return []


class FakeXuiRepository:
    def __init__(self):
        self.disabled_ids = []

    def set_client_enabled(self, telegram_id: int, is_enabled: bool):
        if not is_enabled:
            self.disabled_ids.append(telegram_id)

        return True


class PartiallyFailingXuiRepository(FakeXuiRepository):
    def set_client_enabled(self, telegram_id: int, is_enabled: bool):
        if telegram_id == 1002:
            return False

        return super().set_client_enabled(telegram_id, is_enabled)


def test_disable_expired_users_disables_users_and_marks_expired():
    bot_repository = FakeBotRepository()
    xui_repository = FakeXuiRepository()

    service = SubscriptionService(
        bot_repository=bot_repository,
        xui_repository=xui_repository,
    )

    disabled_ids = service.disable_expired_users()

    assert disabled_ids == [1001, 1002]
    assert xui_repository.disabled_ids == [1001, 1002]
    assert bot_repository.marked_expired_ids == [1001, 1002]


def test_disable_expired_users_returns_empty_list_when_no_expired_users():
    bot_repository = EmptyBotRepository()
    xui_repository = FakeXuiRepository()

    service = SubscriptionService(
        bot_repository=bot_repository,
        xui_repository=xui_repository,
    )

    disabled_ids = service.disable_expired_users()

    assert disabled_ids == []
    assert xui_repository.disabled_ids == []
    assert bot_repository.marked_expired_ids == []


def test_disable_expired_users_marks_only_successfully_disabled_users():
    bot_repository = FakeBotRepository()
    xui_repository = PartiallyFailingXuiRepository()

    service = SubscriptionService(
        bot_repository=bot_repository,
        xui_repository=xui_repository,
    )

    disabled_ids = service.disable_expired_users()

    assert disabled_ids == [1001]
    assert xui_repository.disabled_ids == [1001]
    assert bot_repository.marked_expired_ids == [1001]


def test_get_expiring_users_by_days_returns_repository_result():
    bot_repository = FakeBotRepository()
    xui_repository = FakeXuiRepository()

    service = SubscriptionService(
        bot_repository=bot_repository,
        xui_repository=xui_repository,
    )

    users = service.get_expiring_users_by_days(days_before_expire=7)

    assert users == [
        (1003, "user3", "User 3", "tg_1003", "active", 3, 30),
    ]


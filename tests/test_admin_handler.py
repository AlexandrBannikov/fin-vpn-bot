import pytest

from app.handlers.admin_handler import (
    build_access_denied_text,
    build_admin_expiring_text,
    build_admin_stats_text,
    build_admin_users_text,
    build_cleanup_result_text,
    build_extend_success_text,
    admin_stats_handler,
    extend_subscription_handler,
    build_user_not_found_text,
    is_admin,
    parse_extend_command,
    register_admin_handlers,
)


class FakeBotRepository:
    def __init__(self, role: str = "user", extend_result: bool = True):
        self.role = role
        self.extend_result = extend_result
        self.extended_telegram_id = None
        self.extended_days = None

    def count_users(self):
        return 4

    def count_all_referrals(self):
        return 3

    def get_user_role(self, telegram_id: int) -> str:
        return self.role

    def extend_subscription(self, telegram_id: int, days: int) -> bool:
        self.extended_telegram_id = telegram_id
        self.extended_days = days

        return self.extend_result

    def get_users_with_subscription_info(self):
        return [
            (
                228333796,
                "Alexandr1977",
                "Александр",
                "tg_228333796",
                None,
                "active",
                10,
                60,
            ),
            (
                607553143,
                "motylek_photo",
                "Юлия",
                "tg_607553143",
                228333796,
                "trial",
                5,
                30,
            ),
        ]

    def get_expiring_users(self, days_before_expire: int = 3):
        return [
            (
                607553143,
                "motylek_photo",
                "Юлия",
                "tg_607553143",
                "trial",
                2,
                30,
            ),
        ]


class EmptyBotRepository(FakeBotRepository):
    def get_users_with_subscription_info(self):
        return []

    def get_expiring_users(self, days_before_expire: int = 3):
        return []


class FakeXuiRepository:
    def __init__(self):
        self.enabled_telegram_id = None
        self.enabled_status = None

    def count_clients(self):
        return 17

    def count_bot_clients(self):
        return 4

    def count_invite_clients(self):
        return 8

    def count_other_clients(self):
        return 5

    def set_client_enabled(self, telegram_id: int, is_enabled: bool):
        self.enabled_telegram_id = telegram_id
        self.enabled_status = is_enabled

        return True


class FakeBot:
    async def send_message(self, chat_id, text, reply_markup=None):
        return None


class FakeInviteRepository:
    def count_all_invite_links(self):
        return 5

    def count_used_invite_links(self):
        return 0

    def count_unused_invite_links(self):
        return 5

    def delete_used_invite_links(self):
        return 3


def test_register_admin_handlers():
    router = register_admin_handlers(
        bot_repository=FakeBotRepository(),
        xui_repository=FakeXuiRepository(),
        invite_repository=FakeInviteRepository(),
        bot=FakeBot(),
    )

    assert router is not None


def test_build_admin_stats_text():
    text = build_admin_stats_text(
        bot_repository=FakeBotRepository(),
        xui_repository=FakeXuiRepository(),
        invite_repository=FakeInviteRepository(),
    )

    assert "👥 Пользователей: 4" in text
    assert "🤝 Рефералов: 3" in text
    assert "🎁 Инвайтов создано: 5" in text
    assert "✅ Инвайтов использовано: 0" in text
    assert "⏳ Инвайтов ожидает: 5" in text
    assert "🔐 VPN-клиентов всего: 17" in text
    assert "👤 Клиентов бота: 4" in text
    assert "🎁 Invite-клиентов: 8" in text
    assert "🧪 Прочих клиентов: 5" in text


def test_build_cleanup_result_text():
    text = build_cleanup_result_text(deleted_count=3)

    assert "🧹 Очистка завершена." in text
    assert "Удалено использованных инвайтов: 3" in text


def test_build_admin_users_text_returns_users():
    text = build_admin_users_text(FakeBotRepository())

    assert "👥 Пользователи VPN:" in text
    assert "👤 Александр (@Alexandr1977)" in text
    assert "ID: 228333796" in text
    assert "VPN: tg_228333796" in text
    assert "Статус: active" in text
    assert "Подключен: 10 из 60 дней" in text
    assert "Реферер: нет" in text

    assert "👤 Юлия (@motylek_photo)" in text
    assert "ID: 607553143" in text
    assert "VPN: tg_607553143" in text
    assert "Статус: trial" in text
    assert "Подключен: 5 из 30 дней" in text
    assert "Реферер: 228333796" in text


def test_build_admin_users_text_returns_empty_message():
    text = build_admin_users_text(EmptyBotRepository())

    assert text == "👥 Пользователей пока нет."


def test_build_admin_expiring_text_returns_users():
    text = build_admin_expiring_text(FakeBotRepository())

    assert "⚠️ Подписки заканчиваются в ближайшие 3 дня:" in text
    assert "👤 Юлия (@motylek_photo)" in text
    assert "ID: 607553143" in text
    assert "VPN: tg_607553143" in text
    assert "Статус: trial" in text
    assert "Осталось дней: 2" in text
    assert "Всего дней: 30" in text


def test_build_admin_expiring_text_returns_empty_message():
    text = build_admin_expiring_text(EmptyBotRepository())

    assert text == "✅ В ближайшие 3 дня подписки не заканчиваются."


def test_is_admin_returns_true_for_owner():
    bot_repository = FakeBotRepository(role="owner")

    assert is_admin(bot_repository, 228333796) is True


def test_is_admin_returns_true_for_admin():
    bot_repository = FakeBotRepository(role="admin")

    assert is_admin(bot_repository, 123456789) is True


def test_is_admin_returns_false_for_user():
    bot_repository = FakeBotRepository(role="user")

    assert is_admin(bot_repository, 123456789) is False


def test_parse_extend_command_returns_values_for_valid_command():
    telegram_id, days, error_text = parse_extend_command("/extend 228333796 30")

    assert telegram_id == 228333796
    assert days == 30
    assert error_text is None


def test_parse_extend_command_returns_error_for_wrong_format():
    telegram_id, days, error_text = parse_extend_command("/extend 228333796")

    assert telegram_id is None
    assert days is None
    assert "❌ Неверный формат команды." in error_text


def test_parse_extend_command_returns_error_for_non_numeric_values():
    telegram_id, days, error_text = parse_extend_command("/extend abc days")

    assert telegram_id is None
    assert days is None
    assert error_text == "❌ Telegram ID и количество дней должны быть числами."


def test_parse_extend_command_returns_error_for_zero_days():
    telegram_id, days, error_text = parse_extend_command("/extend 228333796 0")

    assert telegram_id is None
    assert days is None
    assert error_text == "❌ Количество дней должно быть больше нуля."


def test_parse_extend_command_returns_error_for_negative_days():
    telegram_id, days, error_text = parse_extend_command("/extend 228333796 -5")

    assert telegram_id is None
    assert days is None
    assert error_text == "❌ Количество дней должно быть больше нуля."


def test_parse_extend_command_returns_error_for_empty_command():
    telegram_id, days, error_text = parse_extend_command(None)

    assert telegram_id is None
    assert days is None
    assert "❌ Неверный формат команды." in error_text


def test_build_extend_success_text():
    text = build_extend_success_text(228333796, 30)

    assert text == "✅ Подписка пользователя 228333796 продлена на 30 дней."


def test_build_user_not_found_text():
    assert build_user_not_found_text() == "❌ Пользователь не найден."


def test_build_access_denied_text():
    assert build_access_denied_text() == "⛔ Нет доступа."


class FakeTelegramUser:
    id = 228333796


class FakeMessage:
    def __init__(self, text: str):
        self.text = text
        self.from_user = FakeTelegramUser()
        self.answers = []

    async def answer(self, text, reply_markup=None):
        self.answers.append(
            {
                "text": text,
                "reply_markup": reply_markup,
            }
        )


@pytest.mark.anyio
async def test_extend_subscription_handler_success():
    """
    Проверяем успешное продление подписки админом.
    """
    message = FakeMessage("/extend 607553143 30")
    bot_repository = FakeBotRepository(role="owner", extend_result=True)
    xui_repository = FakeXuiRepository()

    await extend_subscription_handler(
        message=message,
        bot_repository=bot_repository,
        xui_repository=xui_repository,
    )

    assert bot_repository.extended_telegram_id == 607553143
    assert bot_repository.extended_days == 30

    assert xui_repository.enabled_telegram_id == 607553143
    assert xui_repository.enabled_status is True

    assert message.answers[0]["text"] == "✅ Подписка пользователя 607553143 продлена на 30 дней."


@pytest.mark.anyio
async def test_extend_subscription_handler_denies_user_access():
    """
    Проверяем, что обычный пользователь не может продлевать подписки.
    """
    message = FakeMessage("/extend 607553143 30")
    bot_repository = FakeBotRepository(role="user", extend_result=True)
    xui_repository = FakeXuiRepository()

    await extend_subscription_handler(
        message=message,
        bot_repository=bot_repository,
        xui_repository=xui_repository,
    )

    assert message.answers[0]["text"] == "⛔ Нет доступа."
    assert bot_repository.extended_telegram_id is None
    assert xui_repository.enabled_telegram_id is None


@pytest.mark.anyio
async def test_extend_subscription_handler_returns_error_for_unknown_user():
    """
    Проверяем ошибку, если продлеваемого пользователя нет в базе.
    """
    message = FakeMessage("/extend 607553143 30")
    bot_repository = FakeBotRepository(role="owner", extend_result=False)
    xui_repository = FakeXuiRepository()

    await extend_subscription_handler(
        message=message,
        bot_repository=bot_repository,
        xui_repository=xui_repository,
    )

    assert message.answers[0]["text"] == "❌ Пользователь не найден."
    assert xui_repository.enabled_telegram_id is None


@pytest.mark.anyio
async def test_admin_stats_handler_returns_statistics_for_owner():
    """
    Проверяем выдачу статистики владельцу.
    """
    message = FakeMessage("/admin")

    await admin_stats_handler(
        message=message,
        bot_repository=FakeBotRepository(role="owner"),
        xui_repository=FakeXuiRepository(),
        invite_repository=FakeInviteRepository(),
    )

    assert len(message.answers) == 1
    assert "📈 Статистика проекта:" in message.answers[0]["text"]


@pytest.mark.anyio
async def test_admin_stats_handler_denies_access_for_user():
    """
    Проверяем запрет доступа обычному пользователю.
    """
    message = FakeMessage("/admin")

    await admin_stats_handler(
        message=message,
        bot_repository=FakeBotRepository(role="user"),
        xui_repository=FakeXuiRepository(),
        invite_repository=FakeInviteRepository(),
    )

    assert len(message.answers) == 1
    assert message.answers[0]["text"] == "⛔ Нет доступа."

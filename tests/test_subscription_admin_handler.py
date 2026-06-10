from app.handlers.subscription_admin_handler import (
    build_disable_success_text,
    build_enable_success_text,
    parse_user_control_command,
)


class FakeUser:
    """
    Фейковый Telegram-пользователь.
    """

    def __init__(self, user_id: int):
        self.id = user_id


class FakeMessage:
    """
    Фейковое Telegram-сообщение.
    """

    def __init__(self, text: str, user_id: int):
        self.text = text
        self.from_user = FakeUser(user_id)
        self.answers = []

    async def answer(self, text: str):
        """
        Запоминает ответы handler вместо отправки в Telegram.
        """
        self.answers.append(text)


def test_parse_user_control_command_returns_telegram_id():
    telegram_id, error_text = parse_user_control_command(
        "/disable 228333796",
        "disable",
    )

    assert telegram_id == 228333796
    assert error_text is None


def test_parse_user_control_command_returns_error_for_wrong_format():
    telegram_id, error_text = parse_user_control_command(
        "/disable",
        "disable",
    )

    assert telegram_id is None
    assert "Неверный формат" in error_text


def test_parse_user_control_command_returns_error_for_non_numeric_id():
    telegram_id, error_text = parse_user_control_command(
        "/enable abc",
        "enable",
    )

    assert telegram_id is None
    assert "Telegram ID должен быть числом" in error_text


def test_build_disable_success_text():
    text = build_disable_success_text(228333796)

    assert "228333796" in text
    assert "отключён" in text


def test_build_enable_success_text():
    text = build_enable_success_text(228333796)

    assert "228333796" in text
    assert "включён" in text

import pytest

from app.handlers.subscription_admin_handler import (
    handle_disable_user_command,
    handle_enable_user_command,
)


class FakeMessage:
    def __init__(self, text: str, user_id: int):
        self.text = text
        self.answers = []

        class User:
            pass

        self.from_user = User()
        self.from_user.id = user_id

    async def answer(self, text: str):
        self.answers.append(text)


class AdminBotRepository:
    def __init__(self):
        self.expired_users = []
        self.extended_users = []

    def get_user_role(self, telegram_id: int):
        return "owner"

    def mark_users_as_expired(self, telegram_ids):
        self.expired_users.extend(telegram_ids)

    def extend_subscription(self, telegram_id: int, days: int):
        self.extended_users.append((telegram_id, days))


class UserBotRepository(AdminBotRepository):
    def get_user_role(self, telegram_id: int):
        return "user"


class FakeXuiRepository:
    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def set_client_enabled(self, telegram_id: int, is_enabled: bool):
        self.calls.append((telegram_id, is_enabled))
        return self.result


@pytest.mark.anyio
async def test_disable_user_success():
    message = FakeMessage("/disable 228333796", 1)

    bot_repository = AdminBotRepository()
    xui_repository = FakeXuiRepository(True)

    await handle_disable_user_command(
        message,
        bot_repository,
        xui_repository,
    )

    assert bot_repository.expired_users == [228333796]
    assert "отключён" in message.answers[0]


@pytest.mark.anyio
async def test_enable_user_success():
    message = FakeMessage("/enable 228333796", 1)

    bot_repository = AdminBotRepository()
    xui_repository = FakeXuiRepository(True)

    await handle_enable_user_command(
        message,
        bot_repository,
        xui_repository,
    )

    assert bot_repository.extended_users == [
        (228333796, 1)
    ]
    assert "включён" in message.answers[0]


@pytest.mark.anyio
async def test_disable_access_denied():
    message = FakeMessage("/disable 228333796", 1)

    await handle_disable_user_command(
        message,
        UserBotRepository(),
        FakeXuiRepository(True),
    )

    assert message.answers == ["⛔ Нет доступа."]


@pytest.mark.anyio
async def test_enable_access_denied():
    message = FakeMessage("/enable 228333796", 1)

    await handle_enable_user_command(
        message,
        UserBotRepository(),
        FakeXuiRepository(True),
    )

    assert message.answers == ["⛔ Нет доступа."]


@pytest.mark.anyio
async def test_disable_user_not_found():
    message = FakeMessage("/disable 228333796", 1)

    await handle_disable_user_command(
        message,
        AdminBotRepository(),
        FakeXuiRepository(False),
    )

    assert message.answers == ["❌ Пользователь не найден."]


@pytest.mark.anyio
async def test_enable_user_not_found():
    message = FakeMessage("/enable 228333796", 1)

    await handle_enable_user_command(
        message,
        AdminBotRepository(),
        FakeXuiRepository(False),
    )

    assert message.answers == ["❌ Пользователь не найден."]


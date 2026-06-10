import pytest

from app.handlers.referral_handler import (
    build_referral_link,
    build_referral_stats_text,
    handle_referral_link_command,
    handle_referral_stats_command,
    register_referral_handlers,
)


class FakeUser:
    def __init__(self, user_id: int):
        self.id = user_id


class FakeMessage:
    def __init__(self, user_id: int):
        self.from_user = FakeUser(user_id)
        self.answers = []

    async def answer(self, text: str, reply_markup=None):
        self.answers.append((text, reply_markup))


class FakeBotRepository:
    def count_referrals(self, telegram_id: int) -> int:
        return 3


class FakeUserService:
    def __init__(self):
        self.saved_messages = []

    def save_user_from_message(self, message):
        self.saved_messages.append(message)


class FakeBot:
    async def get_me(self):
        class BotInfo:
            username = "FinVpnBot"

        return BotInfo()


def test_register_referral_handlers_returns_router():
    router = register_referral_handlers(
        bot_repository=FakeBotRepository(),
        user_service=FakeUserService(),
        bot=FakeBot(),
    )

    assert router is not None


def test_build_referral_link_returns_telegram_start_link():
    link = build_referral_link(
        bot_username="FinVpnBot",
        user_id=228333796,
    )

    assert link == "https://t.me/FinVpnBot?start=228333796"


def test_build_referral_stats_text_returns_total():
    text = build_referral_stats_text(3)

    assert text == "📊 Приглашено: 3"


@pytest.mark.anyio
async def test_handle_referral_link_command_sends_link():
    message = FakeMessage(user_id=228333796)
    user_service = FakeUserService()

    await handle_referral_link_command(
        message=message,
        user_service=user_service,
        bot=FakeBot(),
    )

    assert user_service.saved_messages == [message]
    assert message.answers[0][0] == "https://t.me/FinVpnBot?start=228333796"


@pytest.mark.anyio
async def test_handle_referral_stats_command_sends_stats():
    message = FakeMessage(user_id=228333796)
    user_service = FakeUserService()

    await handle_referral_stats_command(
        message=message,
        bot_repository=FakeBotRepository(),
        user_service=user_service,
    )

    assert user_service.saved_messages == [message]
    assert message.answers[0][0] == "📊 Приглашено: 3"


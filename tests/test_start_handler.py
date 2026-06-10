import pytest

from app.handlers.start_handler import (
    build_start_text,
    parse_referrer_id,
    register_start_handlers,
    start_handler,
)


class FakeTelegramUser:
    id = 228333796


class FakeMessage:
    def __init__(self, text="/start 111"):
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


class FakeUserService:
    def __init__(self):
        self.saved_message = None
        self.saved_referrer_id = None

    def save_user_from_message(self, message, referrer_id):
        self.saved_message = message
        self.saved_referrer_id = referrer_id

    def get_user_role_from_message(self, message):
        return "owner"


def test_register_start_handlers_returns_router():
    """
    Проверяем, что start-обработчик регистрируется и возвращает router.
    """
    router = register_start_handlers(FakeUserService())

    assert router is not None


@pytest.mark.anyio
async def test_start_handler_saves_user_and_sends_start_text():
    """
    Проверяем, что start_handler сохраняет пользователя и отправляет стартовое меню.
    """
    message = FakeMessage()
    user_service = FakeUserService()

    await start_handler(message, user_service)

    assert user_service.saved_message == message
    assert user_service.saved_referrer_id == 111

    assert len(message.answers) == 1
    assert "Привет 👋" in message.answers[0]["text"]
    assert message.answers[0]["reply_markup"] is not None


def test_build_start_text_contains_main_message():
    """
    Проверяем приветственный текст.
    """
    text = build_start_text()

    assert "Привет 👋" in text
    assert "Это бот для подключения VPN." in text
    assert "Нажмите кнопку ниже" in text


def test_parse_referrer_id_returns_number():
    """
    Проверяем, что корректный referrer_id достаётся из /start.
    """
    assert parse_referrer_id("/start 228333796") == 228333796


def test_parse_referrer_id_returns_none_without_argument():
    """
    Проверяем /start без аргумента.
    """
    assert parse_referrer_id("/start") is None


def test_parse_referrer_id_returns_none_for_invalid_argument():
    """
    Проверяем защиту от мусора вместо числа.
    """
    assert parse_referrer_id("/start abc") is None


def test_parse_referrer_id_returns_none_for_empty_text():
    """
    Проверяем пустой текст сообщения.
    """
    assert parse_referrer_id(None) is None

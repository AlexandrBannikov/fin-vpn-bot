import pytest

from app.handlers.invite_handler import (
    build_invite_qr_caption,
    build_invite_text,
    register_invite_handlers,
    send_invite_link,
)


class FakeTelegramUser:
    id = 228333796


class FakeMessage:
    def __init__(self):
        self.from_user = FakeTelegramUser()
        self.answers = []
        self.photos = []

    async def answer(self, text, reply_markup=None):
        self.answers.append(
            {
                "text": text,
                "reply_markup": reply_markup,
            }
        )

    async def answer_photo(self, photo, caption=None):
        self.photos.append(
            {
                "photo": photo,
                "caption": caption,
            }
        )


class FakeUserService:
    def __init__(self):
        self.saved_message = None

    def save_user_from_message(self, message):
        self.saved_message = message


class FakeInviteService:
    def create_invite_link(self, owner_tg_id: int) -> dict:
        return {
            "invite_url": "https://vpn.example.com/i/test-token",
        }


class FakeQrService:
    def make_qr(self, text: str):
        return b"fake-qr"


class FakeMenuService:
    def get_keyboard_for_message(self, message):
        return "fake-keyboard"


def test_register_invite_handlers_returns_router():
    """
    Проверяем, что invite-обработчик регистрируется и возвращает router.
    """
    router = register_invite_handlers(
        user_service=FakeUserService(),
        invite_service=FakeInviteService(),
        qr_service=FakeQrService(),
        menu_service=FakeMenuService(),
    )

    assert router is not None


@pytest.mark.anyio
async def test_send_invite_link_sends_text_and_qr():
    """
    Проверяем, что send_invite_link отправляет ссылку и QR-код.
    """
    message = FakeMessage()
    user_service = FakeUserService()

    await send_invite_link(
        message=message,
        user_service=user_service,
        invite_service=FakeInviteService(),
        qr_service=FakeQrService(),
        menu_service=FakeMenuService(),
    )

    assert user_service.saved_message == message

    assert len(message.answers) == 1
    assert "🎁 Одноразовая пригласительная ссылка для друга:" in message.answers[0]["text"]
    assert "https://vpn.example.com/i/test-token" in message.answers[0]["text"]
    assert message.answers[0]["reply_markup"] == "fake-keyboard"

    assert len(message.photos) == 1
    assert message.photos[0]["photo"] == b"fake-qr"
    assert message.photos[0]["caption"] == "QR-код одноразовой пригласительной ссылки"


def test_build_invite_text_contains_invite_url():
    """
    Проверяем, что текст приглашения содержит ссылку и объяснение.
    """
    text = build_invite_text("https://vpn.example.com/i/test-token")

    assert "🎁 Одноразовая пригласительная ссылка для друга:" in text
    assert "https://vpn.example.com/i/test-token" in text
    assert "SMS, WhatsApp, iMessage" in text
    assert "получит VPN-подписку" in text
    assert "После первого открытия" in text


def test_build_invite_qr_caption_returns_caption():
    """
    Проверяем подпись QR-кода.
    """
    assert build_invite_qr_caption() == "QR-код одноразовой пригласительной ссылки"

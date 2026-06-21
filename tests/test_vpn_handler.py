import pytest

from app.handlers.vpn_handler import (
    build_vpn_qr_caption,
    build_vpn_text,
    register_vpn_handlers,
    send_vpn,
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


class FakeVpnService:
    def get_or_create_client(self, telegram_id: int) -> dict:
        return {
            "sub_id": "test-sub-id",
            "vless_url": "vless://uuid@vpn.example.com:443?type=tcp#tg_228333796",
            "created": True,
        }

    def build_sub_url(self, sub_id: str) -> str:
        return f"https://vpn.example.com/sub/{sub_id}"


class FakeQrService:
    def make_qr(self, text: str):
        return b"fake-qr"


class FakeMenuService:
    def get_keyboard_for_message(self, message):
        return "fake-keyboard"


def test_register_vpn_handlers_returns_router():
    """
    Проверяем, что VPN-обработчики регистрируются и возвращают router.
    """
    router = register_vpn_handlers(
        user_service=FakeUserService(),
        vpn_service=FakeVpnService(),
        qr_service=FakeQrService(),
        menu_service=FakeMenuService(),
    )

    assert router is not None


@pytest.mark.anyio
async def test_send_vpn_sends_subscription_and_qr():
    """
    Проверяем, что send_vpn отправляет ссылку подписки и QR-код.
    """
    message = FakeMessage()
    user_service = FakeUserService()

    await send_vpn(
        message=message,
        user_service=user_service,
        vpn_service=FakeVpnService(),
        qr_service=FakeQrService(),
        menu_service=FakeMenuService(),
    )

    assert user_service.saved_message == message

    assert len(message.answers) == 1
    assert "✅ VPN создан." in message.answers[0]["text"]
    assert "vless://uuid@vpn.example.com:443?type=tcp#tg_228333796" in message.answers[0]["text"]
    assert "https://vpn.example.com/sub/test-sub-id" in message.answers[0]["text"]
    assert message.answers[0]["reply_markup"] == "fake-keyboard"

    assert len(message.photos) == 1
    assert message.photos[0]["photo"] == b"fake-qr"
    assert message.photos[0]["caption"] == "QR-код прямой VPN-ссылки"


def test_build_vpn_text_for_new_client():
    """
    Проверяем текст для нового VPN-клиента.
    """
    text = build_vpn_text(
        sub_url="https://vpn.example.com/sub/test-sub-id",
        vless_url="vless://uuid@vpn.example.com:443?type=tcp#tg_228333796",
        is_created=True,
    )

    assert "✅ VPN создан." in text
    assert "vless://uuid@vpn.example.com:443?type=tcp#tg_228333796" in text
    assert "https://vpn.example.com/sub/test-sub-id" in text
    assert "Добавьте прямую VPN-ссылку или QR-код" in text
    assert "можно добавить ссылку подписки" in text


def test_build_vpn_text_for_existing_client():
    """
    Проверяем текст для уже существующего VPN-клиента.
    """
    text = build_vpn_text(
        sub_url="https://vpn.example.com/sub/test-sub-id",
        vless_url="vless://uuid@vpn.example.com:443?type=tcp#tg_228333796",
        is_created=False,
    )

    assert "✅ VPN уже создан." in text
    assert "vless://uuid@vpn.example.com:443?type=tcp#tg_228333796" in text
    assert "https://vpn.example.com/sub/test-sub-id" in text


def test_build_vpn_qr_caption_returns_caption():
    """
    Проверяем подпись QR-кода VPN-подписки.
    """
    assert build_vpn_qr_caption() == "QR-код прямой VPN-ссылки"

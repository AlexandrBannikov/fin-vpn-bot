from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.menu_service import MenuService
from app.services.qr_service import QrService
from app.services.user_service import UserService
from app.services.vpn_service import VpnService

router = Router()


def build_vpn_text(sub_url: str, is_created: bool) -> str:
    """
    Формирует текст с VPN-подпиской.

    Если клиент создан впервые — показываем "VPN создан".
    Если клиент уже существовал — показываем "VPN уже создан".
    """
    status_text = "✅ VPN создан." if is_created else "✅ VPN уже создан."

    return (
        f"{status_text}\n\n"
        f"🔗 Ссылка подписки:\n\n"
        f"{sub_url}\n\n"
        f"1. Установите приложение.\n"
        f"2. Добавьте подписку по ссылке или QR-коду.\n"
        f"3. Обновите подписку в приложении."
    )


def build_vpn_qr_caption() -> str:
    """
    Формирует подпись к QR-коду VPN-подписки.
    """
    return "QR-код подписки"


async def send_vpn(
    message: Message,
    user_service: UserService,
    vpn_service: VpnService,
    qr_service: QrService,
    menu_service: MenuService,
) -> None:
    """
    Отправляет пользователю VPN-ссылку и QR-код подписки.
    """
    user_service.save_user_from_message(message)

    client = vpn_service.get_or_create_client(message.from_user.id)
    sub_url = vpn_service.build_sub_url(client["sub_id"])
    qr = qr_service.make_qr(sub_url)

    await message.answer(
        build_vpn_text(
            sub_url=sub_url,
            is_created=client["created"],
        ),
        reply_markup=menu_service.get_keyboard_for_message(message),
    )

    await message.answer_photo(qr, caption=build_vpn_qr_caption())


def register_vpn_handlers(
    user_service: UserService,
    vpn_service: VpnService,
    qr_service: QrService,
    menu_service: MenuService,
) -> Router:
    @router.message(Command("getvpn"))
    async def getvpn_command(message: Message):
        await send_vpn(message, user_service, vpn_service, qr_service, menu_service)

    @router.message(Command("myvpn"))
    async def myvpn_command(message: Message):
        await send_vpn(message, user_service, vpn_service, qr_service, menu_service)

    @router.message(F.text == "🔑 Получить VPN")
    async def getvpn_button(message: Message):
        await send_vpn(message, user_service, vpn_service, qr_service, menu_service)

    @router.message(F.text == "👤 Мой VPN")
    async def myvpn_button(message: Message):
        await send_vpn(message, user_service, vpn_service, qr_service, menu_service)

    return router

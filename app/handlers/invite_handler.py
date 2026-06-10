from aiogram import F, Router
from aiogram.types import Message

from app.services.invite_service import InviteService
from app.services.menu_service import MenuService
from app.services.qr_service import QrService
from app.services.user_service import UserService

router = Router()


def build_invite_text(invite_url: str) -> str:
    """
    Формирует текст одноразовой пригласительной ссылки.
    """
    return (
        "🎁 Одноразовая пригласительная ссылка для друга:\n\n"
        f"{invite_url}\n\n"
        "Эту ссылку можно отправить в SMS, WhatsApp, iMessage или куда угодно.\n"
        "Друг откроет её в браузере и получит VPN-подписку.\n\n"
        "После первого открытия ссылка больше не покажет подписку."
    )


def build_invite_qr_caption() -> str:
    """
    Формирует подпись к QR-коду пригласительной ссылки.
    """
    return "QR-код одноразовой пригласительной ссылки"


async def send_invite_link(
    message: Message,
    user_service: UserService,
    invite_service: InviteService,
    qr_service: QrService,
    menu_service: MenuService,
) -> None:
    """
    Создаёт и отправляет одноразовую пригласительную ссылку.
    """
    user_service.save_user_from_message(message)

    invite = invite_service.create_invite_link(message.from_user.id)
    qr = qr_service.make_qr(invite["invite_url"])

    await message.answer(
        build_invite_text(invite["invite_url"]),
        reply_markup=menu_service.get_keyboard_for_message(message),
    )

    await message.answer_photo(qr, caption=build_invite_qr_caption())


def register_invite_handlers(
    user_service: UserService,
    invite_service: InviteService,
    qr_service: QrService,
    menu_service: MenuService,
) -> Router:
    @router.message(F.text == "🎁 Пригласительная ссылка")
    async def invite_link_button(message: Message):
        await send_invite_link(
            message=message,
            user_service=user_service,
            invite_service=invite_service,
            qr_service=qr_service,
            menu_service=menu_service,
        )

    return router

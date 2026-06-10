from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.menu_service import MenuService

router = Router()


def build_help_text() -> str:
    """
    Формирует текст помощи по подключению VPN.
    """
    return (
        "ℹ️ Как подключиться:\n\n"
        "1. Нажмите «📱 Скачать приложение».\n"
        "2. Установите Happ или 2rayTun.\n"
        "3. Нажмите «🔑 Получить VPN».\n"
        "4. Добавьте подписку по QR-коду или ссылке.\n\n"
        "Если VPN уже был создан — нажмите «👤 Мой VPN»."
    )


def register_help_handlers(menu_service: MenuService) -> Router:
    async def send_help(message: Message):
        await message.answer(
            build_help_text(),
            reply_markup=menu_service.get_keyboard_for_message(message),
        )

    @router.message(Command("help"))
    async def help_command(message: Message):
        await send_help(message)

    @router.message(F.text == "ℹ️ Помощь")
    async def help_button(message: Message):
        await send_help(message)

    return router

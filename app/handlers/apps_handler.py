from aiogram import F, Router
from aiogram.types import Message

from app.keyboards import app_keyboard


router = Router()


def build_apps_text() -> str:
    """
    Формирует текст для кнопки скачивания приложения.
    """
    return "📱 Скачайте приложение для подключения:"


def register_apps_handlers() -> Router:
    @router.message(F.text == "📱 Скачать приложение")
    async def apps_button(message: Message):
        await message.answer(
            build_apps_text(),
            reply_markup=app_keyboard,
        )

    return router


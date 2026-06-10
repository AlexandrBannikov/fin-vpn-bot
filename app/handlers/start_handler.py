from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards import get_keyboard_by_role
from app.services.user_service import UserService

router = Router()


def build_start_text() -> str:
    """
    Формирует приветственный текст бота.
    """
    return (
        "Привет 👋\n\n"
        "Это бот для подключения VPN.\n"
        "Нажмите кнопку ниже, чтобы получить VPN."
    )


def parse_referrer_id(message_text: str | None) -> int | None:
    """
    Достаёт referrer_id из команды /start.

    Примеры:
    - /start 123 -> 123
    - /start abc -> None
    - /start -> None
    """
    if not message_text:
        return None

    parts = message_text.split()

    if len(parts) <= 1:
        return None

    try:
        return int(parts[1])
    except ValueError:
        return None


async def start_handler(message: Message, user_service: UserService) -> None:
    """
    Обрабатывает команду /start.

    Сохраняет пользователя, учитывает referrer_id
    и показывает меню по роли пользователя.
    """
    referrer_id = parse_referrer_id(message.text)

    user_service.save_user_from_message(message, referrer_id)

    role = user_service.get_user_role_from_message(message)

    await message.answer(
        build_start_text(),
        reply_markup=get_keyboard_by_role(role),
    )


def register_start_handlers(user_service: UserService) -> Router:
    @router.message(CommandStart())
    async def start(message: Message):
        await start_handler(message, user_service)

    return router

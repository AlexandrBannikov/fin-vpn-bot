from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.handlers.admin_handler import (
    build_access_denied_text,
    build_user_not_found_text,
    is_admin,
)
from app.repositories.bot_repository import BotRepository
from app.repositories.xui_repository import XuiRepository

router = Router()


def parse_user_control_command(command_text: str | None, command_name: str) -> tuple[int | None, str | None]:
    """
    Разбирает команды ручного управления пользователем.

    Формат:
    /disable <telegram_id>
    /enable <telegram_id>
    """
    parts = (command_text or "").split()

    if len(parts) != 2:
        return None, (
            "❌ Неверный формат команды.\n"
            "Используй так:\n"
            f"/{command_name} 228333796"
        )

    try:
        telegram_id = int(parts[1])
    except ValueError:
        return None, "❌ Telegram ID должен быть числом."

    return telegram_id, None


def build_disable_success_text(telegram_id: int) -> str:
    """
    Формирует текст успешного отключения пользователя.
    """
    return f"⛔ Пользователь {telegram_id} отключён от VPN."


def build_enable_success_text(telegram_id: int) -> str:
    """
    Формирует текст успешного включения пользователя.
    """
    return f"✅ Пользователь {telegram_id} включён в VPN."


async def handle_disable_user_command(
    message: Message,
    bot_repository: BotRepository,
    xui_repository: XuiRepository,
) -> None:
    """
    Выполняет команду /disable.
    """
    if not is_admin(bot_repository, message.from_user.id):
        await message.answer(build_access_denied_text())
        return

    telegram_id, error_text = parse_user_control_command(
        command_text=message.text,
        command_name="disable",
    )

    if error_text:
        await message.answer(error_text)
        return

    is_disabled = xui_repository.set_client_enabled(
        telegram_id=telegram_id,
        is_enabled=False,
    )

    if not is_disabled:
        await message.answer(build_user_not_found_text())
        return

    bot_repository.mark_users_as_expired([telegram_id])

    await message.answer(build_disable_success_text(telegram_id))


async def handle_enable_user_command(
    message: Message,
    bot_repository: BotRepository,
    xui_repository: XuiRepository,
) -> None:
    """
    Выполняет команду /enable.
    """
    if not is_admin(bot_repository, message.from_user.id):
        await message.answer(build_access_denied_text())
        return

    telegram_id, error_text = parse_user_control_command(
        command_text=message.text,
        command_name="enable",
    )

    if error_text:
        await message.answer(error_text)
        return

    is_enabled = xui_repository.set_client_enabled(
        telegram_id=telegram_id,
        is_enabled=True,
    )

    if not is_enabled:
        await message.answer(build_user_not_found_text())
        return

    bot_repository.extend_subscription(
        telegram_id=telegram_id,
        days=1,
    )

    await message.answer(build_enable_success_text(telegram_id))


def register_subscription_admin_handlers(
    bot_repository: BotRepository,
    xui_repository: XuiRepository,
) -> Router:
    """
    Регистрирует админ-команды управления VPN-подпиской.
    """

    @router.message(Command("disable"))
    async def disable_user_command(message: Message):
        await handle_disable_user_command(
            message=message,
            bot_repository=bot_repository,
            xui_repository=xui_repository,
        )

    @router.message(Command("enable"))
    async def enable_user_command(message: Message):
        await handle_enable_user_command(
            message=message,
            bot_repository=bot_repository,
            xui_repository=xui_repository,
        )

    return router


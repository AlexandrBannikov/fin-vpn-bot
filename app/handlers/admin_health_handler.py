import sqlite3

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import BOT_DB_PATH, INBOUND_ID, XUI_DB_PATH
from app.db import connect_sqlite
from app.handlers.admin_handler import build_access_denied_text, is_admin
from app.repositories.bot_repository import BotRepository
from app.repositories.xui_repository import XuiRepository

router = Router()


def can_open_sqlite_database(db_path: str) -> bool:
    """
    Проверяет, что SQLite-база доступна для открытия.
    """
    try:
        with connect_sqlite(db_path) as conn:
            conn.execute("SELECT 1")
        return True
    except sqlite3.Error:
        return False


def build_status_icon(is_ok: bool) -> str:
    """
    Возвращает иконку состояния.
    """
    return "🟢" if is_ok else "🔴"


def build_admin_health_text(
    bot_repository: BotRepository,
    xui_repository: XuiRepository,
) -> str:
    """
    Формирует health-check отчёт для админа.
    """
    bot_db_ok = can_open_sqlite_database(BOT_DB_PATH)
    xui_db_ok = can_open_sqlite_database(XUI_DB_PATH)

    inbound = None
    if xui_db_ok:
        inbound = xui_repository.get_inbound_by_id(INBOUND_ID)

    inbound_ok = inbound is not None

    users_count = bot_repository.count_users() if bot_db_ok else 0
    vpn_clients_count = xui_repository.count_clients() if xui_db_ok else 0

    system_ok = bot_db_ok and xui_db_ok and inbound_ok

    return (
        "🩺 Health-check VPN Bot:\n\n"
        f"{build_status_icon(bot_db_ok)} bot.db доступна\n"
        f"{build_status_icon(xui_db_ok)} x-ui.db доступна\n"
        f"{build_status_icon(inbound_ok)} inbound #{INBOUND_ID} найден\n\n"
        f"👥 Пользователей в боте: {users_count}\n"
        f"🔐 VPN-клиентов в 3X-UI: {vpn_clients_count}\n\n"
        f"{build_status_icon(system_ok)} Общий статус: "
        f"{'система исправна' if system_ok else 'есть проблема'}"
    )


def register_admin_health_handlers(
    bot_repository: BotRepository,
    xui_repository: XuiRepository,
) -> Router:
    """
    Регистрирует команду /admin_health.
    """

    @router.message(Command("admin_health"))
    async def admin_health_command(message: Message):
        """
        Показывает техническое состояние VPN-бота.
        """
        if not is_admin(bot_repository, message.from_user.id):
            await message.answer(build_access_denied_text())
            return

        await message.answer(
            build_admin_health_text(
                bot_repository=bot_repository,
                xui_repository=xui_repository,
            )
        )

    return router

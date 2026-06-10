import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from app.config import BOT_TOKEN
from app.handlers.admin_handler import register_admin_handlers
from app.handlers.subscription_admin_handler import register_subscription_admin_handlers
from app.handlers.admin_health_handler import register_admin_health_handlers
from app.handlers.apps_handler import register_apps_handlers
from app.handlers.help_handler import register_help_handlers
from app.handlers.invite_handler import register_invite_handlers
from app.handlers.referral_handler import register_referral_handlers
from app.handlers.start_handler import register_start_handlers
from app.handlers.vpn_handler import register_vpn_handlers
from app.repositories.bot_repository import BotRepository
from app.repositories.invite_repository import InviteRepository
from app.repositories.xui_repository import XuiRepository
from app.services.invite_service import InviteService
from app.services.menu_service import MenuService
from app.services.qr_service import QrService
from app.services.user_service import UserService
from app.services.vpn_service import VpnService


async def set_bot_commands(bot: Bot) -> None:
    """
    Регистрирует список команд Telegram-бота.

    После регистрации Telegram показывает эти команды,
    когда пользователь вводит символ '/' в строке сообщения.
    """
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="apps", description="Приложения VPN"),

        BotCommand(command="getvpn", description="Получить VPN"),
        BotCommand(command="myvpn", description="Мой VPN"),

        BotCommand(command="ref", description="Реферальная ссылка"),
        BotCommand(command="refstats", description="Реферальная статистика"),

        BotCommand(command="admin", description="Админ-панель"),
        BotCommand(command="admin_users", description="Пользователи"),
        BotCommand(command="admin_expiring", description="Истекающие подписки"),
        BotCommand(command="admin_health", description="Проверка системы"),
        BotCommand(command="refresh_menu", description="Обновить меню всем"),

        BotCommand(command="extend", description="Продлить подписку"),
        BotCommand(command="disable", description="Отключить пользователя"),
        BotCommand(command="enable", description="Включить пользователя"),
    ])


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    bot_repository = BotRepository()
    xui_repository = XuiRepository()
    invite_repository = InviteRepository()

    vpn_service = VpnService(xui_repository)
    qr_service = QrService()
    user_service = UserService(bot_repository, vpn_service)
    menu_service = MenuService(user_service)
    invite_service = InviteService(invite_repository, vpn_service)

    bot_repository.init_db()

    dp.include_router(register_start_handlers(user_service))
    dp.include_router(register_vpn_handlers(user_service, vpn_service, qr_service, menu_service))
    dp.include_router(register_subscription_admin_handlers(bot_repository, xui_repository))
    dp.include_router(
        register_admin_health_handlers(
            bot_repository,
            xui_repository,
        )
    )
    dp.include_router(register_apps_handlers())
    dp.include_router(register_referral_handlers(bot_repository, user_service, bot))
    dp.include_router(register_invite_handlers(user_service, invite_service, qr_service, menu_service))
    dp.include_router(register_admin_handlers(bot_repository, xui_repository, invite_repository, bot))
    dp.include_router(register_help_handlers(menu_service))

    await set_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

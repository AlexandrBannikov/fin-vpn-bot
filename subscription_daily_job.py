import asyncio

from aiogram import Bot

from app.config import BOT_TOKEN
from app.repositories.bot_repository import BotRepository
from app.repositories.xui_repository import XuiRepository
from app.services.subscription_notification_service import SubscriptionNotificationService
from app.services.subscription_service import SubscriptionService


async def main() -> None:
    """
    Ежедневная задача обслуживания подписок.

    Делает строго по порядку:
    1. Отправляет предупреждения за 7/3/1 день.
    2. Отключает пользователей с истёкшей подпиской.
    """
    bot_repository = BotRepository()
    xui_repository = XuiRepository()

    bot = Bot(token=BOT_TOKEN)

    notification_service = SubscriptionNotificationService(
        bot_repository=bot_repository,
        bot=bot,
    )

    subscription_service = SubscriptionService(
        bot_repository=bot_repository,
        xui_repository=xui_repository,
    )

    try:
        sent_warnings_count = await notification_service.send_expiration_warnings()
        disabled_user_ids = subscription_service.disable_expired_users()

        print(f"Subscription warnings sent: {sent_warnings_count}")
        print(f"Expired users disabled: {disabled_user_ids}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())


from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards import main_keyboard
from app.repositories.bot_repository import BotRepository
from app.services.user_service import UserService

router = Router()


def build_referral_link(bot_username: str, user_id: int) -> str:
    """
    Формирует персональную реферальную ссылку пользователя.
    """
    return f"https://t.me/{bot_username}?start={user_id}"


def build_referral_stats_text(total: int) -> str:
    """
    Формирует текст статистики приглашений.
    """
    return f"📊 Приглашено: {total}"


async def handle_referral_link_command(message: Message, user_service: UserService, bot) -> None:
    """
    Отправляет пользователю его персональную реферальную ссылку.
    """
    user_service.save_user_from_message(message)

    bot_info = await bot.get_me()
    ref_link = build_referral_link(
        bot_username=bot_info.username,
        user_id=message.from_user.id,
    )

    await message.answer(ref_link, reply_markup=main_keyboard)


async def handle_referral_stats_command(
    message: Message,
    bot_repository: BotRepository,
    user_service: UserService,
) -> None:
    """
    Отправляет пользователю статистику его приглашений.
    """
    user_service.save_user_from_message(message)

    total = bot_repository.count_referrals(message.from_user.id)

    await message.answer(
        build_referral_stats_text(total),
        reply_markup=main_keyboard,
    )


def register_referral_handlers(
    bot_repository: BotRepository,
    user_service: UserService,
    bot,
) -> Router:
    @router.message(Command("ref"))
    async def ref_command(message: Message):
        await handle_referral_link_command(
            message=message,
            user_service=user_service,
            bot=bot,
        )

    @router.message(Command("refstats"))
    async def refstats_command(message: Message):
        await handle_referral_stats_command(
            message=message,
            bot_repository=bot_repository,
            user_service=user_service,
        )

    @router.message(F.text == "🔗 Реферальная ссылка")
    async def ref_button(message: Message):
        await handle_referral_link_command(
            message=message,
            user_service=user_service,
            bot=bot,
        )

    @router.message(F.text == "📊 Мои приглашения")
    async def refstats_button(message: Message):
        await handle_referral_stats_command(
            message=message,
            bot_repository=bot_repository,
            user_service=user_service,
        )

    return router


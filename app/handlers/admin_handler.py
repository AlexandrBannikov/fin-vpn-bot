from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards import main_keyboard
from app.repositories.bot_repository import BotRepository
from app.repositories.invite_repository import InviteRepository
from app.repositories.xui_repository import XuiRepository

router = Router()


def is_admin(bot_repository: BotRepository, user_id: int) -> bool:
    """
    Проверяет доступ к админ-командам.
    """
    user_role = bot_repository.get_user_role(user_id)
    return user_role in ("owner", "admin")


def parse_extend_command(command_text: str | None) -> tuple[int | None, int | None, str | None]:
    """
    Разбирает команду продления подписки.

    Формат:
    /extend <telegram_id> <days>
    """
    parts = (command_text or "").split()

    if len(parts) != 3:
        return None, None, (
            "❌ Неверный формат команды.\n"
            "Используй так:\n"
            "/extend 228333796 30"
        )

    try:
        telegram_id = int(parts[1])
        days = int(parts[2])
    except ValueError:
        return None, None, "❌ Telegram ID и количество дней должны быть числами."

    if days <= 0:
        return None, None, "❌ Количество дней должно быть больше нуля."

    return telegram_id, days, None


def build_extend_success_text(telegram_id: int, days: int) -> str:
    """
    Формирует текст успешного продления подписки.
    """
    return f"✅ Подписка пользователя {telegram_id} продлена на {days} дней."


def build_user_not_found_text() -> str:
    """
    Формирует текст ошибки, если пользователь не найден.
    """
    return "❌ Пользователь не найден."


def build_access_denied_text() -> str:
    """
    Формирует текст отказа в доступе.
    """
    return "⛔ Нет доступа."


def build_admin_stats_text(
    bot_repository: BotRepository,
    xui_repository: XuiRepository,
    invite_repository: InviteRepository,
) -> str:
    """
    Формирует общую статистику проекта для админа.
    """
    bot_users = bot_repository.count_users()
    referrals = bot_repository.count_all_referrals()

    vpn_clients = xui_repository.count_clients()
    bot_vpn_clients = xui_repository.count_bot_clients()
    invite_vpn_clients = xui_repository.count_invite_clients()
    other_vpn_clients = xui_repository.count_other_clients()

    invite_links_total = invite_repository.count_all_invite_links()
    invite_links_used = invite_repository.count_used_invite_links()
    invite_links_unused = invite_repository.count_unused_invite_links()

    return (
        "📈 Статистика проекта:\n\n"
        f"👥 Пользователей: {bot_users}\n"
        f"🤝 Рефералов: {referrals}\n\n"
        f"🎁 Инвайтов создано: {invite_links_total}\n"
        f"✅ Инвайтов использовано: {invite_links_used}\n"
        f"⏳ Инвайтов ожидает: {invite_links_unused}\n\n"
        f"🔐 VPN-клиентов всего: {vpn_clients}\n"
        f"👤 Клиентов бота: {bot_vpn_clients}\n"
        f"🎁 Invite-клиентов: {invite_vpn_clients}\n"
        f"🧪 Прочих клиентов: {other_vpn_clients}"
    )


def build_cleanup_result_text(deleted_count: int) -> str:
    """
    Формирует текст результата очистки использованных инвайтов.
    """
    return (
        "🧹 Очистка завершена.\n\n"
        f"Удалено использованных инвайтов: {deleted_count}"
    )


def build_admin_users_text(bot_repository: BotRepository) -> str:
    """
    Формирует текст со списком пользователей и сроком их подписки.
    """
    users = bot_repository.get_users_with_subscription_info()

    if not users:
        return "👥 Пользователей пока нет."

    lines = ["👥 Пользователи VPN:\n"]

    for user in users:
        (
            telegram_id,
            username,
            first_name,
            vpn_email,
            referrer_id,
            subscription_status,
            days_connected,
            subscription_days,
        ) = user

        name = first_name or "Без имени"
        username_text = f"@{username}" if username else "без username"
        referrer_text = str(referrer_id) if referrer_id else "нет"

        lines.append(
            f"👤 {name} ({username_text})\n"
            f"ID: {telegram_id}\n"
            f"VPN: {vpn_email}\n"
            f"Статус: {subscription_status}\n"
            f"Подключен: {days_connected} из {subscription_days} дней\n"
            f"Реферер: {referrer_text}\n"
        )

    return "\n".join(lines)


def build_admin_expiring_text(bot_repository: BotRepository) -> str:
    """
    Формирует текст со списком пользователей,
    у которых подписка заканчивается в ближайшие 3 дня.
    """
    users = bot_repository.get_expiring_users(days_before_expire=3)

    if not users:
        return "✅ В ближайшие 3 дня подписки не заканчиваются."

    lines = ["⚠️ Подписки заканчиваются в ближайшие 3 дня:\n"]

    for user in users:
        (
            telegram_id,
            username,
            first_name,
            vpn_email,
            subscription_status,
            days_left,
            subscription_days,
        ) = user

        name = first_name or "Без имени"
        username_text = f"@{username}" if username else "без username"

        lines.append(
            f"👤 {name} ({username_text})\n"
            f"ID: {telegram_id}\n"
            f"VPN: {vpn_email}\n"
            f"Статус: {subscription_status}\n"
            f"Осталось дней: {days_left}\n"
            f"Всего дней: {subscription_days}\n"
        )

    return "\n".join(lines)


async def extend_subscription_handler(
    message: Message,
    bot_repository: BotRepository,
    xui_repository: XuiRepository,
) -> None:
    """
    Обрабатывает продление подписки пользователя.

    Проверяет права, разбирает команду,
    продлевает подписку и включает клиента в 3X-UI.
    """
    if not is_admin(bot_repository, message.from_user.id):
        await message.answer(build_access_denied_text())
        return

    telegram_id, days, error_text = parse_extend_command(message.text)

    if error_text:
        await message.answer(error_text)
        return

    is_extended = bot_repository.extend_subscription(
        telegram_id=telegram_id,
        days=days,
    )

    if not is_extended:
        await message.answer(build_user_not_found_text())
        return

    xui_repository.set_client_enabled(
        telegram_id=telegram_id,
        is_enabled=True,
    )

    await message.answer(build_extend_success_text(telegram_id, days))


async def admin_stats_handler(
    message: Message,
    bot_repository: BotRepository,
    xui_repository: XuiRepository,
    invite_repository: InviteRepository,
) -> None:
    """
    Показывает администратору общую статистику проекта.
    """
    if not is_admin(bot_repository, message.from_user.id):
        await message.answer(build_access_denied_text())
        return

    await message.answer(
        build_admin_stats_text(bot_repository, xui_repository, invite_repository),
        reply_markup=main_keyboard,
    )


def register_admin_handlers(
    bot_repository: BotRepository,
    xui_repository: XuiRepository,
    invite_repository: InviteRepository,
) -> Router:
    @router.message(Command("admin"))
    async def admin_command(message: Message):
        await admin_stats_handler(
            message=message,
            bot_repository=bot_repository,
            xui_repository=xui_repository,
            invite_repository=invite_repository,
        )

    @router.message(lambda message: message.text == "📈 Статистика")
    async def stats_button(message: Message):
        await admin_stats_handler(
            message=message,
            bot_repository=bot_repository,
            xui_repository=xui_repository,
            invite_repository=invite_repository,
        )

    @router.message(lambda message: message.text == "🧹 Очистить использованные инвайты")
    async def cleanup_used_invites_button(message: Message):
        if not is_admin(bot_repository, message.from_user.id):
            await message.answer(build_access_denied_text())
            return

        deleted_count = invite_repository.delete_used_invite_links()

        await message.answer(
            build_cleanup_result_text(deleted_count),
            reply_markup=main_keyboard,
        )

    @router.message(Command("admin_users"))
    async def admin_users_command(message: Message):
        """
        Показывает админу список пользователей и срок их подписки.
        """
        if not is_admin(bot_repository, message.from_user.id):
            await message.answer(build_access_denied_text())
            return

        await message.answer(build_admin_users_text(bot_repository))

    @router.message(Command("admin_expiring"))
    async def admin_expiring_command(message: Message):
        """
        Показывает админу пользователей,
        у которых скоро закончится подписка.
        """
        if not is_admin(bot_repository, message.from_user.id):
            await message.answer(build_access_denied_text())
            return

        await message.answer(build_admin_expiring_text(bot_repository))

    @router.message(Command("extend"))
    async def extend_subscription_command(message: Message):
        """
        Продлевает подписку пользователя.

        Формат:
        /extend <telegram_id> <days>
        """
        await extend_subscription_handler(message, bot_repository, xui_repository)

    return router


import time

from aiogram.types import Message

from app.repositories.bot_repository import BotRepository
from app.services.vpn_service import VpnService


class UserService:
    def __init__(self, bot_repository: BotRepository, vpn_service: VpnService):
        self.bot_repository = bot_repository
        self.vpn_service = vpn_service

    def now_ts(self) -> int:
        """
        Возвращает текущее время в Unix seconds.
        """
        return int(time.time())

    def save_user_from_message(self, message: Message, referrer_id: int | None = None) -> None:
        """
        Сохраняет нового пользователя из Telegram-сообщения.

        Если пользователь уже есть в базе, ничего не меняем.
        """
        telegram_id = message.from_user.id

        if self.bot_repository.user_exists(telegram_id):
            return

        if referrer_id == telegram_id:
            referrer_id = None

        self.bot_repository.save_user(
            telegram_id=telegram_id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or "",
            vpn_email=self.vpn_service.make_email(telegram_id),
            referrer_id=referrer_id,
            created_at=self.now_ts(),
        )

    def get_user_role_from_message(self, message: Message) -> str:
        """
        Возвращает роль пользователя из Telegram-сообщения.
        """
        return self.bot_repository.get_user_role(message.from_user.id)

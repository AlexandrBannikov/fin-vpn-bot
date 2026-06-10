from aiogram.types import Message, ReplyKeyboardMarkup

from app.keyboards import get_keyboard_by_role
from app.services.user_service import UserService


class MenuService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def get_keyboard_for_message(self, message: Message) -> ReplyKeyboardMarkup:
        """
        Возвращает правильную клавиатуру для пользователя из Telegram-сообщения.

        owner получает расширенное меню.
        Обычный пользователь получает клиентское меню.
        """
        role = self.user_service.get_user_role_from_message(message)

        return get_keyboard_by_role(role)

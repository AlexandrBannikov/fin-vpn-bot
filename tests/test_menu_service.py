from app.keyboards import get_keyboard_by_role, owner_keyboard, user_keyboard
from app.services.menu_service import MenuService


class FakeUserService:
    def __init__(self, role: str):
        self.role = role

    def get_user_role_from_message(self, message):
        return self.role


def test_get_keyboard_by_role_returns_owner_keyboard_for_owner():
    """
    Проверяем, что owner получает расширенное меню.
    """
    assert get_keyboard_by_role("owner") == owner_keyboard


def test_get_keyboard_by_role_returns_user_keyboard_for_user():
    """
    Проверяем, что обычный пользователь получает клиентское меню.
    """
    assert get_keyboard_by_role("user") == user_keyboard


def test_get_keyboard_by_role_returns_user_keyboard_for_unknown_role():
    """
    Проверяем, что неизвестная роль не получает админское меню.
    """
    assert get_keyboard_by_role("admin") == user_keyboard


def test_menu_service_returns_keyboard_by_message_user_role():
    """
    Проверяем, что MenuService возвращает клавиатуру по роли пользователя.
    """
    menu_service = MenuService(FakeUserService("owner"))

    assert menu_service.get_keyboard_for_message(None) == owner_keyboard

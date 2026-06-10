from unittest.mock import Mock

from app.handlers.help_handler import build_help_text, register_help_handlers


def test_register_help_handlers_returns_router():
    """
    Проверяем, что обработчики помощи регистрируются и возвращают router.
    """
    menu_service = Mock()

    router = register_help_handlers(menu_service)

    assert router is not None


def test_build_help_text_contains_connection_steps():
    """
    Проверяем, что текст помощи содержит основные шаги подключения.
    """
    text = build_help_text()

    assert "ℹ️ Как подключиться:" in text
    assert "📱 Скачать приложение" in text
    assert "Happ или 2rayTun" in text
    assert "🔑 Получить VPN" in text
    assert "QR-коду или ссылке" in text
    assert "👤 Мой VPN" in text

from app.handlers.apps_handler import build_apps_text, register_apps_handlers


def test_register_apps_handlers_returns_router():
    """
    Проверяем, что обработчики приложений регистрируются и возвращают router.
    """
    router = register_apps_handlers()

    assert router is not None


def test_build_apps_text_contains_download_message():
    """
    Проверяем текст сообщения для скачивания приложения.
    """
    text = build_apps_text()

    assert text == "📱 Скачайте приложение для подключения:"


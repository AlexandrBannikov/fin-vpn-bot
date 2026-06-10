from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# Меню обычного пользователя.
# Здесь только кнопки, которые нужны клиенту для использования VPN.
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔑 Получить VPN")],
        [KeyboardButton(text="👤 Мой VPN"), KeyboardButton(text="📱 Скачать приложение")],
        [KeyboardButton(text="🔗 Реферальная ссылка")],
        [KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True,
)

# Меню владельца бота.
# Здесь есть клиентские кнопки + рабочие кнопки для управления сервисом.
owner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔑 Получить VPN")],
        [KeyboardButton(text="👤 Мой VPN"), KeyboardButton(text="📱 Скачать приложение")],
        [KeyboardButton(text="🔗 Реферальная ссылка"), KeyboardButton(text="🎁 Пригласительная ссылка")],
        [KeyboardButton(text="📊 Мои приглашения"), KeyboardButton(text="📈 Статистика")],
        [KeyboardButton(text="🧹 Очистить использованные инвайты")],
        [KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True,
)


def get_keyboard_by_role(role: str | None) -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру по роли пользователя.

    owner получает расширенное меню.
    Все остальные получают обычное клиентское меню.
    """
    if role == "owner":
        return owner_keyboard

    return user_keyboard


# Оставляем старое имя для совместимости со старыми импортами.
# Все старые обработчики пока будут показывать обычное меню.
main_keyboard = user_keyboard

app_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🍏 iPhone — Happ",
                url="https://apps.apple.com/app/happ-proxy-utility/id6504287215",
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Android — Happ",
                url="https://play.google.com/store/apps/details?id=com.happproxy",
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Android — 2rayTun",
                url="https://play.google.com/store/apps/details?id=com.v2raytun.android",
            )
        ],
    ]
)
